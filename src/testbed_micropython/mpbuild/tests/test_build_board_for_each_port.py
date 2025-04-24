"""
Call mpbuild for all boards.
Tests the wlanAP two variants.

Goal is a high test coverage of the boards.
"""

import os
import pathlib

from mpbuild import Database
from mpbuild.build import MpbuildNotSupportedException

from testbed_micropython.mpbuild.build_api import build

THIS_FILE = pathlib.Path(__file__)
RESULTS_DIRECTORY = THIS_FILE.parent / "testresults"
RESULTS_DIRECTORY.mkdir(parents=True, exist_ok=True)


MICROPY_DIR = "MICROPY_DIR"

NUMBER_BOARDS = 1
NUMBER_VARIANTS = 2


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

    for port in db.ports.values():
        for board in list(port.boards.values())[0:NUMBER_BOARDS]:
            variant_names = []
            if board.physical_board:
                variant_names.append(None)  # Default variant
            variant_names.extend(v.name for v in board.variants[0:NUMBER_VARIANTS])
            for variant_name in variant_names:
                print(f"Testing {board.name}-{variant_name}")
                try:
                    logfile = (
                        RESULTS_DIRECTORY
                        / f"{THIS_FILE.stem}-{board.name}-{variant_name}.txt"
                    )
                    firmware = build(
                        logfile=logfile,
                        db=db,
                        board=board,
                        variant=variant_name,
                        do_clean=False,
                    )
                    print(f"  {firmware}")
                except MpbuildNotSupportedException:
                    print("  Not supported!")


if __name__ == "__main__":
    main()
