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

import re
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path

from mpbuild.board_database import Board, Database
from mpbuild.build import (
    BUILD_CONTAINERS,
    MpbuildNotSupportedException,
    docker_build_cmd,
)
from octoprobe.lib_tentacle_dut import VERSION_IMPLEMENTATION_SEPARATOR

from .board_tweaks import board_specific_download, tweak_build_folder

BOARD_VARIANT_SEPARATOR = "-"

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
        proc: subprocess.CompletedProcess,
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
    filename: Path
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
        return f"{self.board.name}{BOARD_VARIANT_SEPARATOR}{self.variant}"

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
    "samd": "firmware.uf2",
    "stm32": "firmware.dfu",
    "unix": "micropython",
    "nrf": "firmware.bin",
    "mimxrt": "firmware.hex",
}


class BuildFolder:
    """
    This class extracts information from the build folder:
    * the firmware filename
    * the micropython version text (e.g. '3.4.0; MicroPython v1.24.0 on 2024-10-25')
    """

    _REGEX_MICOPY_SYS_VERSION2 = re.compile(r"mp_sys_version_obj.*?sizeof\((\".+?\")\)")
    """
    static const mp_obj_str_t mp_sys_version_obj = {{&mp_type_str}, 0, sizeof("3.4.0; " "MicroPython " "v1.24.1" " on " "2024-12-12") - 1, (const byte *)"3.4.0; " "MicroPython " "v1.24.1" " on " "2024-12-12"};
    static const mp_obj_str_t mp_sys_version_obj = {{&mp_type_str}, 0, sizeof("3.4.0; " "MicroPython " "v1.25.0-preview.147.g136058496" " on " "2024-12-22") - 1, (const byte *)"3.4.0; " "MicroPython " "v1.25.0-preview.147.g136058496" " on " "2024-12-22"};
    """

    _REGEX_MICROPY_MCU_NAME = re.compile(
        r"mp_sys_implementation_machine_obj.*?sizeof\((\".+?\")\)"
    )
    """
    static const mp_obj_str_t mp_sys_implementation_machine_obj = {{&mp_type_str}, 0, sizeof("Raspberry Pi Pico2" " with " "RP2350-RISCV") - 1, (const byte *)"Raspberry Pi Pico2" " with " "RP2350-RISCV"};
    static const mp_obj_str_t mp_sys_implementation_machine_obj = {{&mp_type_str}, 0, sizeof("ESP module (512K)" " with " "ESP8266") - 1, (const byte *)"ESP module (512K)" " with " "ESP8266"};
    """

    _REGEX_MICROPY_BUILD = re.compile(
        r"mp_sys_implementation__build_obj.*?sizeof\((\".+?\")\)"
    )
    """
    static const mp_obj_str_t mp_sys_implementation__build_obj = {{&mp_type_str}, 0, sizeof("PYBV11") - 1, (const byte *)"PYBV11"};
    """

    def __init__(self, board: Board, variant: str | None) -> None:
        self.board = board
        self.variant = variant

        def get_build_folder() -> Path:
            tweak = tweak_build_folder(board=board, variant=variant)
            if tweak:
                return self.board.port.directory / tweak

            if board.physical_board:
                # Example: board_name == 'stm32'
                build_directory = f"build-{self.board.name}"
                if variant is not None:
                    build_directory += f"{BOARD_VARIANT_SEPARATOR}{variant}"
                return self.board.port.directory / build_directory

            # Example: board_name == 'unix'
            build_directory = "build"
            if variant is not None:
                build_directory += f"{BOARD_VARIANT_SEPARATOR}{variant}"
            return self.board.port.directory / build_directory

        self.build_folder = get_build_folder()

        self.filename_qstr_i_last = self.build_folder / "genhdr" / "qstr.i.last"
        try:
            self.file_qstr_i_last = self.filename_qstr_i_last.read_text()
        except FileNotFoundError as e:
            raise MpbuildException(
                f"Firmware for {self.board.name}{BOARD_VARIANT_SEPARATOR}{self.variant}: Could not read: {self.filename_qstr_i_last}"
            ) from e

    @property
    def firmware_filename(self) -> Path:
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
                f"The firmware for {self.board.name}{BOARD_VARIANT_SEPARATOR}{self.variant} was not found: {_filename}"
            )

        return _filename

    @property
    def micropython_sys_version_text(self) -> str:
        """
        As returned from 'sys.version'
        Example: '3.4.0; MicroPython v1.24.0 on 2024-10-25'
        """

        return self.get_regex(self._REGEX_MICOPY_SYS_VERSION2)

    @property
    def micropython_sys_implementation_text(self) -> str:
        """
        As returned from 'sys.implementation'
        Example: 'LOLIN_C3_MINI with ESP32-C3FH4'
        """
        return self.get_regex(self._REGEX_MICROPY_MCU_NAME)

    @property
    def micropython_sys_build_text(self) -> str:
        """
        As returned from 'sys.implementation._build'
        See https://github.com/micropython/micropython/pull/16843.
        Example: 'PYBV11-DP'
        """
        match = self._REGEX_MICROPY_BUILD.search(self.file_qstr_i_last)
        if match is None:
            return ""
        return self.get_regex(self._REGEX_MICROPY_BUILD)

    @property
    def micropython_full_version_text(self) -> str:
        versions = []
        if self.micropython_sys_build_text != "":
            versions.append(self.micropython_sys_build_text)
        versions.append(self.micropython_sys_version_text)
        versions.append(self.micropython_sys_implementation_text)
        return VERSION_IMPLEMENTATION_SEPARATOR.join(versions)

    def get_regex(self, pattern: re.Pattern) -> str:
        match = pattern.search(self.file_qstr_i_last)
        if match is None:
            raise MpbuildException(
                f"Firmware for {self.board.name}{BOARD_VARIANT_SEPARATOR}{self.variant}: Could not find '{pattern.pattern}' in: {self.filename_qstr_i_last}"
            )
        text = match.group(1)
        # Example 'mcu_name': "LOLIN_C3_MINI" " with " "ESP32-C3FH4"
        text = eval(text)  # pylint: disable=eval-used
        # Example 'mcu_name': LOLIN_C3_MINI with ESP32-C3FH4
        return text


def build(
    logfile: Path,
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
        privileged=False,
    )

    with logfile.open("w") as f:
        begin_s = time.monotonic()
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
    logfile: Path, db: Database, variant_normalized: str, do_clean: bool
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

    board_str, variant_str = split_board_variant(variant_normalized)
    # Example variant_str:
    #  "": for the default variant
    #  "THREAD": for variant "THREAD"

    try:
        board = db.boards[board_str]
    except KeyError as e:
        valid_boards = sorted(db.boards.keys())
        raise MpbuildException(
            f"Board '{board_str}' not found. Valid boards are {valid_boards}"
        ) from e

    variant = None if variant_str == "" else variant_str

    return build(
        logfile=logfile, db=db, board=board, variant=variant, do_clean=do_clean
    )


def split_board_variant(board_variant: str) -> tuple[str, str]:
    """
    Example: "RPI_PICO2-RISCV" -> "RPI_PICO2", "RISCV"
    Example: "RPI_PICO2" -> "RPI_PICO", ""
    """
    board_str, _, variant_str = board_variant.partition(BOARD_VARIANT_SEPARATOR)
    return (board_str, variant_str)
