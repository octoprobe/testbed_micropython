from __future__ import annotations

import dataclasses
import pathlib
import typing

from octoprobe.lib_tentacle import TentacleBase
from octoprobe.util_firmware_spec import (
    FirmwareDownloadSpec,
    MICROPYTHON_FULL_VERSION_TEXT_FORCE,
)

if typing.TYPE_CHECKING:
    from .util_firmware_mpbuild import FirmwareBuilderBase


class ArgsFirmware:
    def __init__(
        self,
        firmware_build: str,
        flash_skip: bool,
        flash_force: bool,
        git_clean: bool,
        directory_git_cache: pathlib.Path,
    ) -> None:
        assert isinstance(firmware_build, str | None)
        assert isinstance(flash_skip, bool)
        assert isinstance(flash_force, bool)
        assert isinstance(git_clean, bool)
        assert isinstance(directory_git_cache, pathlib.Path)
        self.firmware_build = firmware_build
        if self.firmware_build is None:
            flash_skip = True
        self.flash_skip = flash_skip
        self.flash_force = flash_force
        self.git_clean = git_clean
        self.directory_git_cache = directory_git_cache
        self._builder: FirmwareBuilderBase | None = None

    def setup(self) -> None:
        """
        This will clone the micropython git repo for the firmware to be build.
        Or verify, if the micropython repo exists.
        """
        from .util_firmware_mpbuild import (
            FirmwareBuilder,
            FirmwareBuilderSkipFlash,
        )

        if self.flash_skip:
            self._builder = FirmwareBuilderSkipFlash()
            return

        if FirmwareDownloadSpec.is_download(self.firmware_build):
            return

        self._builder = FirmwareBuilder(
            firmware_git=self.firmware_build,
            directory_git_cache=self.directory_git_cache,
            git_clean=self.git_clean,
        )

    @property
    def repo_micropython_firmware(self) -> pathlib.Path:
        assert self._builder is not None
        return self._builder.repo_directory

    @property
    def ref_firmware(self) -> str:
        if self.flash_skip:
            return "unknown due to flash_skip"
        if self.firmware_build is None:
            return "???"
        return self.firmware_build

    def build_firmware(
        self,
        tentacle: TentacleBase,
        mpbuild_artifacts: pathlib.Path,
    ) -> None:
        """
        Build the firmware and update 'tentacle.tentacle_state.firmware_spec'.
        """
        if self.flash_skip:
            return

        if tentacle.is_mcu:
            if FirmwareDownloadSpec.is_download(self.firmware_build):
                tentacle.tentacle_state.firmware_spec = FirmwareDownloadSpec.factory(
                    self.firmware_build
                )
                return

            assert self._builder is not None
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
