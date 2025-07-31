"""
Classes required to define to specify the tests which have to run.
"""

from __future__ import annotations

import dataclasses
import enum
import logging
import typing

from octoprobe.util_micropython_boards import VARIANT_UNKNOWN

from ..constants import EnumFut
from ..mpbuild.build_api import BoardVariant
from ..mptest.util_baseclasses import ArgsQuery
from ..tentacle_spec import TentacleMicropython, TentacleSpecMicropython

if typing.TYPE_CHECKING:
    from ..testcollection.baseclasses_run import TestRunSpecs

logger = logging.getLogger(__file__)


class TestRole(enum.StrEnum):
    ROLE_INSTANCE0 = "instance0"
    """
    See the test script, could be WLAN-STAT.
    """
    ROLE_INSTANCE1 = "instance1"
    """
    See the test script, could be WLAN-AP.
    """


@dataclasses.dataclass(frozen=True, unsafe_hash=True, order=True)
class TentacleSpecVariant:
    tentacle: TentacleMicropython
    variant: str
    role: TestRole
    testrun_idx0: int = 0
    """
    Example: 0, 1, 2
    If '--count=3' is given, there will be a 'TestRunSpec' for each run!
    """

    def __post_init__(self) -> None:
        assert isinstance(self.tentacle, TentacleMicropython)
        assert isinstance(self.variant, str)
        assert isinstance(self.role, TestRole)
        assert isinstance(self.testrun_idx0, int)

    def __repr__(self) -> str:
        return f"{self.board_variant}({self.testrun_idx0}, {self.role.name})"

    def equals(self, tentacle_variant: TentacleSpecVariant) -> bool:
        assert isinstance(tentacle_variant, TentacleSpecVariant)
        return (
            (self.testrun_idx0 == tentacle_variant.testrun_idx0)
            and (self.board_variant == tentacle_variant.board_variant)
            and (self.role == tentacle_variant.role)
        )

    @property
    def testrun_idx_text(self) -> str:
        """
        Example: 'a'
        """
        return chr(ord("a") + self.testrun_idx0)

    @property
    def board(self) -> str:
        tentacle_spec = self.tentacle.tentacle_spec
        assert isinstance(tentacle_spec, TentacleSpecMicropython)
        return tentacle_spec.board

    @property
    def board_variant(self) -> str:
        """
        Returns:
         'RPI_PICO2' for a default variant
         'RPI_PICO2-RISCV' for a variant
        """
        if self.variant == "":
            return self.board
        return f"{self.board}-{self.variant}"

    @property
    def dash_variant(self) -> str:
        """
        Example for RPI_PICO2: '' or '-RISCV'
        """
        if self.variant == "":
            return ""
        return "-" + self.variant


def tentacle_spec_2_tsvs(
    tentacle: TentacleMicropython,
    role: TestRole,
    count: int,
    flash_skip: bool,
) -> list[TentacleSpecVariant]:
    """
    ["RP_PICO2W-default", "RP_PICO2W-RISCV"]
    """
    assert isinstance(tentacle, TentacleMicropython)
    assert isinstance(role, TestRole)
    assert isinstance(count, int)

    variants = tentacle.tentacle_spec.build_variants
    if tentacle.tentacle_state.variants_required is not None:
        variants = tentacle.tentacle_state.variants_required
    if (len(variants) > 1) and flash_skip:
        # This board supports multiple variants: If we do not flash, we do not know the variant...
        variants = [VARIANT_UNKNOWN]
    return [
        TentacleSpecVariant(tentacle=tentacle, variant=v, role=role, testrun_idx0=idx0)
        for v in variants
        for idx0 in range(count)
    ]


class TentacleSpecVariants(list[TentacleSpecVariant]):
    def __repr__(self) -> str:
        board_variants = [tsv.board_variant for tsv in self]
        boards_variants_text = ", ".join(board_variants)
        return f"TentacleSpecVariants({boards_variants_text})"

    @property
    def sorted_text(self) -> list[str]:
        return sorted([s.board_variant for s in self])


class ConnectedTentacles(list[TentacleMicropython]):
    def get_tsvs(
        self,
        roles: list[TestRole],
        count: int,
        flash_skip: bool,
    ) -> TentacleSpecVariants:
        s: set[TentacleSpecVariant] = set()
        for tentacle in self:
            for role in roles:
                for tsv in tentacle_spec_2_tsvs(
                    tentacle=tentacle,
                    role=role,
                    count=count,
                    flash_skip=flash_skip,
                ):
                    s.add(tsv)
        return TentacleSpecVariants(sorted(s))

    def get_exclude_reference(
        self,
        exclude_reference: TentacleMicropython | None,
    ) -> ConnectedTentacles:
        if exclude_reference is None:
            return self
        assert isinstance(exclude_reference, TentacleMicropython)
        return ConnectedTentacles([t for t in self if exclude_reference is not t])

    def get_by_fut(self, fut: EnumFut) -> ConnectedTentacles:
        return ConnectedTentacles([t for t in self if fut in t.tentacle_spec.futs])

    def find_first_tentacle(self, board: str) -> TentacleMicropython | None:
        """
        Example 'board':
         * "RPI_PICO_W" (DEFAULT_REFERENCE_BOARD)
         * "" (ANY_REFERENCE_BOARD)

        Finds the first tentacle corresponding to 'board' and returns its tentacle.
        Returns None if not found.
        """
        assert isinstance(board, str)

        for t in self:
            if t.tentacle_spec.board == board:
                return t

        return None

    def query_boards(
        self,
        query: ArgsQuery,
        testrun_specs: TestRunSpecs,
        tentacle_reference: TentacleMicropython | None = None,
    ) -> ConnectedTentacles:
        assert isinstance(query, ArgsQuery)
        # assert isinstance(testrun_specs, TestRunSpecs)
        assert isinstance(tentacle_reference, TentacleMicropython | None)

        connected_boards = {t.tentacle_spec.tentacle_tag for t in self}

        query_only = {BoardVariant.parse(o).board for o in query.only}

        def board_not_connected_warning(boards: set[str]) -> None:
            for board in boards:
                if board not in connected_boards:
                    logger.warning(
                        f"Board '{board}' not found. Connected boards are {','.join(sorted(connected_boards))}"
                    )

        board_not_connected_warning(boards=query_only)
        board_not_connected_warning(boards=query.skip)

        selected_boards = connected_boards
        if len(query_only) > 0:
            selected_boards.intersection_update(query_only)
        if len(query.skip) > 0:
            selected_boards.difference_update(query.skip)

        # TODO(hans): Why has `connected_tentacles` to be evaluated here? We have the same variable in the outer context.
        connected_tentacles = [
            t for t in self if t.tentacle_spec.tentacle_tag in sorted(selected_boards)
        ]
        if len(query_only) > 0:
            # If a board with variant was specified. Example: --only-board=RPI_PICO2-RISCV
            # Then 'RISCV' has to be stored in the 'tentacle_state'.
            for connected_tentacle in connected_tentacles:
                for _board_variant in query.only:
                    board_variant = BoardVariant.parse(_board_variant)
                    if board_variant.has_variant_separator:
                        if (
                            connected_tentacle.tentacle_spec.board
                            == board_variant.board
                        ):
                            connected_tentacle.tentacle_state.set_variants_required(
                                [board_variant.variant]
                            )

        if tentacle_reference is not None:
            if testrun_specs.requires_reference_tentacle(connected_tentacles):
                if tentacle_reference not in connected_tentacles:
                    connected_tentacles.append(tentacle_reference)

        return ConnectedTentacles(connected_tentacles)
