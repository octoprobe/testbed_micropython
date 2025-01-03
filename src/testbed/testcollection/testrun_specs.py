from __future__ import annotations

import abc
import contextlib
import dataclasses
import itertools
import pathlib
import typing
from collections.abc import Iterator

from octoprobe.lib_tentacle import Tentacle

from testbed.constants import EnumFut

from .baseclasses_spec import (
    ConnectedTentacles,
    ListTentacleSpecVariants,
    TentacleSpecVariants,
    TentacleVariant,
)

if typing.TYPE_CHECKING:
    from testbed.mptest.util_testrunner import ResultsDir


@dataclasses.dataclass(repr=True)
class TestArgs:
    testresults_directory: ResultsDir
    repo_micropython_tests: pathlib.Path


@dataclasses.dataclass(repr=True)
class TestRun:
    testrun_spec: TestRunSpec
    list_tentacle_variant: list[TentacleVariant]

    def __post_init__(self) -> None:
        assert isinstance(self.testrun_spec, TestRunSpec)
        assert isinstance(self.list_tentacle_variant, list)

    def done(self) -> None:
        self.testrun_spec.done(test_run=self)

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

    @property
    @contextlib.contextmanager
    def active_led_on(self) -> typing.Generator[typing.Any, None, None]:
        """
        Turn active leds on during the test
        """
        try:
            for t in self.tentacles:
                t.infra.mcu_infra.active_led(on=True)
            yield
        finally:
            for t in self.tentacles:
                t.infra.mcu_infra.active_led(on=False)


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
        self.list_tsvs_todo = ListTentacleSpecVariants()

    @property
    def command_executable(self) -> str:
        return self.command[0]

    @property
    def command_args(self) -> list[str]:
        return self.command[1:]

    def assign_tentacles(
        self,
        tentacles: ConnectedTentacles,
        only_board_variants: list[str] | None,
        flash_skip: bool,
    ) -> None:
        """
        Assign tentacle-variants (board-variants) to be tested.
        """
        assert isinstance(tentacles, ConnectedTentacles)
        assert isinstance(only_board_variants, list | None)
        assert isinstance(flash_skip, bool)

        selected_tentacles = tentacles.get_by_fut(self.required_fut)
        tsvs_todo = selected_tentacles.get_tsvs(flash_skip=flash_skip)
        tsvs_todo = tsvs_todo.get_only_board_variants(
            only_board_variants=only_board_variants
        )
        self.list_tsvs_todo = ListTentacleSpecVariants(
            [TentacleSpecVariants(tsvs_todo) for _ in range(self.tentacles_required)]
        )

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
            tsvs.remove_tentacle_variant(tentacle_variant=tentacle_variant)

    @property
    def tests_todo(self) -> int:
        return self.list_tsvs_todo.tests_todo

    @property
    def iter_text_tsvs(self) -> Iterator[str]:
        for i in range(self.tentacles_required):
            tag = ["first", "second", "third"][i]
            for tsvs in self.list_tsvs_todo[i]:
                yield f"{tsvs!r} {tag}"

    def generate(
        self,
        available_tentacles: list[Tentacle],
        firmwares_built: set[str],
    ) -> Iterator[TestRun]:
        assert isinstance(available_tentacles, list)
        assert isinstance(firmwares_built, set)

        list_tsvs_todo = self.list_tsvs_todo.filter_firmwares_built(
            firmwares_built=firmwares_built
        )
        tsvs_combinations = list(itertools.product(*list_tsvs_todo))

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
