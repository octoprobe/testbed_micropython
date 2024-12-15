from __future__ import annotations

import dataclasses
import pathlib
import typing

from octoprobe.util_dut_programmers import MICROPYTHON_FULL_VERSION_TEXT_FORCE

from testbed.util_firmware_mpbuild import BoardVariant, FirmwareBuildSpec

if typing.TYPE_CHECKING:
    from testbed.constants import Tentacle
    from testbed.util_firmware_mpbuild import FirmwareBuilder, FirmwareSpecBase


@dataclasses.dataclass(repr=True)
class ArgsFirmware:
    firmware_build: str
    flash_skip: bool
    flash_force: bool
    _builder: FirmwareBuilder | None = None

    def setup(self) -> None:
        """
        This will clone the micropython git repo for the firmware to be build.
        Or verify, if the micropython repo exists.
        """
        from testbed.util_firmware_mpbuild import FirmwareBuilder

        if self.flash_skip:
            return

        self._builder = FirmwareBuilder(firmware_git=self.firmware_build)

    def get_firmware_spec(self, tentacle: Tentacle, variant: str) -> FirmwareSpecBase:
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
        assert isinstance(variant, str)

        if self.flash_skip:
            #
            # Nothing was specified: We do not flash any firmware
            #
            from testbed.util_firmware_specs import FirmwareNoFlashingSpec

            return FirmwareNoFlashingSpec.factory()

        #
        # Collect firmware specs by connected tentacles
        #
        return FirmwareBuildSpec(
            board_variant=BoardVariant(
                board=tentacle.tentacle_spec.tentacle_tag,
                variant=variant,
            )
        )

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
                    firmware_spec=tentacle.dut.firmware_spec,
                    testresults_mpbuild=testresults_mpbuild,
                )
                # After building, the spec is more detailed: Reassign it!
                if self.flash_force:
                    spec = dataclasses.replace(
                        spec,
                        micropython_full_version_text=MICROPYTHON_FULL_VERSION_TEXT_FORCE,
                    )
                tentacle.dut.firmware_spec = spec
