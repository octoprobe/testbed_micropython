import pathlib

from mpbuild.board_database import Board, Database
from octoprobe.util_subprocess import subprocess_run


def board_specific_download(
    logfile: pathlib.Path,
    db: Database,
    board: Board,
    variant: str | None = None,
) -> None:
    if board.name == "ARDUINO_NANO_33_BLE_SENSE":
        # mpbuild build ARDUINO_NANO_33_BLE_SENSE``` fails with `The build target requires a Bluetooth LE stack.`.

        # * The micropython github ci pipeline installs the driver

        # See: https://github.com/micropython/micropython/blob/master/tools/ci.sh
        # See: https://github.com/micropython/micropython/blob/master/ports/nrf/drivers/bluetooth/download_ble_stack.sh

        # ```bash
        # function ci_nrf_build {
        #     ports/nrf/drivers/bluetooth/download_ble_stack.sh s140_nrf52_6_1_1
        #     ...
        # ```
        subprocess_run(
            args=[
                "ports/nrf/drivers/bluetooth/download_ble_stack.sh",
                "s140_nrf52_6_1_1",
            ],
            cwd=db.mpy_root_directory,
            logfile=logfile.with_stem(f"{logfile.stem}_board_specific"),
            timeout_s=10.0,
        )


def tweak_build_folder(
    board: Board,
    variant: str | None = None,
) -> str | None:
    if board.name == "ARDUINO_NANO_33_BLE_SENSE":
        return "build-ARDUINO_NANO_33_BLE_SENSE-s140"
    return None
