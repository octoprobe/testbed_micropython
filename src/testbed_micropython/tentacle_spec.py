from __future__ import annotations

import dataclasses
import typing

from octoprobe.lib_tentacle import TentacleBase
from octoprobe.util_baseclasses import TentacleSpecBase
from octoprobe.util_constants import TAG_MCU

from .constants import TAG_BOARD, TAG_BUILD_VARIANTS


@dataclasses.dataclass(frozen=True, repr=True, eq=True, order=True)
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
        """
        variants = self.get_tag(TAG_BUILD_VARIANTS)
        if variants is None:
            return [""]
        return variants.split(":")

    def get_first_last_variant(self, last: bool) -> str:
        """
        Return "" for the first (default) variant.
        Return "RISCV" for the 'last_variant' of the RP_PICO2.
        """
        return self.build_variants[-1 if last else 0]


@dataclasses.dataclass(frozen=True, repr=True)
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
