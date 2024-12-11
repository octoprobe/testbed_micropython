from __future__ import annotations

import abc
import copy
import dataclasses
import itertools
import pathlib
import typing
from collections.abc import Iterator

from octoprobe.lib_tentacle import Tentacle

from .baseclasses_spec import (
    TentacleSpecVariants,
    TentacleVariant,
)

if typing.TYPE_CHECKING:
    from testbed.testrunner.util_testrunner import ResultsDir


@dataclasses.dataclass(repr=True)
class TestArgs:
    testresults_directory: ResultsDir
    git_micropython_tests: pathlib.Path


@dataclasses.dataclass(repr=True)
class TestRun:
    testrun_spec: TestRunSpec
    list_tentacle_variant: list[TentacleVariant]

    def __post_init__(self) -> None:
        assert isinstance(self.testrun_spec, TestRunSpec)
        assert isinstance(self.list_tentacle_variant, list)

    def done(self) -> None:
        self.testrun_spec.done(test_run=self)

    def copy_tentacles(self) -> None:
        """
        We want to override tentacle.firmware_spec later on.
        So we create a copy as we do not want to alter the origin.
        """
        self.list_tentacle_variant = [
            TentacleVariant(
                tentacle=copy.copy(tv.tentacle),
                board=tv.board,
                variant=tv.variant,
            )
            for tv in self.list_tentacle_variant
        ]

    @abc.abstractmethod
    def test(self, testargs: TestArgs) -> None: ...

    @property
    def tentacles(self) -> list[Tentacle]:
        return [x.tentacle for x in self.list_tentacle_variant]

    @property
    def testid(self) -> str:
        """
        For example: run-perfbench.py[2d2d-lolin_D1-ESP8266_GENERIC]
        """
        subprocess = "-".join(self.testrun_spec.subprocess_args)
        tentacles = ",".join(
            [
                f"{tv.tentacle.label_short2}-{tv.label}"
                for tv in self.list_tentacle_variant
            ]
        )
        return f"{subprocess}[{tentacles}]"


@dataclasses.dataclass
class TestRunSpec:
    """
    Tentacle_WLA_STA connects to Tentacle_WLAN_AP.
    Two tentacles connect to an AP and communicate together.

    Every tentacle has to be tested against two other tentacles. Once as fist, and once as second.
    """

    def __init__(
        self,
        subprocess_args: list[str],
        tentacles_required: int,
        testrun_class: type[TestRun] = TestRun,
    ) -> None:
        assert isinstance(testrun_class, type(TestRun))
        assert isinstance(subprocess_args, list)
        assert isinstance(tentacles_required, int)

        self.testrun_class = testrun_class
        self.tentacles_required = tentacles_required
        self.list_tsvs_tbt: list[TentacleSpecVariants] = []
        self.subprocess_args = subprocess_args
        """
        wlantest.py
        """

    def assign_tsvs_tbd(self, tsvs_tbt: TentacleSpecVariants) -> None:
        assert isinstance(tsvs_tbt, TentacleSpecVariants)
        self.list_tsvs_tbt = [
            TentacleSpecVariants(tsvs_tbt) for _ in range(self.tentacles_required)
        ]

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.subprocess_args})"

    def done(self, test_run: TestRun) -> None:
        assert isinstance(test_run, TestRun)

        assert len(self.list_tsvs_tbt) == len(test_run.list_tentacle_variant)
        for tsvs, tentacle_variant in zip(
            self.list_tsvs_tbt, test_run.list_tentacle_variant
        ):
            tsvs.remove_tentacle_variant(tentacle_variant)

    @property
    def tests_tbd(self) -> int:
        return sum([len(tsvs_tbt) for tsvs_tbt in self.list_tsvs_tbt])

    @property
    def iter_text_tsvs(self) -> Iterator[str]:
        for i in range(self.tentacles_required):
            tag = ["first", "second", "third"][i]
            for tsvs in self.list_tsvs_tbt[i]:
                yield f"{tsvs!r} {tag}"

    def generate(self, available_tentacles: list[Tentacle]) -> Iterator[TestRun]:
        tsvs_combinations = list(itertools.product(*self.list_tsvs_tbt))

        for tsvs_combination in tsvs_combinations:
            for tentacles in itertools.combinations(
                available_tentacles, self.tentacles_required
            ):

                def tentacles_available():
                    assert len(tsvs_combination) == len(tentacles)
                    for tsv, tentacle in zip(tsvs_combination, tentacles):
                        if tsv.tentacle_spec is not tentacle.tentacle_spec:
                            return False
                    return True

                if not tentacles_available():
                    continue

                list_tentacle_variant = [
                    TentacleVariant(
                        tentacle=tentacle,
                        board=variant.board,
                        variant=variant.variant,
                    )
                    for variant, tentacle in zip(tsvs_combination, tentacles)
                ]

                yield self.testrun_class(
                    testrun_spec=self,
                    list_tentacle_variant=list_tentacle_variant,
                )
                break
