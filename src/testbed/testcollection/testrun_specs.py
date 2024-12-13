from __future__ import annotations

import abc
import copy
import dataclasses
import itertools
import pathlib
import typing
from collections.abc import Iterator

from octoprobe.lib_tentacle import Tentacle

from testbed.constants import EnumFut

from .baseclasses_spec import (
    ConnectedTentacles,
    TentacleSpecVariants,
    TentacleVariant,
)

if typing.TYPE_CHECKING:
    from testbed.mptest.util_testrunner import ResultsDir


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
        tentacles = ",".join(
            [
                f"{tv.tentacle.label_short}{tv.dash_variant}"
                for tv in self.list_tentacle_variant
            ]
        )
        return f"{self.testrun_spec.label}[{tentacles}]"


@dataclasses.dataclass
class TestRunSpec:
    """
    Tentacle_WLA_STA connects to Tentacle_WLAN_AP.
    Two tentacles connect to an AP and communicate together.

    Every tentacle has to be tested against two other tentacles. Once as fist, and once as second.
    """

    def __init__(
        self,
        label: str,
        helptext: str,
        command: list[str],
        required_fut: EnumFut,
        required_tentacles_count: int,
        testrun_class: type[TestRun] = TestRun,
    ) -> None:
        assert isinstance(label, str)
        assert isinstance(helptext, str)
        assert isinstance(command, list)
        assert isinstance(required_fut, EnumFut)
        assert isinstance(required_tentacles_count, int)
        assert isinstance(testrun_class, type(TestRun))

        self.command: list[str] = command
        self.label: str = label
        self.helptext: str = helptext
        self.testrun_class: type[TestRun] = testrun_class
        self.required_fut: EnumFut = required_fut
        self.tentacles_required: int = required_tentacles_count
        self.list_tsvs_todo: list[TentacleSpecVariants] = []

    @property
    def command_executable(self) -> str:
        return self.command[0]

    @property
    def command_args(self) -> list[str]:
        return self.command[1:]

    def assign_tentacles(self, tentacles: ConnectedTentacles) -> None:
        assert isinstance(tentacles, ConnectedTentacles)
        selected_tentacles = tentacles.get_by_fut(self.required_fut)
        tsvs_todo = selected_tentacles.tsvs
        self.list_tsvs_todo = [
            TentacleSpecVariants(tsvs_todo) for _ in range(self.tentacles_required)
        ]

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.label} {self.command_args})"

    def done(self, test_run: TestRun) -> None:
        assert isinstance(test_run, TestRun)

        assert len(self.list_tsvs_todo) == len(test_run.list_tentacle_variant)
        for tsvs, tentacle_variant in zip(
            self.list_tsvs_todo,
            test_run.list_tentacle_variant,
            strict=False,
        ):
            tsvs.remove_tentacle_variant(tentacle_variant)

    @property
    def tests_todo(self) -> int:
        return sum([len(tsvs_todo) for tsvs_todo in self.list_tsvs_todo])

    @property
    def iter_text_tsvs(self) -> Iterator[str]:
        for i in range(self.tentacles_required):
            tag = ["first", "second", "third"][i]
            for tsvs in self.list_tsvs_todo[i]:
                yield f"{tsvs!r} {tag}"

    def generate(self, available_tentacles: list[Tentacle]) -> Iterator[TestRun]:
        tsvs_combinations = list(itertools.product(*self.list_tsvs_todo))

        for tsvs_combination in tsvs_combinations:
            for tentacles in itertools.combinations(
                available_tentacles, self.tentacles_required
            ):

                def tentacles_available() -> bool:
                    assert len(tsvs_combination) == len(tentacles)
                    for tsv, tentacle in zip(tsvs_combination, tentacles, strict=False):
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
                    for variant, tentacle in zip(
                        tsvs_combination, tentacles, strict=False
                    )
                ]

                yield self.testrun_class(
                    testrun_spec=self,
                    list_tentacle_variant=list_tentacle_variant,
                )
                break
