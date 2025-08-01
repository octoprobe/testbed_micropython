"""
Classes required to describe the tests to be run.
"""

from __future__ import annotations

import typing
from collections.abc import Iterator

from ..tentacle_spec import TentacleMicropython
from .baseclasses_spec import ConnectedTentacles
from .testrun_specs import TestRun, TestRunSpec


class TestRunSpecs(list[TestRunSpec]):
    def generate(
        self,
        available_tentacles: typing.Sequence[TentacleMicropython],
        firmwares_built: set[str] | None,
        flash_skip: bool,
        tentacle_reference: TentacleMicropython | None,
    ) -> Iterator[TestRun]:
        assert isinstance(available_tentacles, list)

        for testrun_spec in self:
            applicable_tentacles = [
                x
                for x in available_tentacles
                if testrun_spec.required_fut in x.tentacle_spec.futs
            ]
            yield from testrun_spec.generate(
                available_tentacles=applicable_tentacles,
                firmwares_built=firmwares_built,
                flash_skip=flash_skip,
                tentacle_reference=tentacle_reference,
            )

    @property
    def tests_todo(self) -> int:
        return sum(testrun_spec.tests_todo for testrun_spec in self)

    @property
    def tests_progress(self) -> str:
        tests_total_count = sum(testrun_spec.tsvs_total_count for testrun_spec in self)
        return f"{self.tests_todo + 1}({tests_total_count})"

    def requires_reference_tentacle(self, tentacles: list[TentacleMicropython]) -> bool:
        """
        Returns True if at least one test requires the reference tentacle
        """
        assert isinstance(tentacles, list)
        for tentacle in tentacles:
            assert isinstance(tentacle, TentacleMicropython)

        for testrun_spec in self:
            if testrun_spec.requires_reference_tentacle:
                for tentacle in tentacles:
                    if testrun_spec.required_fut in tentacle.tentacle_spec.futs:
                        return True

        return False

    def assign_tentacles(
        self,
        tentacles: ConnectedTentacles,
        count: int,
        flash_skip: bool,
    ) -> None:
        for testrun_spec in self:
            testrun_spec.assign_tentacles(
                tentacles=tentacles,
                count=count,
                flash_skip=flash_skip,
            )

        self.sort()

    def pytest_print(self, indent: int, file: typing.TextIO) -> None:
        for testrunspec in self:
            print(
                indent * "  "
                + f"testrunspec['{testrunspec.label}'] tests_todo={testrunspec.tests_todo}",
                file=file,
            )
            testrunspec.pytest_print(indent + 1, file=file)

    def contains_test_with_label(self, label: str) -> bool:
        for testrun_specs in self:
            if testrun_specs.label == label:
                return True
        return False
