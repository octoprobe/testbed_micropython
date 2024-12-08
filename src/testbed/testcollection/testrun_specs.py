from __future__ import annotations

import abc
import dataclasses
import itertools
from collections.abc import Iterator

from .baseclasses_spec import (
    Tentacle,
    TentacleSpecVariant,
    TentacleSpecVariants,
    TentacleVariant,
)


@dataclasses.dataclass
class TestRunBase:
    testrun_spec: TestRunSpecBase

    @property
    @abc.abstractmethod
    def tentacles(self) -> list[Tentacle]: ...

    def done(self) -> None:
        self.testrun_spec.done(test_run=self)


class TestRunSpecBase(abc.ABC):
    @abc.abstractmethod
    def generate(self, available_tentacles: list) -> Iterator[TestRunBase]: ...

    @abc.abstractmethod
    def done(self, test_run: TestRunBase) -> None: ...

    @property
    @abc.abstractmethod
    def tests_tbd(self) -> int: ...

    @property
    @abc.abstractmethod
    def iter_text_tsvs(self) -> Iterator[str]: ...


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
        return f"{self.__class__.__name__}({self.subprocess_args})"

    def done(self, test_run: TestRunBase) -> None:
        from .test_runs import TestRunSingle

        assert isinstance(test_run, TestRunSingle)

        self.tsvs_tbt.remove_tentacle_variant(test_run.tentacle_variant)

    @property
    def tests_tbd(self) -> int:
        return len(self.tsvs_tbt)

    @property
    def iter_text_tsvs(self) -> Iterator[str]:
        for tsvs in self.tsvs_tbt:
            yield f"{tsvs!r}"

    def generate(self, available_tentacles: list[Tentacle]) -> Iterator[TestRunBase]:
        for tsv_to_be_tested in self.tsvs_tbt:
            for available_tentacle in available_tentacles:
                if (
                    available_tentacle.tentacle_spec
                    is not tsv_to_be_tested.tentacle_spec
                ):
                    continue
                from .test_runs import TestRunSingle

                yield TestRunSingle(
                    testrun_spec=self,
                    tentacle_variant=TentacleVariant(
                        tentacle=available_tentacle,
                        variant=tsv_to_be_tested.variant,
                    ),
                )
                break


@dataclasses.dataclass
class TestRunSpecWlanAPvsSTA(TestRunSpecBase):
    """
    Tentacle_WLA_STA connects to Tentacle_WLAN_AP.
    Two tentacles connect to an AP and communicate together.

    Every tentacle has to be tested against two other tentacles. Once as wlanAP, and once as wlanSTA.
    """

    def __init__(
        self,
        subprocess_args: list[str],
        tsvs_tbt: TentacleSpecVariants,
    ) -> None:
        assert isinstance(subprocess_args, list)
        assert isinstance(tsvs_tbt, TentacleSpecVariants)

        self.tsvs_tbt_wlanAP = TentacleSpecVariants(tsvs_tbt)
        self.tsvs_tbt_wlanSTA = TentacleSpecVariants(tsvs_tbt)
        self.subprocess_args = subprocess_args
        """
        wlantest.py
        """

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.subprocess_args})"

    def done(self, test_run: TestRunBase) -> None:
        from .test_runs import TestRunWlanAPWlanSTA

        assert isinstance(test_run, TestRunWlanAPWlanSTA)

        self.tsvs_tbt_wlanAP.remove_tentacle_variant(test_run.tentacle_variant_wlanAP)
        self.tsvs_tbt_wlanSTA.remove_tentacle_variant(test_run.tentacle_variant_wlanSTA)

    @property
    def tests_tbd(self) -> int:
        return len(self.tsvs_tbt_wlanAP) + len(self.tsvs_tbt_wlanSTA)

    @property
    def iter_text_tsvs(self) -> Iterator[str]:
        for tsvs in self.tsvs_tbt_wlanAP:
            yield f"{tsvs!r} wlanAP"
        for tsvs in self.tsvs_tbt_wlanSTA:
            yield f"{tsvs!r} wlanSTA"

    def generate(self, available_tentacles: list[Tentacle]) -> Iterator[TestRunBase]:
        tsvs_combinations: list[tuple[TentacleSpecVariant, TentacleSpecVariant]] = []
        for wlanAP in self.tsvs_tbt_wlanAP:
            for wlanSTA in self.tsvs_tbt_wlanSTA:
                tsvs_combinations.append((wlanAP, wlanSTA))

        if False:
            for s in tsvs_combinations:
                print(s)

        for wlanAP, wlanSTA in tsvs_combinations:
            for tentacle_wlanAP, tentacle_wlanSTA in itertools.combinations(
                available_tentacles, 2
            ):
                if tentacle_wlanAP.tentacle_spec is not wlanAP.tentacle_spec:
                    continue
                if tentacle_wlanSTA.tentacle_spec is not wlanSTA.tentacle_spec:
                    continue
                from .test_runs import (
                    TestRunWlanAPWlanSTA,
                )

                yield TestRunWlanAPWlanSTA(
                    testrun_spec=self,
                    tentacle_variant_wlanAP=TentacleVariant(
                        tentacle=tentacle_wlanAP,
                        variant=wlanAP.variant,
                    ),
                    tentacle_variant_wlanSTA=TentacleVariant(
                        tentacle=tentacle_wlanSTA,
                        variant=wlanAP.variant,
                    ),
                )
                break
