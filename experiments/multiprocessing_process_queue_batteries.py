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
import multiprocessing
import multiprocessing.queues
import pathlib
import time
import typing
from dataclasses import dataclass
from queue import Empty

logger = logging.getLogger(__file__)


@dataclass(repr=True)
class TargetArg1:
    name: str
    queue: multiprocessing.Queue

    def queue_put(self, event: EventBase) -> None:
        assert isinstance(event, EventBase)
        logger.debug(f"Queue put: {event}")
        self.queue.put(event)

    def queue_log(self, msg: str) -> None:
        assert isinstance(msg, str)
        self.queue_put(EventLog(self.name, msg))


class Target:
    def __init__(
        self, targets: Targets, process: multiprocessing.Process, timeout_s: float
    ) -> None:
        self._targets = targets
        self._process = process
        self.timeout_s = timeout_s
        self._begin_s = time.monotonic()
        self._timeout_notification_s = 0.5 * timeout_s
        self._timeout_notification_sent = False
        self.event_exit: EventExit | None = None

    def join(self) -> None:
        with log_duration_s(f"{self.name}: join()"):
            self._process.join()
        self._targets.targets.remove(self)

    def cleanup(self) -> bool:
        """
        Return True: If a process has been killed and the processlist was modified.
        In this case, the calling method must not use the process list anymore!
        """
        if self._process.is_alive():
            livetime_s = self.livetime_s
            if not self._timeout_notification_sent:
                if livetime_s > self._timeout_notification_s:
                    logger.warning(
                        f"{self.name}: About to reach timeout: {self.livetime_text} of {self.timeout_text}"
                    )
                    self._timeout_notification_sent = True
            if livetime_s > self.timeout_s:
                logger.warning(
                    f"{self.name}: Timeout {self.timeout_text} reached: Kill and join "
                )
                self._process.kill()
                self.join()
            return True
        return False

    def handle_event(self, event: EventBase) -> None:
        if isinstance(event, EventExit):
            assert self.event_exit is None
            self.event_exit = event
            self.join()

    @property
    def livetime_s(self) -> float:
        return time.monotonic() - self._begin_s

    @property
    def livetime_text(self) -> str:
        return f"{self.livetime_s:0.1f}s"

    @property
    def timeout_text(self) -> str:
        return f"{self.timeout_s:0.1f}s"

    @property
    def name(self) -> str:
        return self._process.name

    @property
    def is_alive(self) -> bool:
        return self._process.is_alive()


class Targets:
    def __init__(self) -> None:
        self.targets: list[Target] = []
        self.ctx = multiprocessing.get_context("spawn")
        self.queue = self.ctx.Queue()

    @property
    def done(self) -> bool:
        return len(self.targets) == 0

    def start(
        self,
        name: str,
        target_func: typing.Callable,
        target_args: list[typing.Any],
        timeout_s: float,
    ) -> Target:
        assert callable(target_func)
        assert isinstance(name, str)
        assert isinstance(target_args, list)
        assert isinstance(timeout_s, float)

        process = self.ctx.Process(
            target=target_func,
            name=name,
            args=(TargetArg1(name=name, queue=self.queue), *target_args),
        )
        target = Target(targets=self, process=process, timeout_s=timeout_s)
        self.targets.append(target)
        process.start()
        return target

    def iter_queue(self) -> typing.Iterator[Target, EventBase]:
        while True:
            try:
                event = self.queue.get(timeout=0.1)
            except Empty:
                break
            assert isinstance(event, EventBase), f"Unexpected event: {event!r}"
            logger.debug(f"{event.process_name}: Queue get: {event}")
            target = self.get_target(target_name=event.process_name)
            target.handle_event(event)
            yield target, event

        self.cleanup()

    def get_target(self, target_name: str) -> Target:
        for t in self.targets:
            if t.name == target_name:
                return t
        raise ValueError(f"{target_name=} not found!")

    def cleanup(self) -> None:
        for t in self.targets:
            if t.cleanup():
                continue

        for t in self.targets:
            if not t.is_alive:
                logger.debug(f"ERROR: Unexpected exit of {t.name}")
                t.join()


@contextlib.contextmanager
def log_duration_s(msg: str) -> typing.Iterator[None]:
    begin_s = time.monotonic()
    yield
    duration_text = f"{time.monotonic() - begin_s:0.3f}s"
    logger.debug(f"{msg}: duration: {duration_text}")


@dataclass(repr=True)
class EventBase:
    process_name: str


@dataclass(repr=True)
class EventExit(EventBase):
    logfile: pathlib.Path
    success: bool


@dataclass(repr=True)
class EventLog(EventBase):
    msg: str


@dataclass(repr=True)
class EventExitTargetShowcase(EventExit):
    duration_s: float


def target_showcase(arg1: TargetArg1, duration_s: float, time_s: int) -> None:
    logfile = pathlib.Path("/here_is_the_logfile")
    success = False
    try:
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
            arg1.name,
            success=success,
            logfile=logfile,
            duration_s=time.monotonic() - duration_s,
        )
    )


def init_logging() -> None:
    start_s = time.time()

    logging.basicConfig(level=logging.DEBUG)

    class CustomFormatter(logging.Formatter):
        def formatTime(self, record, datefmt=None):
            elapsed_seconds = record.created - start_s
            return f"{elapsed_seconds:6.3f}s"

    formatter = CustomFormatter("%(asctime)s %(levelname)-7s %(message)s")
    for handler in logging.root.handlers:
        handler.setFormatter(formatter)


def main():
    init_logging()

    ps = Targets()
    if True:
        begin_s = time.monotonic()
        for duration_s, timeout_s in (
            (10, 8.0),
            (3, 20.0),
            (6, 20.0),
            (5, 4.0),
            (2, 20.0),
        ):
            _target = ps.start(
                name=f"Showcase-Process-{duration_s:0.1f}s",
                target_func=target_showcase,
                target_args=[begin_s, duration_s],
                timeout_s=timeout_s,
            )

        while True:
            for _target, event in ps.iter_queue():
                if isinstance(event, EventLog):
                    logger.info(f"{event.process_name}: {event.msg}")

            if ps.done:
                logger.info("Done")
                return


if __name__ == "__main__":
    main()
