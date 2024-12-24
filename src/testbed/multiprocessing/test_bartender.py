"""
Important Terms (abbreviations)
* tsv: TentacleSpecVariant
* tsvs: TentacleSpecVariants
* tbt: ToBeTested

The bartender
* knows which tests are currently running.
* desides which test comes next
* knows when all tests are over
"""

from __future__ import annotations

import pathlib

from testbed.mptest import util_testrunner
from testbed.multiprocessing import util_multiprocessing
from testbed.testcollection.baseclasses_run import TestRunSpecs
from testbed.testcollection.baseclasses_spec import ConnectedTentacles
from testbed.testcollection.testrun_specs import TestRun


class CurrentlyNoTestsException(Exception):
    pass


class AllTestsDoneException(Exception):
    pass


class TestBartender:
    def __init__(
        self,
        connected_tentacles: ConnectedTentacles,
        testrun_specs: TestRunSpecs,
    ) -> None:
        assert isinstance(connected_tentacles, ConnectedTentacles)
        assert isinstance(testrun_specs, TestRunSpecs)
        self.connected_tentacles = connected_tentacles
        self.testrun_specs = testrun_specs
        self.actual_testruns: list[TestRun] = []
        self.available_tentacles = connected_tentacles.copy()

    @property
    def tests_todo(self) -> int:
        return self.testrun_specs.tests_todo

    def testrun_next(self, firmwares_built: set[str]) -> TestRun:
        possible_testruns = list(
            self.testrun_specs.generate(
                available_tentacles=self.available_tentacles,
                firmwares_built=firmwares_built,
            )
        )
        if len(possible_testruns) == 0:
            if self.tests_todo == 0:
                raise AllTestsDoneException()
            raise CurrentlyNoTestsException()
        # Calculate priorities
        # Return max

        selected_testrun = possible_testruns[-1]
        # selected_test_run.decrement()available_tentacles: list[
        self._reserve(testrun=selected_testrun)
        return selected_testrun

    def testrun_done(self, testrun: TestRun) -> None:
        self._release(testrun=testrun)

    def _reserve(self, testrun: TestRun) -> None:
        self.actual_testruns.append(testrun)

        for tentacle in testrun.tentacles:
            assert tentacle in self.available_tentacles
            self.available_tentacles.remove(tentacle)

    def _release(self, testrun: TestRun) -> None:
        assert isinstance(testrun, TestRun)
        assert testrun in self.actual_testruns
        self.actual_testruns.remove(testrun)

        testrun.done()

        for tentacle in testrun.tentacles:
            assert tentacle not in self.available_tentacles
            self.available_tentacles.append(tentacle)


class AsyncResultTest(util_multiprocessing.AsyncResult):
    def __init__(
        self,
        args: util_testrunner.Args,
        ntestrun: util_testrunner.NTestRun,
        testrun: TestRun,
        repo_micropython_tests: pathlib.Path,
    ) -> None:
        # pylint: disable=reimported,redefined-outer-name
        from testbed.mptest import util_testrunner

        assert isinstance(args, util_testrunner.Args)
        assert isinstance(ntestrun, util_testrunner.NTestRun)
        assert isinstance(testrun, TestRun)
        assert isinstance(repo_micropython_tests, pathlib.Path)

        super().__init__(
            label=f"Test {testrun.testid}",
            tentacles=testrun.tentacles,
            func=util_testrunner.run_one_test_async,
            func_args=[args, ntestrun, testrun, repo_micropython_tests],
        )

        self.testrun = testrun

    def done(self, bartender: TestBartender) -> None:
        assert isinstance(bartender, TestBartender)
        bartender.testrun_done(testrun=self.testrun)
