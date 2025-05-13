"""
Classes required to define to specify the tests which have to run.
"""

from __future__ import annotations

import dataclasses
import logging

from ..constants import EnumFut
from ..mptest.util_baseclasses import ArgsQuery
from ..tentacle_spec import TentacleMicropython, TentacleSpecMicropython

logger = logging.getLogger(__file__)


@dataclasses.dataclass(frozen=True, unsafe_hash=True, order=True)
class TentacleSpecVariant:
    tentacle_spec: TentacleSpecMicropython
    variant: str

    def __post_init__(self) -> None:
        assert isinstance(self.tentacle_spec, TentacleSpecMicropython)
        assert isinstance(self.variant, str)

    def __repr__(self) -> str:
        return self.board_variant

    @property
    def board(self) -> str:
        tentacle_spec = self.tentacle_spec
        assert isinstance(tentacle_spec, TentacleSpecMicropython)
        return tentacle_spec.board

    @property
    def board_variant(self) -> str:
        """
        Returns:
         'RPI_PICO2' for a default variant
         'RPI_PICO2-RISCV' for a variant
        #  'ESP8266_GENERIC' for a default variant
        #  'ESP8266_GENERIC-FLASH_512K' for a variant
        """
        if self.variant == "":
            return self.board
        return f"{self.board}-{self.variant}"


def tentacle_spec_2_tsvs(
    tentacle_spec: TentacleSpecMicropython,
) -> list[TentacleSpecVariant]:
    """
    ["RP_PICO2W-default", "RP_PICO2W-RISCV"]
    """
    assert isinstance(tentacle_spec, TentacleSpecMicropython)

    variants = tentacle_spec.build_variants
    return [
        TentacleSpecVariant(tentacle_spec=tentacle_spec, variant=v) for v in variants
    ]


@dataclasses.dataclass(frozen=True, repr=True, unsafe_hash=True)
class TentacleVariant:
    tentacle: TentacleMicropython
    board: str
    variant: str

    def __post_init__(self) -> None:
        assert isinstance(self.tentacle, TentacleMicropython)
        assert isinstance(self.board, str)
        assert isinstance(self.variant, str)

    @property
    def board_variant(self) -> str:
        """
        Example: RPI_PICO2-RISCV
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

    def __repr__(self) -> str:
        return f"{self.tentacle.tentacle_serial_number[:4]}_{self.tentacle.tentacle_spec.tentacle_tag} variant={self.variant}"


class TentacleSpecVariants(set[TentacleSpecVariant]):
    def __repr__(self) -> str:
        board_variants = [tsv.board_variant for tsv in self]
        boards_variants_text = ", ".join(board_variants)
        return f"TentacleSpecVariants({boards_variants_text})"

    def remove_tentacle_variant(
        self,
        tentacle_variant: TentacleVariant,
    ) -> None:
        assert isinstance(tentacle_variant, TentacleVariant)
        for tsv in self:
            if tsv.tentacle_spec == tentacle_variant.tentacle.tentacle_spec:
                if tsv.variant == tentacle_variant.variant:
                    assert tsv in self
                    self.remove(tsv)
                    return

        logger.warning(
            f"remove_tentacle_variant(): Could not remove as not found: {tentacle_variant.board_variant}"
        )

    @property
    def sorted_text(self) -> list[str]:
        return sorted([s.board_variant for s in self])


class RolesTentacleSpecVariants(list[TentacleSpecVariants]):
    """
    Assert: len(self) == required_tentacles_count
    self[0]: Role WLAN-First
    self[1]: Role WLAN-Second
    """

    def verify(self, required_tentacles_count: int) -> None:
        assert len(self) == required_tentacles_count

    @property
    def tests_todo(self) -> int:
        return sum(len(tsvs_todo) for tsvs_todo in self)


class ConnectedTentacles(list[TentacleMicropython]):
    @property
    def tentacle_specs(self) -> set[TentacleSpecMicropython]:
        specs: set[TentacleSpecMicropython] = set()
        for t in self:
            specs.add(t.tentacle_spec)
        return specs

    def get_tsvs(self) -> TentacleSpecVariants:
        s = TentacleSpecVariants()
        for tentacle_spec in self.tentacle_specs:
            for tsv in tentacle_spec_2_tsvs(tentacle_spec=tentacle_spec):
                s.add(tsv)
        return s

    def get_by_fut(self, fut: EnumFut) -> ConnectedTentacles:
        return ConnectedTentacles([t for t in self if fut in t.tentacle_spec.futs])

    def query_boards(self, query: ArgsQuery) -> ConnectedTentacles:
        connected_boards = {t.tentacle_spec.tentacle_tag for t in self}

        def board_not_connected_warning(boards: set[str]) -> None:
            for board in boards:
                if board not in connected_boards:
                    logger.warning(
                        f"Board '{board}' not found. Connected boards are {','.join(sorted(connected_boards))}"
                    )

        board_not_connected_warning(boards=query.only)
        board_not_connected_warning(boards=query.skip)

        selected_boards = connected_boards
        if len(query.only) > 0:
            selected_boards.intersection_update(query.only)
        if len(query.skip) > 0:
            selected_boards.difference_update(query.skip)

        return ConnectedTentacles(
            [t for t in self if t.tentacle_spec.tentacle_tag in sorted(selected_boards)]
        )
