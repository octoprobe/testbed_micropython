from __future__ import annotations

import dataclasses

from octoprobe.util_baseclasses import TentacleSpec
from octoprobe.util_constants import TAG_MCU

from testbed.constants import TAG_BOARD, TAG_BUILD_VARIANTS


class TentacleSpecMicropython(TentacleSpec):
    @property
    def micropython_board(self) -> str:
        """
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
            return self.micropython_board
        return mcu + "/" + self.micropython_board

    @property
    def build_variants(self) -> list[str]:
        """
        Example for RP2_PICO: ["", "RISCV"]
        Example for ESP8266_GENERIC: [""]
        """
        variants = self.get_tag(TAG_BUILD_VARIANTS)
        if variants is None:
            return [""]
        return variants.split(":")


@dataclasses.dataclass
class McuConfig:
    """
    These variables will be replaced in micropython code
    """

    micropython_perftest_args: list[str] | None = None

    def __post_init__(self) -> None:
        assert isinstance(self.micropython_perftest_args, list | None)
