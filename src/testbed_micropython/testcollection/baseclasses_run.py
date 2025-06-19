"""
Classes required to describe the tests to be run.
"""

from __future__ import annotations

import typing
from collections.abc import Iterator

from .baseclasses_spec import ConnectedTentacles
from .testrun_specs import TentacleMicropython, TestRun, TestRunSpec


class TestRunSpecs(list[TestRunSpec]):
    def generate(
        self,
        available_tentacles: typing.Sequence[TentacleMicropython],
        firmwares_built: set[str] | None,
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
            )

    @property
    def tests_todo(self) -> int:
        return sum(testrun_spec.tests_todo for testrun_spec in self)

    def assign_tentacles(self, tentacles: ConnectedTentacles) -> None:
        for testrun_spec in self:
            testrun_spec.assign_tentacles(tentacles=tentacles)

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
