"""
Classes required to define to specify the tests which have to run.
"""

from __future__ import annotations

import dataclasses


@dataclasses.dataclass(frozen=True, unsafe_hash=True)
class TentacleSpecVariant:
    tentacle_spec: TentacleSpec
    variant: str

    def __repr__(self) -> str:
        return f"{self.tentacle_spec.board}-{self.variant}"


class TentacleSpec:
    def __init__(self, board: str, variants: list[str], list_futs: list[str]) -> None:
        self.board = board
        self.variants = variants
        self.list_futs = list_futs

    @property
    def tsvs(self) -> list[TentacleSpecVariant]:
        """
        ["RP_PICO2W-default", "RP_PICO2W-RISCV"]
        """
        # return [f"{self.board}-{v}" for v in self.variants]
        return [
            TentacleSpecVariant(tentacle_spec=self, variant=v) for v in self.variants
        ]


@dataclasses.dataclass(frozen=True, unsafe_hash=True)
class TentacleVariant:
    tentacle: Tentacle
    variant: str

    def __repr__(self) -> str:
        return f"{self.tentacle.tentacle_spec.board}-{self.variant}"


@dataclasses.dataclass
class Tentacle:
    tentacle_spec: TentacleSpec
    serial: str

    # def __repr__(self)->str:
    #     return f"{self.__class__.__name__}({self.serial}, {self.tentacle_spec.__repr__()})"


class TentacleSpecVariants(set[TentacleSpecVariant]):
    def remove_tentacle_variant(self, tentacle_variant: TentacleVariant) -> None:
        for tsv in self:
            if tsv.tentacle_spec == tentacle_variant.tentacle.tentacle_spec:
                if tsv.variant == tentacle_variant.variant:
                    assert tsv in self
                    self.remove(tsv)
                    return


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
            for tsv in tentacle_spec.tsvs:
                s.add(tsv)
        return s
