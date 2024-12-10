from __future__ import annotations

import dataclasses
import pathlib
import typing

from testbed.util_firmware_mpbuild import collect_firmware_specs

if typing.TYPE_CHECKING:
    from testbed.constants import Tentacle
    from testbed.util_firmware_mpbuild import FirmwareBuilder, FirmwareSpecBase


@dataclasses.dataclass(repr=True)
class ArgsFirmware:
    firmware_build_git: str | None
    firmware_build: str | None
    _builder: FirmwareBuilder | None = None

    def setup(self) -> None:
        """
        This will clone the micropython git repo for the firmware to be build.
        Or verify, if the micropython repo exists.
        """
        from testbed.util_firmware_mpbuild import FirmwareBuilder

        if self.firmware_build_git:
            self._builder = FirmwareBuilder(firmware_git_url=self.firmware_build_git)

    def get_firmware_spec(self, tentacle: Tentacle) -> FirmwareSpecBase:
        """
        Given: arguments to pytest, for example PYTEST_OPT_FIRMWARE.
        Now we create firmware specs.
        In case of PYTEST_OPT_FIRMWARE:
        The firmware has to be downloaded.
        In case of PYTEST_OPT_FIRMWARE-TODO:
        The firmware has to be compiled.
        If nothing is specified, we do not flash any firmware: Return None
        """
        assert tentacle.__class__.__name__ == "Tentacle"

        if self.firmware_build_git is not None:
            #
            # Collect firmware specs by connected tentacles
            #
            specs = collect_firmware_specs(tentacles=[tentacle])
            return specs[0]

        firmware_download_json = config.getoption(PYTEST_OPT_DOWNLOAD_FIRMWARE)
        if firmware_download_json is not None:
            #
            # Donwnload firmware and return the spec
            #
            from testbed.util_firmware_specs import FirmwareDownloadSpec

            assert firmware_download_json is not None
            spec = FirmwareDownloadSpec.factory(filename=firmware_download_json)
            spec.download()
            return spec

        #
        # Nothing was specified: We do not flash any firmware
        #
        from testbed.util_firmware_specs import FirmwareNoFlashingSpec

        return FirmwareNoFlashingSpec.factory()

    def build_firmwares(
        self,
        active_tentacles: list[Tentacle],
        testresults_mpbuild: pathlib.Path,
    ) -> None:
        """
        Build the firmwares
        """
        if self._builder is None:
            return

        for tentacle in active_tentacles:
            if tentacle.is_mcu:
                spec = self._builder.build(
                    firmware_spec=tentacle.firmware_spec,
                    testresults_mpbuild=testresults_mpbuild,
                )
                # After building, the spec is more detailed: Reassign it!
                tentacle.firmware_spec = spec
