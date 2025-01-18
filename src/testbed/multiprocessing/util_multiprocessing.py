"""
Features:
* Using processes (and not a pool): Cleanup guaranteed by OS
* process with timeout:
  * Warning after 0.5*timeout
  * Process kill after timeout
* Subprocess queue to host process:
  * User defined events
* Scheduling of process terminations and reading the queue

Same interface as sync and async
"""

from __future__ import annotations

import contextlib
import logging
import multiprocessing as mp
import multiprocessing.process as mpp
import pathlib
import pickle
import time
import typing
from dataclasses import dataclass
from logging import config
from queue import Empty

from octoprobe.util_constants import relative_cwd

from testbed.reports import util_report_tasks

from ..tentacle_spec import TentacleMicropython

logger = logging.getLogger(__file__)


class EventLogCallback:
    def __init__(self) -> None:
        self._arg1: TargetArg1 | None = None
        self._callback: typing.Callable = self._callback_empty

    def init(self, arg1: TargetArg1) -> None:
        assert isinstance(arg1, TargetArg1)
        self._arg1 = arg1
        self._callback = self._callback_event

    def log(self, msg: str, target_unique_name: str | None = None) -> None:
        self._callback(msg=msg, target_unique_name=target_unique_name)

    def _callback_empty(self, msg: str, target_unique_name: str | None) -> None:
        """
        This callback will be used if running in one process
        """
        assert self._arg1 is None

        logger.info(f"[COLOR_INFO]{msg}")

    def _callback_event(self, msg: str, target_unique_name: str | None) -> None:
        """
        This callback will be used if running in a subprocess
        """
        assert self._arg1 is not None

        if target_unique_name is None:
            target_unique_name = self._arg1.target_unique_name
        logger.info(f"{target_unique_name}: {msg}")
        self._arg1.queue_put(
            EventLog(
                target_unique_name=target_unique_name,
                msg=msg,
            )
        )


EVENTLOGCALLBACK = EventLogCallback()


def init_empty(arg1: TargetArg1) -> None:
    assert isinstance(arg1, TargetArg1)


def init_logging(arg1: TargetArg1) -> None:
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

    assert isinstance(arg1, TargetArg1)
    EVENTLOGCALLBACK.init(arg1=arg1)


def assert_pickable(obj: typing.Any) -> None:
    try:
        dump = pickle.dumps(object)
        pickle.loads(dump)
    except Exception as e:
        err_msg = f"Failed to pickle: {obj!r}"
        logger.exception(err_msg, e)
        raise ValueError(err_msg) from e


class AsyncTarget:
    """
    This class implements a remote procedure call within a multiprocessing pool.
    It will end up in 'target_ctx.apply_async()'.
    The arguments in 'self.funcargs' must be pickable.
    The function 'self.func' must be global.

    Depending of the implementation of the pool, the call might be remote or local.
    This eases debugging errors.
    """

    def __init__(
        self,
        target_unique_name: str,
        tentacles: typing.Sequence[TentacleMicropython],
        func: typing.Callable,
        func_args: list[typing.Any],
        timeout_s: float,
    ) -> None:
        # Fail early: If the arguments can't be pickled, the
        # async call be fail which might be tricky to debug.
        # We take the pickle overhead and pickle now to force early fail.
        assert_pickable(func_args)

        self.target_optional: Target | None = (
            None  # Target(process=None, target_ctx=None, timeout_s=timeout_s)
        )
        self.target_unique_name = target_unique_name
        self.tentacles = tentacles
        self.target_func: typing.Callable = func
        self.target_args: list[typing.Any] = func_args
        self.timeout_s = timeout_s

    def __str__(self) -> str:
        return f"{self.target_unique_name} target={self.target_optional!r}"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self})"

    @property
    def report_task(self) -> util_report_tasks.Task:
        report_tentacles = [
            util_report_tasks.ReportTentacle(
                label=t.label_short,
                board_variant=t.tentacle_state.firmware_spec.board_variant.name_normalized,
            )
            for t in self.tentacles
        ]
        assert self.target.end_s is not None
        return util_report_tasks.Task(
            start_s=self.target.start_s,
            end_s=self.target.end_s,
            label=self.target_unique_name,
            tentacles=report_tentacles,
        )

    def log_started(self) -> None:
        logger.info(f"{self.target_unique_name}: STARTED")

    def log_done(self) -> None:
        logger.info(f"{self.target_unique_name}: DONE {self.target.duration_s:0.1f}s")

    @property
    def target(self) -> Target:
        assert self.target_optional is not None
        return self.target_optional

    @target.setter
    def target(self, target: Target) -> None:
        assert self.target_optional is None
        assert isinstance(target, Target)
        self.target_optional = target

    def fake_start(self) -> None:
        self.target_optional = Target(
            multiprocessing=False,
            timeout_s=60.0,
            process=mp.Process(),
        )

    def fake_join(self) -> None:
        assert not self.target.has_been_joined
        self.target.has_been_joined = True


