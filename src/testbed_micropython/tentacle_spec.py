from __future__ import annotations

import dataclasses
import typing

from octoprobe.lib_tentacle import TentacleBase
from octoprobe.util_baseclasses import TentacleSpecBase
from octoprobe.util_constants import TAG_MCU
from octoprobe.util_micropython_boards import VARIANT_SEPARATOR, VARIANT_UNKNOWN

from .constants import EnumFut, TAG_BOARD, TAG_BUILD_VARIANTS

if typing.TYPE_CHECKING:
    from .testcollection.baseclasses_spec import (
        TentacleSpecVariant,
        TentacleSpecVariants,
        TestRole,
    )


@dataclasses.dataclass(frozen=True, slots=True, repr=True, eq=True, order=True)
class TentacleSpecMicropython(TentacleSpecBase):
    mcu_config: McuConfig | None = None

    def __hash__(self) -> int:  # pylint: disable=useless-parent-delegation
        return super().__hash__()

    @property
    def board(self) -> str:
        """
        The micropython board.

        If
          tags="board=ESP8266_GENERIC, ..."
        is defined, it will be used.
        Fallback to 'tentacle_tag'.
        """
        board = self.get_tag(TAG_BOARD)
        if board is not None:
            return board
        return self.tentacle_tag

    @property
    def description(self) -> str:
        mcu = self.get_tag(TAG_MCU)
        if mcu is None:
            return self.board
        return mcu + "/" + self.board

    @property
    def build_variants(self) -> list[str]:
        """
        Example for PICO: ["", "RISCV"]
        Example for ESP8266_GENERIC: [""]

        How to use 'build_variants':
        * missing: defaults to "build_variants="
        * "build_variants=": Will test PICO-"" only
        * "build_variants=RISCV": Will test PICO-"RISCV" only
        * "build_variants=:RISCV": Will test both, PICO-"" and PICO-"RISCV"
        """
        variants = self.get_tag(TAG_BUILD_VARIANTS)
        if variants is None:
            return [""]
        return variants.split(":")

    @property
    def board_build_variants(self) -> list[str]:
        """
        Example for PICO: ["PICO", "PICO-RISCV"]
        Example for ESP8266_GENERIC: ["ESP8266_GENERIC"]
        """

        def join(variant: str) -> str:
            if variant == "":
                return self.board
            return self.board + VARIANT_SEPARATOR + variant

        return [join(variant) for variant in self.build_variants]

    def get_first_last_variant(self, last: bool) -> str:
        """
        Return "" for the first (default) variant.
        Return "RISCV" for the 'last_variant' of the RP_PICO2.
        """
        return self.build_variants[-1 if last else 0]


def tentacle_spec_2_tsvs(
    tentacle_spec: TentacleSpecMicropython,
    role: TestRole,
    flash_skip: bool,
) -> list[TentacleSpecVariant]:
    """
    ["RP_PICO2W-default", "RP_PICO2W-RISCV"]
    """
    assert isinstance(tentacle_spec, TentacleSpecMicropython)
    from .testcollection.baseclasses_spec import TentacleSpecVariant, TestRole

    assert isinstance(role, TestRole)

    variants = tentacle_spec.build_variants
    # if tentacle_spec.tentacle_state.variants_required is not None:
    #     variants = tentacle_spec.tentacle_state.variants_required
    # if (len(variants) > 1) and flash_skip:
    #     # This board supports multiple variants: If we do not flash, we do not know the variant...
    #     variants = [VARIANT_UNKNOWN]
    if (len(variants) > 1) and flash_skip:
        # This board supports multiple variants: If we do not flash, we do not know the variant...
        variants = [VARIANT_UNKNOWN]
    return [
        TentacleSpecVariant(tentacle_spec=tentacle_spec, variant=v, role=role)
        for v in variants
    ]


class TentacleSpecsMicropython(set[TentacleSpecMicropython]):
    def get_by_fut(self, fut: EnumFut) -> TentacleSpecsMicropython:
        return TentacleSpecsMicropython(spec for spec in self if fut in spec.futs)

    def get_tsvs(
        self,
        roles: list[TestRole],
        flash_skip: bool,
    ) -> TentacleSpecVariants:
        s: set[TentacleSpecVariant] = set()
        for tentacle_spec in self:
            for role in roles:
                for tsv in tentacle_spec_2_tsvs(
                    tentacle_spec=tentacle_spec,
                    role=role,
                    flash_skip=flash_skip,
                ):
                    s.add(tsv)

        from .testcollection.baseclasses_spec import TentacleSpecVariants

        return TentacleSpecVariants(sorted(s))


@dataclasses.dataclass(frozen=True, slots=True, repr=True)
class McuConfig:
    """
    These variables will be replaced in micropython code
    """

    micropython_perftest_args: list[str] | None = None

    def __post_init__(self) -> None:
        assert isinstance(self.micropython_perftest_args, list | None)


class TentacleMicropython(TentacleBase):
    @property
    @typing.override
    def pytest_id(self) -> str:
        """
        Example: 1831-pico2(RPI_PICO2-RISCV)
        Example: 1331-daq
        """
        name = self.label_short
        if self.is_mcu:
            if self.tentacle_state.firmware_spec is None:
                name += "(no-flashing)"
            else:
                name += f"({self.tentacle_state.firmware_spec.board_variant.name_normalized})"
        return name

    @property
    def tentacle_spec(self) -> TentacleSpecMicropython:
        """
        Just does typcasting from TentacleSpecBase to TentacleSpecMicropython
        """
        tentacle_spec_base = self.tentacle_spec_base
        assert isinstance(tentacle_spec_base, TentacleSpecMicropython)
        return tentacle_spec_base

    @property
    def unknown_variant(self) -> str:
        """
        The variant which is to be flashed to the tentacle.

        Examples for RPI_PICO2_W
            Example: ""
            Example: "-RISCV"
            Example: "-unknown"
        """
        build_variant = self.tentacle_spec.build_variants[0]
        if not self.tentacle_state.has_firmware_spec:
            if len(self.tentacle_spec.build_variants) > 1:
                return VARIANT_SEPARATOR + VARIANT_UNKNOWN
        if build_variant == "":
            return build_variant
        return VARIANT_SEPARATOR + build_variant

    @property
    def unknown_board_variant_normalized(self) -> str:
        """
        Example: RPI_PICO2_W\n
        Example: RPI_PICO2_W-RISCV\n
        Example: RPI_PICO2_W-unknown\n
        """
        return f"{self.tentacle_spec_base.tentacle_tag}{self.unknown_variant}"

    # @property
    # def serial_board_variant(self) -> str:
    #     """
    #     Example: 5f2c-RPI_PICO2_W
    #     Example: 5f2c-RPI_PICO2_W-RISCV
    #     Example: 5f2c-RPI_PICO2_W-unknown
    #     """
    #     return f"{self.label_short}{self.variant}"
