"""
Classes required to define to specify the tests which have to run.
"""

from __future__ import annotations

import dataclasses

from octoprobe.lib_tentacle import Tentacle
from octoprobe.util_baseclasses import TentacleSpec

from testbed.constants import EnumFut
from testbed.mpbuild import build_api
from testbed.util_constants import TAG_VARIANTS


@dataclasses.dataclass(frozen=True, unsafe_hash=True)
class TentacleSpecVariant:
    tentacle_spec: TentacleSpec
    variant: str

    def __post_init__(self) -> None:
        assert isinstance(self.tentacle_spec, TentacleSpec)
        assert isinstance(self.variant, str)

    def __repr__(self) -> str:
        return self.board_variant

    @property
    def board(self) -> str:
        return self.tentacle_spec.tentacle_tag
        # boards = self.tentacle_spec.get_tag_mandatory(TAG_BOARDS)
        # for board_variant in board_variants(boards):
        #     return board_variant.board
        # raise ValueError("Programming error")

    @property
    def board_variant(self) -> str:
        if self.variant == "":
            return self.board
        return f"{self.board}-{self.variant}"


def tentacle_spec_2_tsvs(tentacle_spec: TentacleSpec) -> list[TentacleSpecVariant]:
    """
    ["RP_PICO2W-default", "RP_PICO2W-RISCV"]
    """
    assert isinstance(tentacle_spec, TentacleSpec)
    # return [f"{self.board}-{v}" for v in self.variants]
    return [
        TentacleSpecVariant(tentacle_spec=tentacle_spec, variant=v)
        for v in tentacle_spec_2_variants(tentacle_spec)
    ]


def tentacle_spec_2_variants(tentacle_spec: TentacleSpec) -> list[str]:
    """
    Example for RP2_PICO: ["", "RISCV"]
    Example for ESP8266_GENERIC: [""]
    """
    assert isinstance(tentacle_spec, TentacleSpec)

    assert isinstance(tentacle_spec, TentacleSpec)
    variants = tentacle_spec.get_tag(TAG_VARIANTS)
    if variants is None:
        return [""]
    return variants.split(":")

    # return variants.split(":")
    # boards = tentacle_spec.get_tag_mandatory(TAG_BOARDS)
    # return [i.variant for i in board_variants(boards=boards)]


@dataclasses.dataclass(frozen=True, repr=True, unsafe_hash=True)
class TentacleVariant:
    tentacle: Tentacle
    board: str
    variant: str

    def __post_init__(self) -> None:
        assert isinstance(self.tentacle, Tentacle)
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

    def get_only_board_variants(
        self,
        only_board_variants: list[str] | None,
    ) -> TentacleSpecVariants:
        if only_board_variants is None:
            return self
        assert isinstance(only_board_variants, list)
        return TentacleSpecVariants(
            {x for x in self if x.board_variant in only_board_variants}
        )


class ConnectedTentacles(list[Tentacle]):
    @property
    def tentacle_specs(self) -> set[TentacleSpec]:
        specs: set[TentacleSpec] = set()
        for t in self:
            specs.add(t.tentacle_spec)
        return specs

    @property
    def tsvs(self) -> TentacleSpecVariants:
        s = TentacleSpecVariants()
        for tentacle_spec in self.tentacle_specs:
            for tsv in tentacle_spec_2_tsvs(tentacle_spec):
                s.add(tsv)
        return s

    def get_by_fut(self, fut: EnumFut) -> ConnectedTentacles:
        return ConnectedTentacles([t for t in self if fut in t.tentacle_spec.futs])

    def get_only(self, board_variants: list[str] | None) -> ConnectedTentacles:
        assert isinstance(board_variants, list | None)

        if board_variants is None:
            return self

        boards = [build_api.split_board_variant(bv)[0] for bv in board_variants]
        return ConnectedTentacles(
            [t for t in self if t.tentacle_spec.tentacle_tag in boards]
        )
