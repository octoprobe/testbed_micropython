"""
This is the api interface for mpbuild


Topic: When may we skip firmware flashing?

Goal:
  * Flash a required firmware, if it has changed
  * Skip flashing if the required firmware is already installed.

Solutions:
  * 'micropython_full_version_text' include the firmware variant!
    Consequence: Firmware change is NOT detected.

Problems:
  * When the firmware source directory is touched, 'micropython_version_text' will contain '...dirty...'.
    Consequence: Firmware change is NOT detected.
"""

from __future__ import annotations

import logging
import pathlib
import re
import subprocess
import time
from dataclasses import dataclass

from mpbuild.board_database import Board, Database
from mpbuild.build import (
    BUILD_CONTAINERS,
    MpbuildNotSupportedException,
    docker_build_cmd,
)
from octoprobe.lib_tentacle_dut import VERSION_IMPLEMENTATION_SEPARATOR
from octoprobe.util_micropython_boards import VARIANT_SEPARATOR

from .board_tweaks import board_specific_download, tweak_build_folder

logger = logging.getLogger(__file__)

# Overwrite mpbuild default containers
# This should eventually be pushed upstream into mpbuild.
# BUILD_CONTAINERS["esp32"] = "hmaerki/build-micropython-esp32"
BUILD_CONTAINERS["dummyarch"] = "dummycontainer"


class MpbuildException(Exception):
    """
    Thrown by the API if the build fails.
    """


class MpbuildDockerException(MpbuildException):
    """
    Thrown by the API if docker fails.
    The exception contains
    * the board and variant that failed
    * proc.returncode
    * proc.stdout
    * proc.stderr

    stdout/stderr might be very long!
    """

    def __init__(
        self,
        board: Board,
        variant: str | None,
        proc: subprocess.CompletedProcess[str],
    ) -> None:
        super().__init__(f"Failed to build {board.name}-{variant}")
        self.proc = proc

    def __str__(self) -> str:
        """
        As the docker build failed, also return the docker output - which may be many lines long!
        """
        lines = (
            super().__str__(),
            f"{self.proc.returncode=}",  # type: ignore[attr-defined]
            f"{self.proc.stdout=}",  # type: ignore[attr-defined]
            f"{self.proc.stderr=}",  # type: ignore[attr-defined]
        )
        return "\n  ".join(lines)


@dataclass(frozen=True, order=True)
class Firmware:
    filename: pathlib.Path
    """
    the compiled firmware
    """

    board: Board
    """
    The board used to build the firmware.

    This is used by octoprobe to find matching MCUs/boards.
    """

    variant: str | None
    """
    None: Default variant
    """

    micropython_full_version_text: str
    """
    Example:
     * PYBV11-DP: 3.4.0; MicroPython v1.24.0-338.g265d1b2ec on 2025-03-04;PYBv1.1 with STM32F405RG

    Example - after https://github.com/micropython/micropython/pull/16843:
     * PYBV11-DP: PYBV11-DP;3.4.0; MicroPython v1.24.0-338.g265d1b2ec on 2025-03-04;PYBv1.1 with STM32F405RG
    """

    def __str__(self) -> str:
        return f"Firmware({self.variant_name_full}, {self.filename}, {self.micropython_full_version_text})"

    @property
    def variant_name_full(self) -> str:
        """
        return <port>-<board>-<variant>
        """
        name = f"{self.board.port.name}-{self.board.name}"
        if self.variant is None:
            return name
        return name + f"{name}-{self.variant}"

    @property
    def variant_normalized(self) -> str:
        """
        return <board>-<variant>
        """
        if self.variant is None:
            return self.board.name
        return f"{self.board.name}{VARIANT_SEPARATOR}{self.variant}"

    @property
    def requires_flashing(self) -> bool:
        """
        If sources files have been touched, 'dirty' is added.
        """
        return "dirty" in self.micropython_full_version_text


_FIRMWARE_FILENAMES = {
    "esp32": "firmware.bin",
    "esp8266": "firmware.bin",
    "rp2": "firmware.uf2",
    "samd": "firmware.bin",  # using programmer=samd_bossac
    # "samd": "firmware.uf2", # using programmer=samd_mount_point
    "stm32": "firmware.dfu",
    "unix": "micropython",
    "nrf": "firmware.bin",
    "mimxrt": "firmware.hex",
}


