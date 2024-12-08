"""
Classes required to describe the tests to be run.
"""

from __future__ import annotations

from collections.abc import Iterator

from octoprobe.lib_tentacle import Tentacle

from .testrun_specs import TestRunBase, TestRunSpecBase


class RunSpecContainer(list[TestRunSpecBase]):
    def generate(self, available_tentacles: list[Tentacle]) -> Iterator[TestRunBase]:
        for testrun_spec in self:
            yield from testrun_spec.generate(available_tentacles=available_tentacles)

    @property
    def tests_tbd(self) -> int:
        return sum(testrun_spec.tests_tbd for testrun_spec in self)
