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

from testbed.testcollection.baseclasses_run import RunSpecContainer, TestRunBase
from testbed.testcollection.baseclasses_spec import ConnectedTentacles


class WaitForTestsToTerminateException(Exception):
    pass


class AllTestsDoneException(Exception):
    pass


class TestBartender:
    def __init__(
        self,
        connected_tentacles: ConnectedTentacles,
        testrun_spec_container: RunSpecContainer,
    ) -> None:
        assert isinstance(connected_tentacles, ConnectedTentacles)
        assert isinstance(testrun_spec_container, RunSpecContainer)
        self.connected_tentacles = connected_tentacles
        self.testrun_spec_container = testrun_spec_container
        self.actual_runs: list[TestRunBase] = []
        self.available_tentacles = connected_tentacles.copy()

    def test_run_next(self) -> TestRunBase:
        possible_test_runs = list(
            self.testrun_spec_container.generate(
                available_tentacles=self.available_tentacles
            )
        )
        if len(possible_test_runs) == 0:
            if self.tests_tbd == 0:
                raise AllTestsDoneException
            raise WaitForTestsToTerminateException()
        # Calculate priorities
        # Return max

        selected_test_run = possible_test_runs[-1]
        # selected_test_run.decrement()available_tentacles: list[
        self._reserve(test_run=selected_test_run)
        return selected_test_run

    @property
    def tests_tbd(self) -> int:
        return self.testrun_spec_container.tests_tbd

    def _reserve(self, test_run: TestRunBase) -> None:
        self.actual_runs.append(test_run)

        for tentacle in test_run.tentacles:
            assert tentacle in self.available_tentacles
            self.available_tentacles.remove(tentacle)

    def _release(self, test_run: TestRunBase) -> None:
        assert test_run in self.actual_runs
        self.actual_runs.remove(test_run)

        test_run.done()

        for tentacle in test_run.tentacles:
            assert tentacle not in self.available_tentacles
            self.available_tentacles.append(tentacle)

    def test_run_done(self, test_run: TestRunBase) -> None:
        self._release(test_run=test_run)
