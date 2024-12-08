from __future__ import annotations

import dataclasses
import itertools
from collections.abc import Iterator

from testbed.testcollection.baseclasses_run import (
    TestRunBase,
    TestRunFirstSecond,
    TestRunSingle,
    TestRunSpecBase,
)
from testbed.testcollection.baseclasses_spec import (
    Tentacle,
    TentacleSpecVariant,
    TentacleSpecVariants,
    TentacleVariant,
)


class TestRunSpecSingle(TestRunSpecBase):
    """
    Runs tests against a single tentacle.

    Each test has to run on every connected tentacle with FUT_MCU_ONLY.
    """

    def __init__(
        self,
        subprocess_args: list[str],
        tsvs_tbt: TentacleSpecVariants,
    ) -> None:
        assert isinstance(subprocess_args, list)
        assert isinstance(tsvs_tbt, TentacleSpecVariants)

        self.tsvs_tbt = TentacleSpecVariants(tsvs_tbt)
        self.subprocess_args = subprocess_args
        """
        perftest.py, hwtest.py
        """

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(tests_tbd={self.tests_tbd} {self.subprocess_args})"

    def done(self, test_run: TestRunBase) -> None:
        assert isinstance(test_run, TestRunSingle)

        self.tsvs_tbt.remove_tentacle_variant(test_run.tentacle_variant)

    @property
    def tests_tbd(self) -> int:
        return len(self.tsvs_tbt)

    def generate(self, available_tentacles: list[Tentacle]) -> Iterator[TestRunBase]:
        for tsv_to_be_tested in self.tsvs_tbt:
            for available_tentacle in available_tentacles:
                if (
                    available_tentacle.tentacle_spec
                    is not tsv_to_be_tested.tentacle_spec
                ):
                    continue
                yield TestRunSingle(
                    testrun_spec=self,
                    tentacle_variant=TentacleVariant(
                        tentacle=available_tentacle,
                        variant=tsv_to_be_tested.variant,
                    ),
                )
                break


@dataclasses.dataclass
class TestRunSpecWlan(TestRunSpecBase):
    """
    Tentacle_WLA_STA connects to Tentacle_WLAN_AP.
    Two tentacles connect to an AP and communicate together.

    Every tentacle has to be tested against two other tentacles. Once as first, and once as second.
    """

    def __init__(
        self,
        subprocess_args: list[str],
        tsvs_tbt: TentacleSpecVariants,
    ) -> None:
        assert isinstance(subprocess_args, list)
        assert isinstance(tsvs_tbt, TentacleSpecVariants)

        self.tsvs_tbt_first = TentacleSpecVariants(tsvs_tbt)
        self.tsvs_tbt_second = TentacleSpecVariants(tsvs_tbt)
        self.subprocess_args = subprocess_args
        """
        wlantest.py
        """

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(tests_tbd={self.tests_tbd} {self.subprocess_args})"

    def done(self, test_run: TestRunBase) -> None:
        assert isinstance(test_run, TestRunFirstSecond)

        self.tsvs_tbt_first.remove_tentacle_variant(test_run.tentacle_variant_first)
        self.tsvs_tbt_second.remove_tentacle_variant(test_run.tentacle_variant_second)

    @property
    def tests_tbd(self) -> int:
        return len(self.tsvs_tbt_first) + len(self.tsvs_tbt_second)

    def generate(self, available_tentacles: list[Tentacle]) -> Iterator[TestRunBase]:
        tsvs_combinations: list[tuple[TentacleSpecVariant, TentacleSpecVariant]] = []
        for first in self.tsvs_tbt_first:
            for second in self.tsvs_tbt_second:
                tsvs_combinations.append((first, second))

        if False:
            for s in tsvs_combinations:
                print(s)

        for first, second in tsvs_combinations:
            for tentacle_first, tentacle_second in itertools.combinations(
                available_tentacles, 2
            ):
                if tentacle_first.tentacle_spec is not first.tentacle_spec:
                    continue
                if tentacle_second.tentacle_spec is not second.tentacle_spec:
                    continue
                yield TestRunFirstSecond(
                    testrun_spec=self,
                    tentacle_variant_first=TentacleVariant(
                        tentacle=tentacle_first,
                        variant=first.variant,
                    ),
                    tentacle_variant_second=TentacleVariant(
                        tentacle=tentacle_second,
                        variant=first.variant,
                    ),
                )
                break
