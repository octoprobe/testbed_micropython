"""
Classes required to describe the tests to be run.
"""

from __future__ import annotations

from collections.abc import Iterator

from octoprobe.lib_tentacle import Tentacle

from testbed.testcollection.baseclasses_spec import (
    ConnectedTentacles,
)

from .testrun_specs import TestRun, TestRunSpec


class TestRunSpecs(list[TestRunSpec]):
    def generate(
        self,
        available_tentacles: list[Tentacle],
        firmwares_built: set[str],
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

    def assign_tentacles(
        self,
        tentacles: ConnectedTentacles,
        only_board_variants: list[str] | None,
        flash_skip: bool,
    ) -> None:
        for testrun_spec in self:
            testrun_spec.assign_tentacles(
                tentacles=tentacles,
                only_board_variants=only_board_variants,
                flash_skip=flash_skip,
            )