@dataclass(frozen=True)
class MpVersion:
    git_tag: str
    """
    Example: v1.29.0-preview.515.gff2ed49367
    """

    git_hash: str
    """
    Example: ff2ed49367
    """

    git_build_date: str
    """
    Example: 2026-07-09
    """

    version_language: str
    """
    Example: "3.4.0; "
    """

    sys_implementation_build: str
    """
    As returned from 'sys.implementation._build'
    Example: RPI_PICO2-RISCV
    """

    @property
    def micropython_sys_version(self) -> str:
        """
        As returned from 'sys.version'
        Example: '3.4.0; MicroPython v1.24.0 on 2024-10-25'
        """
        return f"{self.version_language}MicroPython {self.git_tag} on {self.git_build_date}"

    @staticmethod
    def _get_python_language_version(board: Board) -> str:
        filename_modsys_c = board.port.directory_repo / "py" / "modsys.c"
        try:
            file_modsys_c = filename_modsys_c.read_text()
        except FileNotFoundError as e:
            raise MpbuildException(
                f"Firmware for {board.name}: Could not read: {filename_modsys_c}"
            ) from e

        # Example: static const MP_DEFINE_STR_OBJ(mp_sys_version_obj, "3.4.0; " MICROPY_BANNER_NAME_AND_VERSION);
        match = re.search(
            r'MP_DEFINE_STR_OBJ\(mp_sys_version_obj,+\s"(?P<version>.+?)"',
            file_modsys_c,
        )
        if match is None:
            raise MpbuildException(
                f"Firmware for {board.name}: {filename_modsys_c}: Version not found!"
            )
        return match.group("version")

    @classmethod
    def factory(cls, board: Board, build_folder: pathlib.Path) -> MpVersion:
        filename_mpversion_h = build_folder / "genhdr" / "mpversion.h"
        try:
            file_mpversion_h = filename_mpversion_h.read_text()
        except FileNotFoundError as e:
            raise MpbuildException(
                f"Firmware for {board.name}: Could not read: {filename_mpversion_h}"
            ) from e

        # This is 'genhdr/mpversion.h'
        # // This file was generated by py/makeversionhdr.py
        # #define MICROPY_GIT_TAG "v1.29.0-preview.515.gff2ed49367"
        # #define MICROPY_GIT_HASH "ff2ed49367"
        # #define MICROPY_BUILD_DATE "2026-07-09"
        regex_mpversion_h = r'#define\s+(MICROPY[A-Z_]+)\s+"(\S+?)"'

        match = re.findall(regex_mpversion_h, file_mpversion_h)
        assert match is not None

        def lookup(tag: str) -> str:
            for _m in match:
                if tag == _m[0]:
                    return str(_m[1])
            raise MpbuildException(
                f"Firmware for {board.name}: In {filename_mpversion_h}: Tag '{tag}' not found!"
            )

        assert build_folder.name.startswith(BuildFolder.BUILD_FOLDER_PREFIX)

        return MpVersion(
            git_tag=lookup(tag="MICROPY_GIT_TAG"),
            git_hash=lookup(tag="MICROPY_GIT_HASH"),
            git_build_date=lookup(tag="MICROPY_BUILD_DATE"),
            version_language=cls._get_python_language_version(board=board),
            sys_implementation_build=build_folder.name[
                len(BuildFolder.BUILD_FOLDER_PREFIX) :
            ],
        )


class BuildFolder:
    """
    This class extracts information from the build folder:
    * the firmware filename
    * the micropython version text (e.g. '3.4.0; MicroPython v1.24.0 on 2024-10-25')
    """

    BUILD_FOLDER_PREFIX = "build-"
    """
    Example build folder: 'build-RPI_PICO2-RISCV
    """

    def __init__(self, board: Board, variant: str | None) -> None:
        self.board = board
        self.variant = variant

        def get_build_folder() -> pathlib.Path:
            tweak = tweak_build_folder(board=board, variant=variant)
            if tweak:
                return self.board.port.directory / tweak

            if board.physical_board:
                # Example: board_name == 'stm32'
                build_directory = f"{self.BUILD_FOLDER_PREFIX}{self.board.name}"
                if variant is not None:
                    build_directory += f"{VARIANT_SEPARATOR}{variant}"
                return self.board.port.directory / build_directory

            # Example: board_name == 'unix'
            build_directory = "build"
            if variant is not None:
                build_directory += f"{VARIANT_SEPARATOR}{variant}"
            return self.board.port.directory / build_directory

        self.build_folder = get_build_folder()
        self.mp_version = MpVersion.factory(board=board, build_folder=self.build_folder)

    @property
    def firmware_filename(self) -> pathlib.Path:
        """
        Returns the filename of the compiled binary.
        """
        filename = _FIRMWARE_FILENAMES.get(self.board.port.name, None)
        if filename is None:
            raise MpbuildNotSupportedException(
                f"Entry port='{self.board.port.name}' missing in 'FIRMWARE_FILENAMES'!"
            )

        _filename = self.build_folder / filename
        if not _filename.is_file():
            raise MpbuildException(
                f"The firmware for {self.board.name}{VARIANT_SEPARATOR}{self.variant} was not found: {_filename}"
            )

        return _filename

    @property
    def micropython_sys_version(self) -> str:
        """
        As returned from 'sys.version'
        Example: '3.4.0; MicroPython v1.24.0 on 2024-10-25'
        """

        return self.mp_version.micropython_sys_version

    @property
    def micropython_sys_build(self) -> str:
        """
        As returned from 'sys.implementation._build'
        See https://github.com/micropython/micropython/pull/16843.
        Example: 'PYBV11-DP'
        """
        return self.mp_version.sys_implementation_build

    @property
    def micropython_full_version_text(self) -> str:
        """
        Example: RPI_PICO_W;3.4.0; MicroPython v1.28.0 on 2026-07-09;RPI_PICO_W
        """
        versions = []
        versions.append(self.micropython_sys_build)
        versions.append(self.micropython_sys_version)
        versions.append(self.mp_version.sys_implementation_build)
        return VERSION_IMPLEMENTATION_SEPARATOR.join(versions)


