"""
Classes required to describe the tests to be run.
"""

from __future__ import annotations

import abc
import dataclasses
from collections.abc import Iterator

from testbed.testcollection.baseclasses_spec import Tentacle, TentacleVariant


class TestRunSpecBase(abc.ABC):
    @abc.abstractmethod
    def generate(self, available_tentacles: list) -> Iterator[TestRunBase]: ...

    @abc.abstractmethod
    def done(self, test_run: TestRunBase) -> None: ...

    @property
    @abc.abstractmethod
    def tests_tbd(self) -> int: ...
@dataclasses.dataclass
class TestRunBase:
    testrun_spec: TestRunSpecBase

    @property
    @abc.abstractmethod
    def tentacles(self) -> list[Tentacle]: ...

    def done(self) -> None:
        self.testrun_spec.done(test_run=self)


@dataclasses.dataclass
class TestRunSingle(TestRunBase):
    tentacle_variant: TentacleVariant

    @property
    def tentacles(self) -> list[Tentacle]:
        return [self.tentacle_variant.tentacle]


@dataclasses.dataclass
class TestRunFirstSecond(TestRunBase):
    tentacle_variant_first: TentacleVariant
    tentacle_variant_second: TentacleVariant

    @property
    def tentacles(self) -> list[Tentacle]:
        return [
            self.tentacle_variant_first.tentacle,
            self.tentacle_variant_second.tentacle,
        ]


class RunSpecContainer(list[TestRunSpecBase]):
    def generate(self, available_tentacles: list[Tentacle]) -> Iterator[TestRunBase]:
        for testrun_spec in self:
            yield from testrun_spec.generate(available_tentacles=available_tentacles)

    @property
    def tests_tbd(self) -> int:
        return sum(testrun_spec.tests_tbd for testrun_spec in self)
