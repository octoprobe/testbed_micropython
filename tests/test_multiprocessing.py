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

import logging
import pathlib
import sys
import time
from dataclasses import dataclass

from testbed_micropython import util_multiprocessing as mp
from testbed_micropython.reports.util_report_renderer import RendererMarkdown
from testbed_micropython.reports.util_report_tasks import TaskReport, Tasks

logger = logging.getLogger(__file__)


def target_showcase(arg1: mp.TargetArg1, duration_s: float, time_s: int) -> None:
    logfile = pathlib.Path("/here_is_the_logfile")
    success = False
    try:
        arg1.initfunc(arg1=arg1)
        assert isinstance(duration_s, float)
        assert isinstance(time_s, int)
        time.sleep(time_s)
        if time_s == 2:
            # Demonstrate how an exception is handled
            msg = f"{time_s=}: Throw an exception!"
            arg1.queue_log(msg)
            raise ValueError(msg)

        # Demonstrate a simple log message sent to the main process
        arg1.queue_log(f"Subprocess log: {time.monotonic()-duration_s:0.1f}s are over")
        time.sleep(1.0)

        success = True
    except Exception as e:
        # We log the exception in the local logger and do NOT
        # send the exception to the main process: pickle will fail on some exceptions!
        logger.error(f"Terminating with exception {e!r}", exc_info=e)

    # We have to send a exit event before returing!
    arg1.queue_put(
        EventExitTargetShowcase(
            arg1.target_unique_name,
            success=success,
            logfile=logfile,
            duration_s=time.monotonic() - duration_s,
        )
    )


@dataclass(repr=True)
class EventExitTargetShowcase(mp.EventExit):
    duration_s: float


class AsyncTargetShowcase(mp.AsyncTarget):
    pass


def init_empty(arg1: mp.TargetArg1) -> None:
    assert isinstance(arg1, mp.TargetArg1)


def init_logging(arg1: mp.TargetArg1) -> None:
    assert isinstance(arg1, mp.TargetArg1)

    start_s = time.time()

    logging.basicConfig(level=logging.DEBUG)

    class CustomFormatter(logging.Formatter):
        def formatTime(self, record, datefmt=None):
            elapsed_seconds = record.created - start_s
            return f"{elapsed_seconds:6.3f}s"

    formatter = CustomFormatter("%(asctime)s %(levelname)-7s %(message)s")
    for handler in logging.root.handlers:
        handler.setFormatter(formatter)


def submain(multiprocessing: bool) -> None:
    logger.info(f"****************** MULTIPROCESSING={multiprocessing}")

    async_targets = mp.AsyncTargets[AsyncTargetShowcase]()
    report_tasks = Tasks()

    initfunc = init_logging if multiprocessing else init_empty

    def doit() -> None:
        with mp.TargetCtx(
            multiprocessing=multiprocessing, initfunc=initfunc
        ) as target_ctx:
            begin_s = time.monotonic()
            for duration_s, timeout_s in (
                (10, 8.0),
                (3, 20.0),
                (6, 20.0),
                (5, 4.0),
                (2, 20.0),
            ):
                async_target = AsyncTargetShowcase(
                    target_unique_name=f"Showcase-Process-{duration_s:0.1f}s",
                    func=target_showcase,
                    func_args=[begin_s, duration_s],
                    timeout_s=timeout_s,
                    tentacles=[],
                )
                async_targets.append(async_target)
                target_ctx.start(async_target=async_target)

            while True:
                for event in target_ctx.iter_queue():
                    async_target2 = async_targets.get_by_event(event=event)
                    assert async_target2 is not None
                    if async_target2.target.handle_exit_event(event):
                        assert async_target2.target.end_s is not None
                        report_tasks.append(async_target2.report_task)

                    if isinstance(event, mp.EventLog):
                        logger.info(f"{event.target_unique_name}: {event.msg}")

                for async_target3 in target_ctx.cleanup(async_targets=async_targets):
                    assert async_target3.target.end_s is not None

                    report_tasks.append(async_target3.report_task)

                if target_ctx.done(async_targets=async_targets):
                    logger.info("Done")
                    return

    doit()
    report = TaskReport(tasks=report_tasks)
    report.report(renderer=RendererMarkdown(sys.stdout))

    filename = __file__
    if multiprocessing:
        filename = filename.replace(".py", "_multiprocessing.py")
    with pathlib.Path(filename).with_suffix(".md").open("w") as f:
        report.report(renderer=RendererMarkdown(f))


def main() -> None:
    # init_logging()
    # submain(multiprocessing=False)

    init_logging(arg1=mp.TargetArg1.dummy_factory())
    submain(multiprocessing=True)


if __name__ == "__main__":
    main()
