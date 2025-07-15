from __future__ import annotations

import abc
import contextlib
import dataclasses
import logging
import pathlib
import typing
from collections.abc import Iterator

from .. import constants
from ..testcollection.baseclasses_spec import (
    ConnectedTentacles,
    TentacleMicropython,
    TentacleSpecVariant,
    TentacleSpecVariants,
    TestRole,
)
from ..testcollection.constants import (
    DELIMITER_TENTACLE,
    DELIMITER_TESTRUN,
    DELIMITER_TESTROLE,
)

if typing.TYPE_CHECKING:
    from ..mptest.util_testrunner import ResultsDir

logger = logging.getLogger(__name__)


@dataclasses.dataclass(repr=True)
class TestArgs:
    testresults_directory: ResultsDir
    repo_micropython_tests: pathlib.Path


# TODO: Remove
_ROLE_LABELS = ["First", "Second", "Third"]


@dataclasses.dataclass(slots=True, repr=True)
class TestRun:
    testrun_spec: TestRunSpec
    tentacle_variant: TentacleSpecVariant
    """
    This includes
    * tentacle
    * variant
    * role
    """
    tentacle_reference: TentacleMicropython | None
    """
    This is only set if subclass of 'class TestRunReference()' respective 'testrun_spec.requires_reference_tentacle'.
    """
    flash_skip: bool

    def __post_init__(self) -> None:
        assert isinstance(self.testrun_spec, TestRunSpec)
        assert isinstance(self.tentacle_variant, TentacleSpecVariant)
        assert isinstance(self.tentacle_reference, TentacleMicropython | None)
        if self.testrun_spec.requires_reference_tentacle:
            assert self.tentacle_reference is not None
        assert isinstance(self.flash_skip, bool)

    def mark_as_done(self) -> None:
        self.testrun_spec.mark_as_done(testrun=self)

    @property
    def timeout_s(self) -> float:
        return self.testrun_spec.timeout_s

    @abc.abstractmethod
    def test(self, testargs: TestArgs) -> None: ...

    @property
    def testid(self) -> str:
        """
        Example: run-perfbench.py,a@2d2d-lolin_D1-ESP8266_GENERIC
        If self.testrun_spec.requires_reference_tentacle:
         Example: run-perfbench.py,a@2d2d-lolin_D1-ESP8266_GENERIC-first
        This is the unique id of the testrun.
        """
        elems = [
            self.testrun_spec.label_testrun,
            DELIMITER_TENTACLE,
            self.tentacle_text,
        ]
        if self.testrun_spec.requires_reference_tentacle:
            elems.append(DELIMITER_TESTROLE)
            elems.append(self.tentacle_variant.role.value)
        return "".join(elems)

    @property
    def testid_group(self) -> str:
        """
        For example: run-perfbench.py@2d2d-lolin_D1-ESP8266_GENERIC
        This is used to group testruns to show flakiness.
        """
        return self.testrun_spec.label + DELIMITER_TENTACLE + self.tentacle_text

    @property
    def tentacles(self) -> Iterator[TentacleMicropython]:
        yield self.tentacle_variant.tentacle
        if self.tentacle_reference is not None:
            yield self.tentacle_reference

    @property
    @contextlib.contextmanager
    def active_led_on(self) -> typing.Generator[typing.Any]:
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

    @property
    def tentacle_text(self) -> str:
        """
        For example: 5f2c-RPI_PICO_W,2d2d-lolin_D1-ESP8266_GENERIC
        """

        def testid(tv: TentacleSpecVariant) -> str:
            if self.flash_skip:
                if len(tv.tentacle.tentacle_spec.build_variants) > 1:
                    return f"{tv.tentacle.label_short}-unknown"

            return f"{tv.tentacle.label_short}{tv.dash_variant}"

        return testid(self.tentacle_variant)

    @property
    def firmware_already_flashed(self) -> bool:
        a = self.tentacle_variant.board_variant
        b = self.tentacle_variant.tentacle.board_variant_normalized
        return a == b

    @property
    def debug_text(self) -> str:
        board_variants = [bv.board_variant for bv in self.tentacle_variant]
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
    def priority_sorter(
        testruns: list[TestRun],
        connected_tentacles: ConnectedTentacles,
    ) -> list[TestRun]:
        """
        Order by priority.
        In the list, the first element has the highest priority.
        """

        def priority(testrun: TestRun) -> tuple:
            build_variants = len(
                testrun.tentacle_variant.tentacle.tentacle_spec.build_variants
            )

            priorities = (
                # The more variants to compile, the higher the priority
                -build_variants,
                # To minimize reflashing, order by variant
                -testrun.firmware_already_flashed,
                # Finally, alphabetical order desc
                testrun.testid,
            )
            return priorities

        return sorted(testruns, key=priority)


