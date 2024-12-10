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

from testbed.testcollection.baseclasses_run import TestRunSpecs
from testbed.testcollection.baseclasses_spec import ConnectedTentacles
from testbed.testcollection.testrun_specs import TestRun


class WaitForTestsToTerminateException(Exception):
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
        self.testrun_spec = testrun_specs
        self.actual_runs: list[TestRun] = []
        self.available_tentacles = connected_tentacles.copy()

    @property
    def tests_tbd(self) -> int:
        return self.testrun_spec.tests_tbd

    def testrun_next(self) -> TestRun:
        possible_test_runs = list(
            self.testrun_spec.generate(available_tentacles=self.available_tentacles)
        )
        if len(possible_test_runs) == 0:
            if self.tests_tbd == 0:
                raise AllTestsDoneException()
            raise WaitForTestsToTerminateException()
        # Calculate priorities
        # Return max

        selected_test_run = possible_test_runs[-1]
        # selected_test_run.decrement()available_tentacles: list[
        self._reserve(test_run=selected_test_run)
        return selected_test_run

    def testrun_done(self, test_run: TestRun) -> None:
        self._release(test_run=test_run)

    def _reserve(self, test_run: TestRun) -> None:
        self.actual_runs.append(test_run)

        for tentacle in test_run.tentacles:
            assert tentacle in self.available_tentacles
            self.available_tentacles.remove(tentacle)

    def _release(self, test_run: TestRun) -> None:
        assert test_run in self.actual_runs
        self.actual_runs.remove(test_run)

        test_run.done()

        for tentacle in test_run.tentacles:
            assert tentacle not in self.available_tentacles
            self.available_tentacles.append(tentacle)
