import logging
import pathlib

import pytest
from octoprobe.lib_tentacle import Tentacle
from octoprobe.util_dut_programmers import (
    FirmwareBuildSpec,
    FirmwareDownloadSpec,
    FirmwareNoFlashingSpec,
    FirmwareSpecBase,
)
from octoprobe.util_micropython_boards import BoardVariant

from .util_firmware_mpbuild import collect_firmware_specs

logger = logging.getLogger(__file__)
PYTEST_OPT_DOWNLOAD_FIRMWARE = "--firmware-json"
PYTEST_OPT_BUILD_FIRMWARE = "--firmware-build-url"
PYTEST_OPT_BUILD_FIRMWARE_MOCK = "MOCK"


def get_firmware_specs(
    config: pytest.Config, tentacles: list[Tentacle]
) -> list[FirmwareSpecBase]:
    """
    Given: arguments to pytest, for example PYTEST_OPT_FIRMWARE.
    Now we create firmware specs.
    In case of PYTEST_OPT_FIRMWARE:
      The firmware has to be downloaded.
    In case of PYTEST_OPT_FIRMWARE-TODO:
      The firmware has to be compiled.
    If nothing is specified, we do not flash any firmware: Return None
    """
    assert isinstance(config, pytest.Config)

    firmware_git_url = config.getoption(PYTEST_OPT_BUILD_FIRMWARE)
    if firmware_git_url is not None:
        #
        # Collect firmware specs by connected tentacles
        #
        if firmware_git_url == PYTEST_OPT_BUILD_FIRMWARE_MOCK:
            #
            # Mocked firmware speces
            #
            return [
                FirmwareBuildSpec(
                    BoardVariant.factory("RPI_PICO"),
                    micropython_version_text="y",
                    _filename=pathlib.Path("/x/y"),
                ),
                FirmwareBuildSpec(
                    BoardVariant.factory("PYBV11"),
                    micropython_version_text="y",
                    _filename=pathlib.Path("/x/y"),
                ),
                FirmwareBuildSpec(
                    BoardVariant.factory("PYBV11-DP"),
                    micropython_version_text="y",
                    _filename=pathlib.Path("/x/y"),
                ),
            ]

        return collect_firmware_specs(tentacles=tentacles)

    firmware_download_json = config.getoption(PYTEST_OPT_DOWNLOAD_FIRMWARE)
    if firmware_download_json is not None:
        #
        # Donwnload firmware and return the spec
        #
        assert firmware_download_json is not None
        spec = FirmwareDownloadSpec.factory(filename=firmware_download_json)
        spec.download()
        return [spec]

    #
    # Nothing was specified: We do not flash any firmware
    #
    return [FirmwareNoFlashingSpec.factory()]
