"""
Classes required to describe the tests to be run.
"""

from __future__ import annotations

from collections.abc import Iterator

from octoprobe.lib_tentacle import Tentacle

from testbed.testcollection.baseclasses_spec import TentacleSpecVariants

from .testrun_specs import TestRun, TestRunSpec


class TestRunSpecs(list[TestRunSpec]):
    def generate(self, available_tentacles: list[Tentacle]) -> Iterator[TestRun]:
        for testrun_spec in self:
            yield from testrun_spec.generate(available_tentacles=available_tentacles)

    @property
    def tests_tbd(self) -> int:
        return sum(testrun_spec.tests_tbd for testrun_spec in self)

    def assign_tsvs_tbd(self, tsvs: TentacleSpecVariants) -> None:
        for testrun_spec in self:
            testrun_spec.assign_tsvs_tbd(tsvs)
