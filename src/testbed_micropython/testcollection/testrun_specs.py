from __future__ import annotations

import abc
import contextlib
import dataclasses
import pathlib
import typing
from collections.abc import Iterator

from ..constants import EnumFut
from ..testcollection.baseclasses_spec import (
    ConnectedTentacles,
    RolesTentacleSpecVariants,
    TentacleMicropython,
    TentacleSpecVariants,
    TentacleVariant,
)

if typing.TYPE_CHECKING:
    from ..mptest.util_testrunner import ResultsDir

TIMEOUT_FLASH_S = 60.0


@dataclasses.dataclass(repr=True)
class TestArgs:
    testresults_directory: ResultsDir
    repo_micropython_tests: pathlib.Path


_ROLE_LABELS = ["First", "Second", "Third"]


@dataclasses.dataclass(repr=True)
class TestRun:
    testrun_spec: TestRunSpec
    list_tentacle_variant: list[TentacleVariant]

    def __post_init__(self) -> None:
        assert isinstance(self.testrun_spec, TestRunSpec)
        assert isinstance(self.list_tentacle_variant, list)

    def mark_as_done(self) -> None:
        self.testrun_spec.mark_as_done(testrun=self)

    @property
    def timeout_s(self) -> float:
        return self.testrun_spec.timeout_s

    @abc.abstractmethod
    def test(self, testargs: TestArgs) -> None: ...

    @property
    def tentacles(self) -> list[TentacleMicropython]:
        return [x.tentacle for x in self.list_tentacle_variant]

    @property
    def testid(self) -> str:
        """
        For example: run-perfbench.py[2d2d-lolin_D1-ESP8266_GENERIC]
        """
        return self.testid_patch(flash_skip=False)

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

    def testid_patch(self, flash_skip: bool) -> str:
        assert isinstance(flash_skip, bool)

        def testid(tv: TentacleVariant) -> str:
            if flash_skip:
                if len(tv.tentacle.tentacle_spec.build_variants) > 1:
                    return f"{tv.tentacle.label_short}-unknown"

            return f"{tv.tentacle.label_short}{tv.dash_variant}"

        tentacles = ",".join([testid(tv) for tv in self.list_tentacle_variant])
        return f"{self.testrun_spec.label}[{tentacles}]"

    @property
    def debug_text(self) -> str:
        board_variants = [bv.board_variant for bv in self.list_tentacle_variant]
        return f"TestRun({self.testrun_spec.label}, {', '.join(board_variants)})"
        # return self.testid

    def pytest_print(self, indent: int, file=typing.TextIO) -> None:
        # print(indent * "  " + f"{self!r}", file=file)
        print(indent * "  " + f"{self.debug_text} / {self.testid}", file=file)

    @staticmethod
    def alphabetical_sorter(testruns: list[TestRun]) -> list[TestRun]:
        def f(testrun: TestRun) -> str:
            return testrun.testid

        return sorted(testruns, key=f)

    @staticmethod
    def priority_sorter(testruns: list[TestRun]) -> list[TestRun]:
        """
        Order by priority.
        In the list, the first element has the highest priority.
        """

        def priority(testrun: TestRun) -> tuple:
            build_variants = sum(
                [
                    len(tentacle.tentacle_spec.build_variants)
                    for tentacle in testrun.tentacles
                ]
            )
            priorities = (
                # The more variants to compile, the higher the priority
                -build_variants,
                # The more tentacles involved, the higher the priority
                -len(testrun.tentacles),
                # Finally, alphabetical order desc
                testrun.testid,
            )
            return priorities

        return sorted(testruns, key=priority)