def build(
    logfile: pathlib.Path,
    db: Database,
    board: Board,
    variant: str | None = None,
    do_clean: bool = False,
) -> Firmware:
    """
    Build the firmware and write the docker ouput to 'logfile'
    """
    board_specific_download(logfile=logfile, db=db, board=board, variant=variant)

    build_cmd = docker_build_cmd(
        board=board,
        variant=variant,
        do_clean=do_clean,
        extra_args=[],
        docker_interactive=False,
        add_device_flags=False,
    )

    mpbuild_cmd = f"mpbuild build {board.name}"
    if variant is not None:
        mpbuild_cmd += f" {variant}"
    logger.debug("Calling mpbuild:")
    logger.debug(f"  cd {db.mpy_root_directory}")
    logger.debug(f"  {mpbuild_cmd}")

    if True:
        with logfile.open("w") as f:
            begin_s = time.monotonic()
            f.write(f"cd {db.mpy_root_directory}\n")
            f.write(f"{mpbuild_cmd}\n")
            f.write(f"{build_cmd}\n\n\n")
            f.flush()
            proc = subprocess.run(
                build_cmd,
                cwd=db.mpy_root_directory,
                shell=True,
                check=False,
                text=True,
                stdout=f,
                stderr=subprocess.STDOUT,
            )
            f.write(f"\n\nreturncode={proc.returncode}\n")
            f.write(f"duration={time.monotonic() - begin_s:0.3f}s\n")

        if proc.returncode != 0:
            raise MpbuildDockerException(
                board=board,
                variant=variant,
                proc=proc,
            )

    build_folder = BuildFolder(board=board, variant=variant)

    return Firmware(
        filename=build_folder.firmware_filename,
        board=board,
        variant=variant,
        micropython_full_version_text=build_folder.micropython_full_version_text,
    )


def build_by_variant_normalized(
    logfile: pathlib.Path,
    db: Database,
    variant_normalized: str,
    do_clean: bool,
) -> Firmware:
    """
    This is the main entry point into mpbuild.

    'variant_normalized' is taken from the micropython filename convention:
    Examples (filename -> variant_normalized):
        PYBV11-20241129-v1.24.1.dfu  ->  PYBV11
        PYBV11-THREAD-20241129-v1.24.1.dfu  ->  PYBV11-THREAD

    This will build the firmware and return
    * firmware: Firmware: The path to the firmware and much more
    * proc: The output from the docker container. This might be useful for logging purposes.

    If the build fails:
    * an exception is raised
    * captured output with the error message is written to stdout/strerr (it would be better to write it to a logfile)
    """

    board_variant = BoardVariant.parse(variant_normalized)
    # Example variant_str:
    #  "": for the default variant
    #  "THREAD": for variant "THREAD"

    try:
        board = db.boards[board_variant.board]
    except KeyError as e:
        valid_boards = sorted(db.boards.keys())
        raise MpbuildException(
            f"Board '{board_variant.board}' not found. Valid boards are {valid_boards}"
        ) from e

    variant = None if board_variant.variant == "" else board_variant.variant

    return build(
        logfile=logfile,
        db=db,
        board=board,
        variant=variant,
        do_clean=do_clean,
    )


@dataclass(slots=True, frozen=True)
class BoardVariant:
    board_variant: str
    board: str
    """
    Example: "RPI_PICO2-RISCV" -> "RPI_PICO2",
    Example: "RPI_PICO2" -> "RPI_PICO2"
    """
    variant: str
    """
    Example: "RPI_PICO2-RISCV" -> "RISCV",
    Example: "RPI_PICO2" -> ""
    """
    has_variant_separator: bool
    """
    Example: "RPI_PICO2-RISCV" -> True. Indicates only variant 'RISCV' should be tested.
    Example: "RPI_PICO2-" -> True. Indicates only variant '' should be tested.
    Example: "RPI_PICO2" -> False. Indicates all variants should be tested.
    """

    @staticmethod
    def parse(board_variant: str) -> BoardVariant:
        board, separator, variant = board_variant.partition(VARIANT_SEPARATOR)

        return BoardVariant(
            board_variant=board_variant,
            board=board,
            variant=variant,
            has_variant_separator=separator == VARIANT_SEPARATOR,
        )
