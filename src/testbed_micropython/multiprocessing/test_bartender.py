"""
Important Terms (abbreviations)
* ts: TentacleSpec
* tss: TentacleSpecs
* tsv: TentacleSpecVariant
* tsvs: TentacleSpecVariants
* tbt: ToBeTested

The bartender
* knows which tests are currently running.
* desides which test comes next
* knows when all tests are over
"""

from __future__ import annotations

import logging
import pathlib
import typing

from ..mptest import util_testrunner
from ..multiprocessing import util_multiprocessing
from ..reports import util_report_tasks
from ..testcollection.baseclasses_run import TestRunSpecs
from ..testcollection.baseclasses_spec import ConnectedTentacles
from ..testcollection.testrun_specs import TestRun

logger = logging.getLogger(__file__)


class CurrentlyNoTestsException(Exception):
    pass


class TestBartender:
    def __init__(
        self,
        connected_tentacles: ConnectedTentacles,
        testrun_specs: TestRunSpecs,
        priority_sorter: typing.Callable[[list[TestRun]], list[TestRun]],
    ) -> None:
        assert isinstance(connected_tentacles, ConnectedTentacles)
        assert isinstance(testrun_specs, TestRunSpecs)
        assert isinstance(priority_sorter, typing.Callable)  # type: ignore[arg-type]
        self.connected_tentacles = connected_tentacles
        self.testrun_specs = testrun_specs
        self.available_tentacles = connected_tentacles.copy()
        self.async_targets = util_multiprocessing.AsyncTargets[AsyncTargetTest]()
        self.get_by_event = self.async_targets.get_by_event
        self.priority_sorter = priority_sorter

    @property
    def tests_todo(self) -> int:
        return self.testrun_specs.tests_todo

    def possible_testruns(
        self,
        firmwares_built: set[str] | None,
    ) -> list[TestRun]:
        _possible_testruns = list(
            self.testrun_specs.generate(
                available_tentacles=self.available_tentacles,
                firmwares_built=firmwares_built,
            )
        )

        return self.priority_sorter(_possible_testruns)

    def testrun_next(
        self,
        firmwares_built: set[str] | None,
        args: util_testrunner.Args,
        ctxtestrun: util_testrunner.CtxTestRun,
        repo_micropython_tests: pathlib.Path,
    ) -> AsyncTargetTest:
        assert isinstance(firmwares_built, set | None)
        assert isinstance(args, util_testrunner.Args)
        assert isinstance(ctxtestrun, util_testrunner.CtxTestRun)
        assert isinstance(repo_micropython_tests, pathlib.Path)

        possible_testruns = self.possible_testruns(firmwares_built=firmwares_built)
        if len(possible_testruns) == 0:
            raise CurrentlyNoTestsException()

        selected_testrun = possible_testruns[0]
        async_target = AsyncTargetTest(
            args=args,
            ctxtestrun=ctxtestrun,
            testrun=selected_testrun,
            repo_micropython_tests=repo_micropython_tests,
            timeout_s=selected_testrun.timeout_s,
        )
        self._reserve(async_target=async_target)
        return async_target

    @property
    def actual_testruns(self) -> list[AsyncTargetTest]:
        return [ar for ar in self.async_targets if not ar.target.has_been_joined]

    def testrun_done(
        self,
        event: util_testrunner.EventExitRunOneTest,
    ) -> AsyncTargetTest:
        assert isinstance(event, util_testrunner.EventExitRunOneTest)
        async_target = self._find_async_target(testid=event.target_unique_name)
        self._release(async_target=async_target)

        log = logger.info if event.success else logger.warning
        color = "[COLOR_SUCCESS]" if event.success else "[COLOR_FAILED]"

        log(
            f"{color}{async_target.target_unique_name}: Completed in {async_target.target.livetime_text_full}: success={event.success}: Logfile: {event.logfile_relative}"
        )

        return async_target

    def _find_async_target(self, testid: str) -> AsyncTargetTest:
        for async_target in self.async_targets:
            if async_target.testrun.testid == testid:
                return async_target
        raise ValueError(f"Testrun not found: {testid}")

    def _reserve(self, async_target: AsyncTargetTest) -> None:
        assert isinstance(async_target, AsyncTargetTest)
        self.async_targets.append(async_target)

        for tentacle in async_target.tentacles:
            assert tentacle in self.available_tentacles
            self.available_tentacles.remove(tentacle)

        async_target.testrun.mark_as_done()

    def _release(self, async_target: AsyncTargetTest) -> None:
        assert isinstance(async_target, AsyncTargetTest)
        assert async_target in self.async_targets
        self.async_targets.remove(async_target)

        for tentacle in async_target.tentacles:
            assert tentacle not in self.available_tentacles
            self.available_tentacles.append(tentacle)

    def handle_timeouts(self, report_tasks: util_report_tasks.Tasks) -> None:
        assert isinstance(report_tasks, util_report_tasks.Tasks)

        for async_target in self.async_targets.timeout_reached():
            self._release(async_target=async_target)

            report_tasks.append(async_target.report_task)

    def pytest_print_actual_testruns(
        self, title: str, indent: int, file: typing.TextIO
    ) -> None:
        print(title, file=file)
        actual_testruns = [x.testrun for x in self.actual_testruns]
        actual_testruns = TestRun.alphabetical_sorter(actual_testruns)
        for testrun in actual_testruns:
            print((indent + 1) * "  " + testrun.testid, file=file)


class AsyncTargetTest(util_multiprocessing.AsyncTarget):
    def __init__(
        self,
        args: util_testrunner.Args,
        ctxtestrun: util_testrunner.CtxTestRun,
        testrun: TestRun,
        repo_micropython_tests: pathlib.Path,
        timeout_s: float,
    ) -> None:
        # pylint: disable=reimported,redefined-outer-name
        from ..mptest import util_testrunner

        assert isinstance(args, util_testrunner.Args)
        assert isinstance(ctxtestrun, util_testrunner.CtxTestRun)
        assert isinstance(testrun, TestRun)
        assert isinstance(repo_micropython_tests, pathlib.Path)
        assert isinstance(timeout_s, float)

        super().__init__(
            target_unique_name=testrun.testid,
            tentacles=testrun.tentacles,
            func=util_testrunner.target_run_one_test_async,
            func_args=[args, ctxtestrun, testrun, repo_micropython_tests],
            timeout_s=timeout_s,
        )

        self.testrun = testrun
