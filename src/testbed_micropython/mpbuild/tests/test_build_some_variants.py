"""
Call mpbuild for some selected boards and variants.

Goal is a high test coverage.
"""

import os
import pathlib

from mpbuild.board_database import Database

from ...mpbuild.build_api import build_by_variant_normalized

THIS_FILE = pathlib.Path(__file__)
RESULTS_DIRECTORY = THIS_FILE.parent / "testresults"
RESULTS_DIRECTORY.mkdir(parents=True, exist_ok=True)

MICROPY_DIR = "MICROPY_DIR"

_VARIANTS_TO_TEST = (
    # Standard case
    "RPI_PICO2",
    # Special case: Variant uses another build container
    "RPI_PICO2-RISCV",
    # Standard case
    "PYBV11",
    "ESP8266_GENERIC",
    "ESP8266_GENERIC-FLASH_512K",
    # "ESP32_GENERIC_S3" # Build fails on 1.24.1
    # Special case: Variant
    "PYBV11-THREAD",
    # Special case: Unix
    "unix-minimal",
    "unix-coverage",
)


def get_db() -> Database:
    try:
        mpy_root_directory = pathlib.Path(os.environ[MICROPY_DIR])
        return Database(mpy_root_directory=mpy_root_directory)
    except KeyError as e:
        raise SystemExit(
            f"The environment variable '{MICROPY_DIR}' is not defined!"
        ) from e


def main():
    db = get_db()

    for variant_normalized in _VARIANTS_TO_TEST:
        print(f"Testing {variant_normalized}")
        logfile = RESULTS_DIRECTORY / f"{THIS_FILE.stem}-{variant_normalized}.txt"
        firmware = build_by_variant_normalized(
            logfile=logfile,
            db=db,
            variant_normalized=variant_normalized,
            do_clean=False,
        )
        print(f"  {firmware}")


if __name__ == "__main__":
    main()