@dataclasses.dataclass(slots=True, repr=True)
class TestRunSpec:
    """
    Tentacle_WLA_STA connects to Tentacle_WLAN_AP.
    Two tentacles connect to an AP and communicate together.

    Every tentacle has to be tested against two other tentacles. Once as fist, and once as second.
    """

    label: str
    """
    Example: 'RUN-TESTS_EXTMOD_HARDWARE'
    """
    helptext: str
    command: list[str]
    required_fut: constants.EnumFut
    requires_reference_tentacle: bool
    timeout_s: float
    testrun_class: type[TestRun]
    tsvs_todo: TentacleSpecVariants = dataclasses.field(
        default_factory=TentacleSpecVariants
    )
    testrun_idx0: int = 0
    """
    Example: 0, 1, 2
    If '--count=3' is given, there will be a 'TestRunSpec' for each run!
    """

    def __post_init__(self) -> None:
        assert isinstance(self.label, str)
        assert isinstance(self.helptext, str)
        assert isinstance(self.command, list)
        assert isinstance(self.required_fut, constants.EnumFut)
        assert isinstance(self.requires_reference_tentacle, bool)
        assert isinstance(self.timeout_s, float)
        assert isinstance(self.testrun_class, type(TestRun))
        assert isinstance(self.tsvs_todo, TentacleSpecVariants)
        assert isinstance(self.testrun_idx0, int)

    @property
    def label_testrun(self) -> str:
        """
        Example: 'RUN-TESTS_EXTMOD_HARDWARE#a'
        """
        return f"{self.label}{DELIMITER_TESTRUN}{chr(ord('a') + self.testrun_idx0)}"

    @property
    def command_executable(self) -> str:
        return self.command[0]

    @property
    def command_args(self) -> list[str]:
        return self.command[1:]

    def assign_tentacles(
        self,
        tentacles: ConnectedTentacles,
        tentacle_reference: TentacleMicropython | None,
    ) -> None:
        """
        Assign tentacle-variants (board-variants) to be tested.
        """
        assert isinstance(tentacles, ConnectedTentacles)

        _tentacles = tentacles.get_exclude_reference(tentacle_reference)
        selected_tentacles = _tentacles.get_by_fut(self.required_fut)

        roles = [TestRole.ROLE_FIRST]
        if self.requires_reference_tentacle:
            roles = [TestRole.ROLE_FIRST, TestRole.ROLE_SECOND]

        self.tsvs_todo = selected_tentacles.get_tsvs(roles=roles)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.label} {self.command_args})"

    def mark_as_done(self, testrun: TestRun) -> None:
        assert isinstance(testrun, TestRun)

        for tsvs in self.tsvs_todo:
            if tsvs.equals(testrun.tentacle_variant):
                self.tsvs_todo.remove(tsvs)
                return

    @property
    def tests_todo(self) -> int:
        return len(self.tsvs_todo)

    def generate(
        self,
        available_tentacles: list[TentacleMicropython],
        firmwares_built: set[str] | None,
        flash_skip: bool,
        tentacle_reference: TentacleMicropython | None,
    ) -> Iterator[TestRun]:
        for tentacle in available_tentacles:
            for tsv in self.tsvs_todo:
                if tsv.board == tentacle.tentacle_spec.board:
                    tentacle_variant = TentacleSpecVariant(
                        tentacle=tentacle,
                        variant=tsv.variant,
                        role=tsv.role,
                    )
                    yield self.testrun_class(
                        testrun_spec=self,
                        tentacle_variant=tentacle_variant,
                        tentacle_reference=tentacle_reference,
                        flash_skip=flash_skip,
                    )

    def pytest_print(self, indent: int, file: typing.TextIO) -> None:
        for idx0_role, role_tsvs_todo in enumerate(self.roles_tsvs_todo):
            label = _ROLE_LABELS[idx0_role]
            print(indent * "  " + f"{label:} {role_tsvs_todo.sorted_text!r}", file=file)