T = typing.TypeVar("T", bound=AsyncTarget)


class AsyncTargets(list[T], typing.Generic[T]):
    def get_by_event(self, event: EventBase) -> T | None:
        assert isinstance(event, EventBase)
        for ar in self:
            if ar.target.name == event.target_unique_name:
                return ar
        return None

    @property
    def targets(self) -> typing.Iterable[Target]:
        for ar in self:
            if ar.target_optional is not None:
                yield ar.target

    def timeout_reached(self) -> typing.Iterator[T]:
        """
        yields the targets for which the timeout has been reached
        """
        for ar in self:
            target = ar.target_optional
            if target is None:
                continue
            if target.timeout_reached():
                logger.warning(
                    f"{target.name}: Timeout {target.timeout_text} reached: Kill and join "
                )
                yield ar


@dataclass(repr=True)
class TargetArg1:
    target_unique_name: str
    queue: mp.Queue
    initfunc: typing.Callable

    def queue_put(self, event: EventBase) -> None:
        assert isinstance(event, EventBase)
        logger.debug(f"Queue put: {event}")
        self.queue.put(event)

    def queue_log(self, msg: str) -> None:
        assert isinstance(msg, str)
        self.queue_put(EventLog(self.target_unique_name, msg))

    @staticmethod
    def dummy_factory() -> TargetArg1:
        return TargetArg1(
            target_unique_name="dummy",
            queue=mp.Queue(),
            initfunc=lambda f: f,
        )


class Target:
    """
    A 'target' is the function to be called in the subprocess.
    Therefore a 'target' is one function call.
    """

    def __init__(
        self,
        process: mpp.BaseProcess,
        timeout_s: float,
        multiprocessing: bool = True,
    ) -> None:
        assert isinstance(process, mpp.BaseProcess)
        assert isinstance(timeout_s, float)
        assert isinstance(multiprocessing, bool)
        self.multiprocessing = multiprocessing
        self._process = process
        self.timeout_s = timeout_s
        self.start_s = time.monotonic()
        self.end_s: float | None = None
        self._timeout_notification_s = 0.5 * timeout_s
        self._timeout_notification_sent = False
        self.event_exit: EventExit | None = None
        self.has_been_joined: bool = False

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(is_alive={self.is_alive}, end_s={self.end_s}, has_been_joined={self.has_been_joined})"

    @property
    def duration_s(self) -> float:
        assert self.end_s is not None
        return self.end_s - self.start_s

    def join(self) -> None:
        assert not self.has_been_joined
        begin_s = time.monotonic()
        if self.multiprocessing:
            self._process.join()
        duration_s = time.monotonic() - begin_s
        self.has_been_joined = True
        self.end_s = time.monotonic()
        if duration_s > 1.0:
            logger.warning(f".join() took {duration_s}s. This should be below 0.5s!")

    def timeout_reached(self) -> bool:
        """
        Return True: If a process has been killed and the processlist was modified.
        In this case, the calling method must not use the process list anymore!
        """
        if self._process.is_alive():
            livetime_s = self.livetime_s
            if not self._timeout_notification_sent:
                if livetime_s > self._timeout_notification_s:
                    logger.debug(
                        f"{self.name}: About to reach timeout: {self.livetime_text} of {self.timeout_text}"
                    )
                    self._timeout_notification_sent = True
            if livetime_s > self.timeout_s:
                self._process.kill()
                self.join()
                return True
        return False

    def handle_exit_event(self, event: EventBase) -> bool:
        assert isinstance(event, EventBase)

        if isinstance(event, EventExit):
            assert self.event_exit is None
            self.event_exit = event
            self.join()
            return True

        return False

    @property
    def livetime_s(self) -> float:
        return time.monotonic() - self.start_s

    @property
    def livetime_text(self) -> str:
        return f"{self.livetime_s:0.1f}s"

    @property
    def livetime_text_full(self) -> str:
        livetime_s = self.livetime_s
        return f"{livetime_s:0.1f}s ({100.0 * livetime_s / self.timeout_s:0.0f}% of {self.timeout_s:0.1f}s)"

    @property
    def timeout_text(self) -> str:
        return f"{self.timeout_s:0.1f}s"

    @property
    def name(self) -> str:
        return self._process.name

    @property
    def is_alive(self) -> bool:
        return self._process.is_alive()