@dataclasses.dataclass(repr=True)
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
        timeout_s: float,
        testrun_class: type[TestRun] = TestRun,
    ) -> None:
        assert isinstance(label, str)
        assert isinstance(helptext, str)
        assert isinstance(command, list)
        assert isinstance(required_fut, EnumFut)
        assert isinstance(required_tentacles_count, int)
        assert isinstance(timeout_s, float)
        assert isinstance(testrun_class, type(TestRun))

        self.command = command
        self.label = label
        self.helptext = helptext
        self.testrun_class = testrun_class
        self.required_fut = required_fut
        self.tentacles_required = required_tentacles_count
        self.timeout_s = timeout_s
        self.roles_tsvs_todo = RolesTentacleSpecVariants()

    @property
    def command_executable(self) -> str:
        return self.command[0]

    @property
    def command_args(self) -> list[str]:
        return self.command[1:]

    def assign_tentacles(self, tentacles: ConnectedTentacles) -> None:
        """
        Assign tentacle-variants (board-variants) to be tested.
        """
        assert isinstance(tentacles, ConnectedTentacles)

        selected_tentacles = tentacles.get_by_fut(self.required_fut)
        if len(selected_tentacles) < self.tentacles_required:
            # Example: Just one Lolin is connected (FUT_WLAN)
            # But there is no other FUT_WLAN we could test against!
            return
        tsvs_todo = selected_tentacles.get_tsvs()
        self.roles_tsvs_todo = RolesTentacleSpecVariants(
            [TentacleSpecVariants(tsvs_todo) for _ in range(self.tentacles_required)]
        )
        self.roles_tsvs_todo.verify(required_tentacles_count=self.tentacles_required)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.label} {self.command_args})"

    def mark_as_done(self, testrun: TestRun) -> None:
        assert isinstance(testrun, TestRun)

        assert len(self.roles_tsvs_todo) == len(testrun.list_tentacle_variant)
        for tsvs, tentacle_variant in zip(
            self.roles_tsvs_todo,
            testrun.list_tentacle_variant,
            strict=False,
        ):
            tsvs.remove_tentacle_variant(tentacle_variant=tentacle_variant)

    @property
    def tests_todo(self) -> int:
        return self.roles_tsvs_todo.tests_todo

    def generate(
        self,
        available_tentacles: list[TentacleMicropython],
        firmwares_built: set[str] | None,
    ) -> Iterator[TestRun]:
        def iter_tvs(tentacle: TentacleMicropython) -> typing.Iterator[TentacleVariant]:
            for variant in tentacle.tentacle_spec.build_variants:
                tv = TentacleVariant(
                    tentacle=tentacle,
                    board=tentacle.tentacle_spec.board,
                    variant=variant,
                )
                if firmwares_built is not None:
                    if tv.board_variant not in firmwares_built:
                        continue
                yield tv

        if self.tentacles_required == 1:
            for tentacle in available_tentacles:
                for tv in iter_tvs(tentacle):
                    first_second = [tv]
                    if self._matches(first_second):
                        yield self.testrun_class(
                            testrun_spec=self,
                            list_tentacle_variant=first_second,
                        )
            return

        if self.tentacles_required == 2:
            for tentacle1 in available_tentacles:
                for tentacle2 in available_tentacles:
                    if tentacle1 is tentacle2:
                        continue
                    for tv1 in iter_tvs(tentacle1):
                        for tv2 in iter_tvs(tentacle2):
                            first_second = [tv1, tv2]
                            if self._matches(first_second):
                                yield self.testrun_class(
                                    testrun_spec=self,
                                    list_tentacle_variant=first_second,
                                )
            return

        raise ValueError(f"Not supported: {self.tentacles_required=}")

    def _matches(self, tvs: list[TentacleVariant]) -> bool:
        """
        Return True if at lease 1 role matches.
        Example tvs: Tentacle A is WLAN-First <-> Tentacle B is WLAN-Second.
        """
        assert len(tvs) == len(self.roles_tsvs_todo)
        for tentacle_variant, tsvs in zip(tvs, self.roles_tsvs_todo, strict=False):
            assert isinstance(tentacle_variant, TentacleVariant)
            assert isinstance(tsvs, TentacleSpecVariants)
            for tsv in tsvs:
                if tentacle_variant.board_variant == tsv.board_variant:
                    return True
        return False

    def pytest_print(self, indent: int, file: typing.TextIO) -> None:
        for idx0_role, role_tsvs_todo in enumerate(self.roles_tsvs_todo):
            label = _ROLE_LABELS[idx0_role]
            print(indent * "  " + f"{label:} {role_tsvs_todo.sorted_text!r}", file=file)
