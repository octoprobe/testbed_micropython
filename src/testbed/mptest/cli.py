"""
Where to take the tests from
--micropython-tests-giturl=https://github.com/dpgeorge/micropython.git@tests-full-test-runner

Where to take the firmware from
--firmware-build-giturl=https://github.com/micropython/micropython.git@v1.24.1
--firmware-build-gitdir=~/micropython
--firmware-gitdir=~/micropython
"""

from __future__ import annotations

import typer
import typing_extensions

from testbed.mptest.util_common import ArgsMpTest
from testbed.mptest.util_testrunner import Args, TestRunner
from testbed.testcollection.baseclasses_spec import (
    tentacle_spec_2_tsvs,
)
from testbed.util_firmware_mpbuild_interface import ArgsFirmware

# 'typer' does not work correctly with typing.Annotated
# Required is: typing_extensions.Annotated
TyperAnnotated = typing_extensions.Annotated

# mypy: disable-error-code="valid-type"
# This will disable this warning:
#   op.py:58: error: Variable "octoprobe.scripts.op.TyperAnnotated" is not valid as a type  [valid-type]
#   op.py:58: note: See https://mypy.readthedocs.io/en/stable/common_issues.html#variables-vs-type-aliases

app = typer.Typer()


@app.command(name="list", help="List tests and connected tentacles")
def list_() -> None:
    args = Args(
        mp_test=ArgsMpTest(
            micropython_tests_git=None,
            micropython_tests=None,
        ),
        firmware=ArgsFirmware(
            firmware_build_git=None,
            firmware_build=None,
        ),
        only_boards=[],
    )
    testrunner = TestRunner(args=args)

    print("")
    print("Connected")
    for tentacle in testrunner.bartender.connected_tentacles:
        print(f"  {tentacle.label}")
        variants = ",".join(
            f"{tsv!r}" for tsv in tentacle_spec_2_tsvs(tentacle.tentacle_spec)
        )
        print(f"    variants={variants}")
        futs = ",".join([fut.name for fut in tentacle.tentacle_spec.futs])
        print(f"    futs={futs}")

    print("")
    print("Tests")
    for testrun_spec in testrunner.bartender.testrun_specs:
        print(f"  {testrun_spec.label}")
        print(f"    reqired_fut={testrun_spec.required_fut.name}")
        print(f"    tests_todo={testrun_spec.tests_todo}")
        print(f"    executable={testrun_spec.command_executable}")
        print(f"      args={testrun_spec.command_args}")
        print("    tests")
        for tsvs in testrun_spec.list_tsvs_todo:
            print(f"      {tsvs}")


@app.command(help="Will flash all firmare when running the tests next time")
def force_build_firmware() -> None:
    pass


@app.command(help="run tests against the connected tentacles")
def test(
    micropython_tests_git: TyperAnnotated[
        str | None,
        typer.Option(
            envvar="TESTBED_MICROPYTHON_MICROPYTHON_TESTS_GIT",
            help="Url to a MicroPython-Repo with the tests. Example: https://github.com/micropython/micropython.git@v1.24.1",
        ),
    ] = None,
    micropython_tests: TyperAnnotated[
        str | None,
        typer.Option(
            envvar="TESTBED_MICROPYTHON_MICROPYTHON_TESTS",
            help="Directory of MicroPython-Repo with the tests. Example ~/micropython",
        ),
    ] = None,
    firmware_build_git: TyperAnnotated[
        str | None,
        typer.Option(
            envvar="TESTBED_MICROPYTHON_FIRMWARE_BUILD_GIT",
            help="Url to a MicroPython-Repo to be cloned and build. Example: https://github.com/micropython/micropython.git@v1.24.1",
        ),
    ] = None,
    firmware_build: TyperAnnotated[
        str | None,
        typer.Option(
            envvar="TESTBED_MICROPYTHON_FIRMWARE_BUILD",
            help="Directory of MicroPython-Repo to build the firmware from. Example: ~/micropython",
        ),
    ] = None,
    only_boards: TyperAnnotated[
        list[str] | None, typer.Argument(help="Only run these tests")
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
    testrunner = TestRunner(args=args)
    testrunner.run_all_in_sequence()


if __name__ == "__main__":
    app()