class TargetCtx:
    def __init__(self, multiprocessing: bool, initfunc: typing.Callable) -> None:
        """
        is_multiprocessing == False: This will call the target directly, eg. in the same
        process. This is useful for debugging.
        """
        assert isinstance(multiprocessing, bool)
        assert callable(initfunc)

        self.multiprocessing = multiprocessing
        self.ctx = mp.get_context("spawn")
        self.queue = self.ctx.Queue()
        self.bartender_token: typing.Any = None
        self.initfunc = initfunc
        self.begin_s = time.monotonic()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def start2(self, async_target: AsyncTarget) -> None:
        assert isinstance(async_target, AsyncTarget)

        assert callable(async_target.target_func)
        assert isinstance(async_target.target_unique_name, str)
        assert isinstance(async_target.target_args, list)
        assert isinstance(async_target.timeout_s, float)
        target_unique_name = async_target.target_unique_name

        target_args_complete = [
            TargetArg1(
                target_unique_name=target_unique_name,
                queue=self.queue,
                initfunc=self.initfunc,
            ),
            *async_target.target_args,
        ]
        process = self.ctx.Process(
            name=target_unique_name,
            target=async_target.target_func,
            args=target_args_complete,
        )
        async_target.target = Target(
            multiprocessing=self.multiprocessing,
            process=process,
            timeout_s=async_target.timeout_s,
        )

        if self.multiprocessing:
            # Start the process
            process.start()
        else:
            # Call the function directly
            async_target.target_func(*target_args_complete)

    def iter_queue(self) -> typing.Iterator[EventBase]:
        while True:
            try:
                event = self.queue.get(timeout=0.1)
            except Empty:
                break
            assert isinstance(event, EventBase), f"Unexpected event: {event!r}"
            logger.debug(f"{event.target_unique_name}: Queue get: {event}")
            yield event

    def cleanup(
        self, async_targets: AsyncTargets[AsyncTarget]
    ) -> typing.Iterator[AsyncTarget]:
        for ar in async_targets:
            target = ar.target_optional
            if target is None:
                continue
            if target.timeout_reached():
                yield ar

        for t in async_targets.targets:
            if not t.is_alive:
                if not t.has_been_joined:
                    logger.error(f"{t.name}: Unexpected termination!")
                    t.join()

    def close_and_join(self, async_targets: AsyncTargets) -> None:
        assert isinstance(async_targets, AsyncTargets)

        for t in async_targets.targets:
            if not t.has_been_joined:
                t.join()

    def targets_not_joined(self, async_targets: AsyncTargets) -> list[Target]:
        assert isinstance(async_targets, AsyncTargets)

        return [t for t in async_targets.targets if not t.has_been_joined]

    def done(self, async_targets: AsyncTargets) -> bool:
        assert isinstance(async_targets, AsyncTargets)

        return len(self.targets_not_joined(async_targets=async_targets)) == 0

    @property
    def duration_s(self) -> float:
        return time.monotonic() - self.begin_s

    @property
    def duration_text(self) -> str:
        return f"{self.duration_s:0.1f}s"


@contextlib.contextmanager
def log_duration_s_obsolete(msg: str) -> typing.Iterator[None]:
    begin_s = time.monotonic()
    yield
    duration_text = f"{time.monotonic() - begin_s:0.3f}s"
    logger.debug(f"{msg}: duration: {duration_text}")


@dataclass(repr=True)
class EventBase:
    target_unique_name: str


@dataclass(repr=True)
class EventExit(EventBase):
    logfile: pathlib.Path
    success: bool

    @property
    def logfile_relative(self) -> pathlib.Path:
        return relative_cwd(self.logfile)


@dataclass(repr=True)
class EventLog(EventBase):
    msg: str
