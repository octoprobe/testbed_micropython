from __future__ import annotations

import abc
import contextlib
import dataclasses
import logging
import pathlib
import typing
from collections.abc import Iterator

from octoprobe.util_micropython_boards import VARIANT_SEPARATOR

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
    DELIMITER_TESTROLE,
    DELIMITER_TESTRUN,
)

if typing.TYPE_CHECKING:
    from ..mptest.util_testrunner import ResultsDir

logger = logging.getLogger(__name__)


@dataclasses.dataclass(repr=True)
class TestArgs:
    testresults_directory: ResultsDir
    repo_micropython_tests: pathlib.Path


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
        else:
            self.tentacle_reference = None
        assert isinstance(self.flash_skip, bool)

    def mark_as_done(self) -> None:
        self.testrun_spec.mark_as_done(testrun=self)

    @property
    def requires_reference_tentacle(self) -> bool:
        return self.testrun_spec.requires_reference_tentacle

    @property
    def timeout_s(self) -> float:
        return self.testrun_spec.timeout_s

    @abc.abstractmethod
    def test(self, testargs: TestArgs) -> None: ...

    @property
    def label_testrun(self) -> str:
        """
        Example: 'RUN-TESTS_EXTMOD_HARDWARE#a'
        """
        return f"{self.testrun_spec.label}{DELIMITER_TESTRUN}{self.tentacle_variant.testrun_idx_text}"

    @property
    def testid(self) -> str:
        """
        Example: run-perfbench.py,a@2d2d-RPI_PICO2-RISCV_GENERIC
        This is the unique id of the testrun.
        """
        return "".join(
            [
                self.label_testrun,
                DELIMITER_TENTACLE,
                self.tentacle_variant_role_text,
            ]
        )

    @property
    def tentacles(self) -> list[TentacleMicropython]:
        _tentacles = [self.tentacle_variant.tentacle]
        if self.tentacle_reference is not None:
            _tentacles.append(self.tentacle_reference)
        return _tentacles

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
    def tentacle_variant_text(self) -> str:
        """
        For example: 5f2c-RPI_PICO_W-unknown
        """
        text = self.tentacle_variant.tentacle.label_short
        if self.tentacle_variant.variant != "":
            text += VARIANT_SEPARATOR + self.tentacle_variant.variant
        return text

    @property
    def tentacle_variant_role_text(self) -> str:
        """
        For example: 5f2c-RPI_PICO_W-unknown-first
        """
        text = self.tentacle_variant_text
        if self.testrun_spec.requires_reference_tentacle:
            text += DELIMITER_TESTROLE + self.tentacle_variant.role.value
        return text

    @property
    def firmware_already_flashed(self) -> bool:
        if self.flash_skip:
            return True

        tentacle_variant = self.tentacle_variant
        tentacle_state = tentacle_variant.tentacle.tentacle_state
        if not tentacle_state.has_firmware_spec:
            # We do not have a firmware_spec, thus the tentacle hast not been flashed yet
            return False

        a = tentacle_variant.board_variant
        b = tentacle_variant.tentacle.tentacle_state.firmware_spec.board_variant.name_normalized
        assert isinstance(a, str)
        assert isinstance(b, str)
        return a == b

    @property
    def debug_text(self) -> str:
        return (
            f"TestRun({self.testrun_spec.label}, {self.tentacle_variant.board_variant})"
        )
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


@dataclasses.dataclass(slots=True, order=True)
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
    tsvs_total_count: int = -1

    def __post_init__(self) -> None:
        assert isinstance(self.label, str)
        assert isinstance(self.helptext, str)
        assert isinstance(self.command, list)
        assert isinstance(self.required_fut, constants.EnumFut)
        assert isinstance(self.requires_reference_tentacle, bool)
        assert isinstance(self.timeout_s, float)
        assert isinstance(self.testrun_class, type(TestRun))
        assert isinstance(self.tsvs_todo, TentacleSpecVariants)

    @property
    def command_executable(self) -> str:
        return self.command[0]

    @property
    def command_args(self) -> list[str]:
        return self.command[1:]

    def assign_tentacles(
        self,
        tentacles: ConnectedTentacles,
        count: int,
        flash_skip: bool,
    ) -> None:
        """
        Assign tentacle-variants (board-variants) to be tested.
        """
        assert isinstance(tentacles, ConnectedTentacles)

        # _tentacles = tentacles
        # if not self.requires_reference_tentacle:
        #     if tentacle_reference is not None:
        #         # This test does not require a reference tentacle
        #         # but the reference tentacle is specified.
        #         # Remove the reference tentacle from the test
        #         _tentacles = tentacles.get_exclude_reference(tentacle_reference)
        # selected_tentacles = _tentacles.get_by_fut(self.required_fut)
        selected_tentacles = tentacles.get_by_fut(self.required_fut)

        roles = [TestRole.ROLE_INSTANCE0]
        if self.requires_reference_tentacle:
            roles = [TestRole.ROLE_INSTANCE0, TestRole.ROLE_INSTANCE1]

        self.tsvs_todo = selected_tentacles.get_tsvs(
            roles=roles,
            count=count,
            flash_skip=flash_skip,
        )
        self.tsvs_total_count = len(self.tsvs_todo)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.label} {self.command_args})"

    def mark_as_done(self, testrun: TestRun) -> None:
        assert isinstance(testrun, TestRun)

        for tsvs in self.tsvs_todo:
            if tsvs.equals(testrun.tentacle_variant):
                self.tsvs_todo.remove(tsvs)
                return

        logger.warning(f"testrun not found: '{testrun.testrun_spec.label}")

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
        if self.requires_reference_tentacle:
            assert tentacle_reference is not None
            if tentacle_reference not in available_tentacles:
                return

        for tentacle in available_tentacles:
            for tsv in self.tsvs_todo:
                if firmwares_built is not None:
                    if tsv.board_variant not in firmwares_built:
                        continue

                if tsv.board == tentacle.tentacle_spec.board:
                    tentacle_variant = TentacleSpecVariant(
                        tentacle=tentacle,
                        variant=tsv.variant,
                        role=tsv.role,
                        testrun_idx0=tsv.testrun_idx0,
                    )
                    yield self.testrun_class(
                        testrun_spec=self,
                        tentacle_variant=tentacle_variant,
                        tentacle_reference=tentacle_reference,
                        flash_skip=flash_skip,
                    )

    def pytest_print(self, indent: int, file: typing.TextIO) -> None:
        for tsv in self.tsvs_todo:
            print(indent * "  " + repr(tsv), file=file)
