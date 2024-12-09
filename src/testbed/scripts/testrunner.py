"""
Where to take the tests from
--micropython-tests-giturl=https://github.com/dpgeorge/micropython.git@tests-full-test-runner

Where to take the firmware from
--firmware-build-giturl=https://github.com/micropython/micropython.git@v1.24.1
--firmware-build-gitdir=~/micropython
--firmware-gitdir=~/micropython
"""

from __future__ import annotations

from typing import Optional

import typer
import typing_extensions

from testbed.testrunner.util_testrunner import Args, run_tests
from testbed.testrunner.utils_common import ArgsMpTest
from testbed.util_firmware_mpbuild_interface import ArgsFirmware

# 'typer' does not work correctly with typing.Annotated
# Required is: typing_extensions.Annotated
TyperAnnotated = typing_extensions.Annotated

# mypy: disable-error-code="valid-type"
# This will disable this warning:
#   op.py:58: error: Variable "octoprobe.scripts.op.TyperAnnotated" is not valid as a type  [valid-type]
#   op.py:58: note: See https://mypy.readthedocs.io/en/stable/common_issues.html#variables-vs-type-aliases

app = typer.Typer()


@app.command()
def run(
    micropython_tests_git: TyperAnnotated[
        Optional[str],
        typer.Option(
            envvar="TESTBED_MICROPYTHON_MICROPYTHON_TESTS_GIT",
            help="Url to a MicroPython-Repo with the tests. Example: https://github.com/micropython/micropython.git@v1.24.1",
        ),
    ] = None,
    micropython_tests: TyperAnnotated[
        Optional[str],
        typer.Option(
            envvar="TESTBED_MICROPYTHON_MICROPYTHON_TESTS",
            help="Directory of MicroPython-Repo with the tests. Example ~/micropython",
        ),
    ] = None,
    firmware_build_git: TyperAnnotated[
        Optional[str],
        typer.Option(
            envvar="TESTBED_MICROPYTHON_FIRMWARE_BUILD_GIT",
            help="Url to a MicroPython-Repo to be cloned and build. Example: https://github.com/micropython/micropython.git@v1.24.1",
        ),
    ] = None,
    firmware_build: TyperAnnotated[
        Optional[str],
        typer.Option(
            envvar="TESTBED_MICROPYTHON_FIRMWARE_BUILD",
            help="Directory of MicroPython-Repo to build the firmware from. Example: ~/micropython",
        ),
    ] = None,
    only_boards: TyperAnnotated[
        Optional[list[str]], typer.Argument(help="Only run these tests")
    ] = None,  # noqa: UP007
) -> None:
    # print(f"{micropython_tests_git=}")
    # print(f"{micropython_tests=}")
    # print(f"{firmware_build_git=}")
    # print(f"{firmware_build=}")
    # print(f"{only_boards=}")

    args = Args(
        mp_test=ArgsMpTest(
            micropython_tests_git=micropython_tests_git,
            micropython_tests=micropython_tests,
        ),
        firmware=ArgsFirmware(
            firmware_build_git=firmware_build_git,
            firmware_build=firmware_build,
        ),
        only_boards=only_boards,
    )
    run_tests(args=args)


if __name__ == "__main__":
    app()
