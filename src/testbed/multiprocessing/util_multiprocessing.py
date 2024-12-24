from __future__ import annotations

import abc
import logging
import multiprocessing
import multiprocessing.pool
import pathlib
import pickle
import time
import typing
from logging import config

from octoprobe.lib_tentacle import Tentacle

from testbed.reports import util_report_renderer as renderer, util_report_tasks

logger = logging.getLogger(__file__)


def init_logging() -> None:
    """
    This method will be used to initialize a multiprocessing subprocess.
    """
    log_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {"simple": {"format": "%(levelname)-8s - %(message)s"}},
        "handlers": {},
        "root": {"level": "DEBUG", "handlers": []},
    }
    config.dictConfig(log_config)


class AsyncResult:
    """
    This class implements a remote procedure call within a multiprocessing pool.
    It will end up in 'process_pool.apply_async()'.
    The arguments in 'self.funcargs' must be pickable.
    The function 'self.func' must be global.

    Depending of the implementation of the pool, the call might be remote or local.
    This eases debugging errors.
    """

    def __init__(
        self,
        label: str,
        tentacles: list[Tentacle],
        func: typing.Callable,
        func_args=list[typing.Any],
    ) -> None:
        try:
            # Fail early: If the arguments can't be pickled, the
            # async call be fail which might be tricky to debug.
            # We take the pickle overhead and pickle now to force early fail.
            pickle.dumps(func_args)
        except Exception as e:
            logger.error(
                f"multiprocessing parameters could not be pickled {func_args!r}: {e!r}"
            )
        self._result: multiprocessing.pool.ApplyResult | None = None
        self._result_value: typing.Any | None = None
        self._start_s: float = time.monotonic()
        self._duration_s: float = 0
        self.label = label
        self.tentacles = tentacles
        self.func: typing.Callable = func
        self.funcargs: list[typing.Any] = func_args

    def get_result(self, report_tasks: util_report_tasks.Tasks) -> None:
        assert self._result is not None
        assert self._result_value is None
        try:
            self._result_value = self._result.get()
        except Exception as e:
            self._result_value = e
            logger.error(f"{self.label}: {e!r}")

        report_tentacles = [
            util_report_tasks.ReportTentacle(
                label=t.label_short,
                board_variant=t.tentacle_state.firmware_spec.board_variant.name_normalized,
            )
            for t in self.tentacles
        ]
        report_tasks.append(
            util_report_tasks.Task(
                start_s=self._start_s,
                end_s=time.monotonic(),
                label=self.label,
                tentacles=report_tentacles,
            )
        )

    def apply_sync(self, bartender: typing.Any) -> None:
        self.log_started()
        self._result_value = self.func(*self.funcargs)
        self.done(bartender=bartender)
        self.log_done()

    def log_started(self) -> None:
        logger.info(f"{self.label}: STARTED")

    def log_done(self) -> None:
        self._duration_s = time.monotonic() - self._start_s
        logger.info(f"{self.label}: DONE {self._duration_s:0.1f}s")

    @abc.abstractmethod
    def done(self, bartender: typing.Any) -> None: ...

    @property
    def result(self) -> multiprocessing.pool.ApplyResult:
        assert self._result is not None
        assert isinstance(self._result, multiprocessing.pool.ApplyResult)
        return self._result

    @result.setter
    def result(self, value: multiprocessing.pool.ApplyResult) -> None:
        assert isinstance(value, multiprocessing.pool.ApplyResult)
        self._result = value

    @property
    def ready(self) -> bool:
        assert self.result is not None
        return self.result.ready()

    @property
    def successful(self) -> bool:
        assert self.result is not None
        return self.result.successful()


class ProcessPoolSync:
    def __init__(
        self,
        processes: int = 12,
        initializer: typing.Callable | None = None,
    ) -> None:
        self.report_tasks = util_report_tasks.Tasks()

    def apply_async(self, async_result: AsyncResult, bartender: typing.Any) -> None:
        async_result.apply_sync(bartender=bartender)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    @property
    def done(self) -> bool:
        return True

    def get_results(self) -> list[AsyncResult]:
        return []

    def close_and_join(self) -> None:
        pass

    def write_report_tasks(self, directory: pathlib.Path) -> None:
        for ext, r in (
            (".md", renderer.RendererMarkdown),
            (".txt", renderer.RendererAscii),
        ):
            with (directory / f"report_tasks{ext}").open("w") as f:
                report = util_report_tasks.TaskReport(self.report_tasks)
                report.report(renderer=r(f=f))


class ProcessPoolAsync(ProcessPoolSync):
    def __init__(
        self,
        processes: int = 12,
        initializer: typing.Callable | None = None,
    ) -> None:
        super().__init__(processes=processes, initializer=initializer)
        self.mp_context = multiprocessing.get_context("spawn")
        self.pool = self.mp_context.Pool(processes=processes, initializer=initializer)
        self.results: list[AsyncResult] = []

    def __enter__(self):
        self.pool.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.pool.__exit__(exc_type, exc_val, exc_tb)

    @typing.override
    @property
    def done(self) -> bool:
        return len(self.results) == 0

    @typing.override
    def apply_async(self, async_result: AsyncResult, bartender: typing.Any) -> None:
        assert isinstance(async_result, AsyncResult)
        result = self.pool.apply_async(
            func=async_result.func, args=async_result.funcargs
        )
        async_result.result = result
        self.results.append(async_result)
        async_result.log_started()

    def get_results(self) -> list[AsyncResult]:
        results: list[AsyncResult] = [r for r in self.results if r.ready]
        for async_result in results:
            async_result.log_done()
            self.results.remove(async_result)
            async_result.get_result(report_tasks=self.report_tasks)

        return results

    @typing.override
    def close_and_join(self) -> None:
        self.pool.close()
        self.pool.join()
