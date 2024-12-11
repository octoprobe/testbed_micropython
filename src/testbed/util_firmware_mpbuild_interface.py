from __future__ import annotations

import dataclasses
import pathlib
import typing

from octoprobe.util_firmware_spec import MICROPYTHON_FULL_VERSION_TEXT_FORCE

if typing.TYPE_CHECKING:
    from testbed.constants import TentacleBase
    from testbed.util_firmware_mpbuild import (
        FirmwareBuilderBase,
    )


class ArgsFirmware:
    def __init__(
        self,
        firmware_build: str,
        flash_skip: bool,
        flash_force: bool,
        git_clean: bool,
    ) -> None:
        assert isinstance(firmware_build, str)
        assert isinstance(flash_skip, bool)
        assert isinstance(flash_force, bool)
        assert isinstance(git_clean, bool)
        self.firmware_build = firmware_build
        self.flash_skip = flash_skip
        self.flash_force = flash_force
        self.git_clean = git_clean
        self._builder: FirmwareBuilderBase

    def setup(self) -> None:
        """
        This will clone the micropython git repo for the firmware to be build.
        Or verify, if the micropython repo exists.
        """
        from testbed.util_firmware_mpbuild import (
            FirmwareBuilder,
            FirmwareBuilderSkipFlash,
        )

        if self.flash_skip:
            self._builder = FirmwareBuilderSkipFlash()
        else:
            self._builder = FirmwareBuilder(
                firmware_git=self.firmware_build, git_clean=self.git_clean
            )

    @property
    def repo_micropython_firmware(self) -> pathlib.Path:
        return self._builder.repo_directory

    def build_firmware(
        self,
        tentacle: TentacleBase,
        mpbuild_artifacts: pathlib.Path,
    ) -> None:
        """
        Build the firmware and update 'tentacle.tentacle_state.firmware_spec'.
        """
        if tentacle.is_mcu:
            spec = self._builder.build(
                firmware_spec=tentacle.tentacle_state.firmware_spec,
                mpbuild_artifacts=mpbuild_artifacts,
            )
            # After building, the spec is more detailed: Reassign it!
            if self.flash_force:
                spec = dataclasses.replace(
                    spec,
                    micropython_full_version_text=MICROPYTHON_FULL_VERSION_TEXT_FORCE,
                )
            tentacle.tentacle_state.firmware_spec = spec
