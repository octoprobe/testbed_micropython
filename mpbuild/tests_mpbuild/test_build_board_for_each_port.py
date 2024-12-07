"""
Call mpbuild for all boards.
Tests the first two variants.

Goal is a high test coverage of the boards.
"""

import pathlib

from mpbuild.build import MpbuildNotSupportedException
from mpbuild.build_api import build
from test_build_some_variants import RESULTS_DIRECTORY, get_db

THIS_FILE = pathlib.Path(__file__)

NUMBER_BOARDS = 1
NUMBER_VARIANTS = 2


def main():
    db = get_db()

    for port in db.ports.values():
        for board in list(port.boards.values())[0:NUMBER_BOARDS]:
            variant_names = []
            if board.physical_board:
                variant_names.append(None)  # Default variant
            variant_names.extend(v.name for v in board.variants[0:NUMBER_VARIANTS])
            for variant_name in variant_names:
                if board.name == "ESP32_GENERIC_S3":
                    print("Skipping ESP32_GENERIC_S3 as build fails on 1.24.1")
                    continue
                print(f"Testing {board.name}-{variant_name}")
                try:
                    logfile = (
                        RESULTS_DIRECTORY
                        / f"{THIS_FILE.stem}-{board.name}-{variant_name}.txt"
                    )
                    firmware = build(
                        logfile=logfile,
                        board=board,
                        variant=variant_name,
                        do_clean=False,
                    )
                    print(f"  {firmware}")
                except MpbuildNotSupportedException:
                    print("  Not supported!")


if __name__ == "__main__":
    main()
