"""
Constants required by this testbed.
"""

from __future__ import annotations

import enum
import pathlib
import typing

from octoprobe.util_baseclasses import TENTACLE_TYPE_MCU
from octoprobe.util_constants import (
    DIRECTORY_OCTOPROBE_DOWNLOADS,
    DIRECTORY_OCTOPROBE_GIT_CACHE,
)

if typing.TYPE_CHECKING:
    from octoprobe.lib_tentacle import TentacleBase

    from .tentacle_spec import TentacleMicropython

TAG_BUILD_VARIANTS = "build_variants"
TAG_BOARD = "board"

TESTBED_NAME = "testbed_micropython"
DEFAULT_REFERENCE_BOARD = "RPI_PICO_W"
ANY_REFERENCE_BOARD = ""

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent
DIRECTORY_GIT_REPO = DIRECTORY_OF_THIS_FILE.parent.parent
if (DIRECTORY_GIT_REPO / ".git").is_dir():
    DIRECTORY_RESULTS_PARENT = DIRECTORY_GIT_REPO
else:
    # If we have been installed into 'site-packages', the default will be ~/octoprobe_downloads/testresults
    DIRECTORY_RESULTS_PARENT = DIRECTORY_OCTOPROBE_DOWNLOADS
DIRECTORY_TESTRESULTS_DEFAULT = DIRECTORY_RESULTS_PARENT / "testresults"

DIRECTORY_GIT_CACHE = DIRECTORY_OCTOPROBE_GIT_CACHE
FILENAME_TESTBED_LOCK = pathlib.Path("/tmp/octoprobe/testbed.lock")
"""
Does not work: "/var/lock/octoprobe/testbed.lock": On Archlinux: Failed to create folder "/var/lock/octoprobe".
"""
SUBDIR_MPBUILD = "mpbuild"
DIRECTORY_MPBUILD_ARTIFACTS_DEFAULT = DIRECTORY_TESTRESULTS_DEFAULT / SUBDIR_MPBUILD


URL_FILENAME_DEFAULT = "."


class EnumTentacleType(enum.StrEnum):
    TENTACLE_MCU = TENTACLE_TYPE_MCU
    TENTACLE_DEVICE_POTPOURRY = "potourry"
    TENTACLE_DAQ_SALEAE = "daq_saleae"

    def get_tentacles_for_type(
        self,
        tentacles: list[TentacleMicropython],
        required_futs: list[EnumFut],
    ) -> list[TentacleBase]:
        """
        Select all tentacles which correspond to this
        EnumTentacleType and list[EnumFut].
        """

        def has_required_futs(t: TentacleMicropython) -> bool:
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

    @staticmethod
    def factory(fut: str) -> EnumFut:
        try:
            return EnumFut[fut]
        except KeyError as e:
            names = sorted([f.name for f in EnumFut])
            raise KeyError(
                f"'{fut}' not found. Valid values are: {','.join(names)}"
            ) from e


def is_url(filename: str) -> bool:
    assert isinstance(filename, str)

    for prefix in ("http://", "https://"):
        if filename.startswith(prefix):
            return True
    return False
