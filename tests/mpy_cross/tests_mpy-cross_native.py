import pathlib
import subprocess

DEBUG_OUTPUT = False

FILENAME_TEST_SOURCE = pathlib.Path(
    "~/gits/micropython/tests/basics/0prelim.py"
).expanduser()
assert FILENAME_TEST_SOURCE.is_file()

DIRECTORY_REPORTS_MPBUILD = pathlib.Path(
    "~/work_octoprobe/testbed_micropython_reports/reports/github_selfhosted_testrun_69/mpbuild"
).expanduser()
assert DIRECTORY_REPORTS_MPBUILD.is_dir()

MARCHS = [
    "x86",
    "x64",
    "armv6",
    "armv6m",
    "armv7m",
    "armv7em",
    "armv7emsp",
    "armv7emdp",
    "xtensa",
    "xtensawin",
    "rv32imc",
]


def main() -> None:
    for march in MARCHS:
        print(march)
        for mpy_cross in DIRECTORY_REPORTS_MPBUILD.glob("**/mpy-cross"):
            if DEBUG_OUTPUT:
                print(mpy_cross)
            assert mpy_cross.is_file()

            args = f"{mpy_cross}  -o - -march={march} -X emit=native {FILENAME_TEST_SOURCE} | md5sum --binary"
            if DEBUG_OUTPUT:
                print(f"  {args}")
            output = subprocess.check_output(args=args, shell=True, text=True)
            output = output.replace("*-", "").strip()
            print(f"  {output} {mpy_cross.parent.name}")

        print("---")


if __name__ == "__main__":
    main()
