"""
Constants required by this testbed.
"""

from __future__ import annotations

import enum
import pathlib
import typing

from octoprobe.util_baseclasses import TENTACLE_TYPE_MCU

if typing.TYPE_CHECKING:
    from octoprobe.lib_tentacle import Tentacle

TAG_BUILD_VARIANTS = "build_variants"
TAG_BOARD = "board"

TESTBED_NAME = "testbed_micropython"

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent
DIRECTORY_REPO = DIRECTORY_OF_THIS_FILE.parent.parent
assert (DIRECTORY_REPO / "src" / "testbed").is_dir()
DIRECTORY_DOWNLOADS = DIRECTORY_REPO / "downloads"
DIRECTORY_TESTRESULTS = DIRECTORY_REPO / "results"
DIRECTORY_GIT_CACHE = DIRECTORY_REPO / "git_cache"
FILENAME_TESTBED_LOCK = DIRECTORY_REPO / "testbed.lock"
DIRECTORY_MPBUILD_ARTIFACTS = DIRECTORY_REPO / "results" / "mpbuild"

URL_FILENAME_DEFAULT = "."


class EnumTentacleType(enum.StrEnum):
    TENTACLE_MCU = TENTACLE_TYPE_MCU
    TENTACLE_DEVICE_POTPOURRY = "potourry"
    TENTACLE_DAQ_SALEAE = "daq_saleae"

    def get_tentacles_for_type(
        self,
        tentacles: list[Tentacle],
        required_futs: list[EnumFut],
    ) -> list[Tentacle]:
        """
        Select all tentacles which correspond to this
        EnumTentacleType and list[EnumFut].
        """

        def has_required_futs(t: Tentacle) -> bool:
            if t.tentacle_spec.tentacle_type == self:
                for required_fut in required_futs:
                    if required_fut in t.tentacle_spec.futs:
                        return True
            return False

        return [t for t in tentacles if has_required_futs(t)]


class EnumFut(enum.StrEnum):
    FUT_MCU_ONLY = enum.auto()
    """
    Do not provide a empty list, use FUT_MCU_ONLY instead!
    """
    FUT_EXTMOD_HARDWARE = enum.auto()
    """
    rx-tx loopback connection
    """
    FUT_WLAN = enum.auto()
    FUT_BLE = enum.auto()


def is_url(filename: str) -> bool:
    assert isinstance(filename, str)

    for prefix in ("http://", "https://"):
        if filename.startswith(prefix):
            return True
    return False
