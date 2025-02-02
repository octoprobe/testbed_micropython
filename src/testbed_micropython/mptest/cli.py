"""
Where to take the tests from
--micropython-tests-giturl=https://github.com/dpgeorge/micropython.git@tests-full-test-runner

Where to take the firmware from
--firmware-build-giturl=https://github.com/micropython/micropython.git@v1.24.1
--firmware-build-gitdir=~/micropython
--firmware-gitdir=~/micropython
"""

from __future__ import annotations

import logging
import pathlib

import typer
import typing_extensions
from mpbuild.board_database import MpbuildMpyDirectoryException
from octoprobe.util_pyudev import UDEV_POLLER_LAZY
from octoprobe.util_tentacle_label import label_renderer

from ..constants import (
    DIRECTORY_DOWNLOADS,
    DIRECTORY_TESTRESULTS_DEFAULT,
    URL_FILENAME_DEFAULT,
)
from ..mptest import util_testrunner
from ..mptest.util_common import ArgsMpTest
from ..multiprocessing import util_multiprocessing
from ..tentacles_inventory import TENTACLES_INVENTORY
from ..testcollection.baseclasses_spec import tentacle_spec_2_tsvs
from ..util_firmware_mpbuild_interface import ArgsFirmware
from .util_testbootmode import do_debugbootmode, get_programmer_labels

logger = logging.getLogger(__file__)

# 'typer' does not work correctly with typing.Annotated
# Required is: typing_extensions.Annotated
TyperAnnotated = typing_extensions.Annotated

# mypy: disable-error-code="valid-type"
# This will disable this warning:
#   op.py:58: error: Variable "octoprobe.scripts.op.TyperAnnotated" is not valid as a type  [valid-type]
#   op.py:58: note: See https://mypy.readthedocs.io/en/stable/common_issues.html#variables-vs-type-aliases

app = typer.Typer(pretty_exceptions_enable=False)


def complete_only_test():
    testrun_specs = util_testrunner.get_testrun_specs()
    return sorted([x.label for x in testrun_specs])


def complete_only_board():
    if False:
        args = util_testrunner.Args.get_default_args()
        testrunner = util_testrunner.TestRunner(args=args)

        connected_tentacles = testrunner.bartender.connected_tentacles
    else:
        connected_tentacles = util_testrunner.query_connected_tentacles_fast()

    return sorted({t.tentacle_spec.board for t in connected_tentacles})

    tsvs = connected_tentacles.get_tsvs()
    return sorted([t.board_variant for t in tsvs])


@app.command(help="Create a pdf with lables for the bolzone_due")
def labels() -> None:
    filename = DIRECTORY_DOWNLOADS / "testbed_labels.pdf"
    label_renderer.create_report(
        filename=filename,
        layout=label_renderer.RendererLabelBolzoneDuo(),
        labels=TENTACLES_INVENTORY.labels_data,
    )
    print(f"Created: {filename}")


@app.command(
    help="Debug entering the boot mode. Used to verify, if a device correctly switches into programming mode."
)
def debugbootmode(
    programmer: TyperAnnotated[
        str,
        typer.Option(
            help=f"One of {get_programmer_labels()}",
        ),
    ],
) -> None:
    do_debugbootmode(programmer=programmer)


@app.command(name="list", help="List tests and connected tentacles")
def list_() -> None:
    # args = util_testrunner.Args.get_default_args()
    # testrunner = util_testrunner.TestRunner(args=args)
    connected_tentacles = util_testrunner.query_connected_tentacles_fast()

    print("")
    print("Connected")
    for tentacle in connected_tentacles:
        print(f"  {tentacle.label}")
        variants = ",".join(
            f"{tsv!r}" for tsv in tentacle_spec_2_tsvs(tentacle.tentacle_spec)
        )
        print(f"    variants={variants}")
        futs = ",".join([fut.name for fut in tentacle.tentacle_spec.futs])
        print(f"    futs={futs}")

    print("")
    print("Tests")
    for testrun_spec in util_testrunner.get_testrun_specs():
        print(f"  {testrun_spec.label}")
        print(f"    help={testrun_spec.helptext}")
        print(f"    executable={testrun_spec.command_executable}")
        print(f"      args={testrun_spec.command_args}")
        print(f"    required_fut={testrun_spec.required_fut.name}")
        print(f"    tests_todo={testrun_spec.tests_todo}")
        print("    tests")
        for tsvs in testrun_spec.roles_tsvs_todo:
            print(f"      {tsvs}")


@app.command(help="Flashes all tentacles without running any tests")
def flash(
    last_variant: TyperAnnotated[
        bool,
        typer.Option(
            help="Build LAST variant if a tentacle supports multiple variants. Not using this option will build the FIRST variant.",
        ),
    ] = False,  # noqa: UP007    force_flash: TyperAnnotated[
    firmware_build: TyperAnnotated[
        str,
        typer.Option(
            envvar="TESTBED_MICROPYTHON_FIRMWARE_BUILD",
            help="Directory of MicroPython-Repo to build the firmware from. Example: ~/micropython or  https://github.com/micropython/micropython.git@v1.24.1",
        ),
    ] = URL_FILENAME_DEFAULT,
    results: TyperAnnotated[
        str,
        typer.Option(
            envvar="TESTBED_MICROPYTHON_RESULTS",
            help="Directory for the testresults",
        ),
    ] = DIRECTORY_TESTRESULTS_DEFAULT,
) -> None:
    args = util_testrunner.Args(
        mp_test=None,
        firmware=ArgsFirmware(
            firmware_build=firmware_build,
            flash_skip=False,
            flash_force=True,
            git_clean=False,
        ),
        directory_results=pathlib.Path(results),
        only_boards=None,
        only_test=None,
        force_multiprocessing=False,
    )

    testrunner = util_testrunner.TestRunner(args=args)
    try:
        testrunner.init()
    except MpbuildMpyDirectoryException as e:
        logger.warning(e)
        return

    args.firmware.flash_force = True
    testrunner.flash(
        udev_poller=UDEV_POLLER_LAZY.udev_poller,
        last_variant=last_variant,
    )
    return


@app.command(help="run tests against the connected tentacles")
def test(
    micropython_tests: TyperAnnotated[
        str,
        typer.Option(
            envvar="TESTBED_MICROPYTHON_MICROPYTHON_TESTS",
            help="Directory of MicroPython-Repo with the tests. Example ~/micropython or https://github.com/micropython/micropython.git@v1.24.1",
        ),
    ] = URL_FILENAME_DEFAULT,
    firmware_build: TyperAnnotated[
        str,
        typer.Option(
            envvar="TESTBED_MICROPYTHON_FIRMWARE_BUILD",
            help="Directory of MicroPython-Repo to build the firmware from. Example: ~/micropython or  https://github.com/micropython/micropython.git@v1.24.1",
        ),
    ] = URL_FILENAME_DEFAULT,
    results: TyperAnnotated[
        str,
        typer.Option(
            envvar="TESTBED_MICROPYTHON_RESULTS",
            help="Directory for the testresults",
        ),
    ] = DIRECTORY_TESTRESULTS_DEFAULT,
    only_board: TyperAnnotated[
        str | None,
        typer.Option(
            help="Only run these on this tentacle.",
            autocompletion=complete_only_board,
        ),
    ] = None,  # noqa: UNoneP007
    only_test: TyperAnnotated[
        str | None,
        typer.Option(help="Only run this test.", autocompletion=complete_only_test),
    ] = None,  # noqa: UP007
    flash_force: TyperAnnotated[
        bool | None,
        typer.Option(help="Will flash all firmware and run tests."),
    ] = False,  # noqa: UP007
    multiprocessing: TyperAnnotated[
        bool,
        typer.Option(
            help="Use python module 'multiprocessing'. This allows parallel processing. Disable to ease debugging.",
        ),
    ] = True,  # noqa: UP007
    git_clean: TyperAnnotated[
        bool,
        typer.Option(
            help="Do a 'git clean -fXd' to make sure that all prior artifacts are removed. Applies ONLY to the firmware repo!",
        ),
    ] = False,  # noqa: UP007
    force_multiprocessing: TyperAnnotated[
        bool,
        typer.Option(
            help="Run tests in sequence. However forces use of python module 'multiprocessing'.",
        ),
    ] = False,  # noqa: UP007
    flash_skip: TyperAnnotated[
        bool | None,
        typer.Option(help="Will not flash and use the firmware already on the boards"),
    ] = False,  # noqa: UP007
) -> None:
    try:
        only_boards = None if only_board is None else [only_board]

        args = util_testrunner.Args(
            mp_test=ArgsMpTest(
                micropython_tests=micropython_tests,
            ),
            firmware=ArgsFirmware(
                firmware_build=firmware_build,
                flash_skip=flash_skip,
                flash_force=flash_force,
                git_clean=git_clean,
            ),
            directory_results=pathlib.Path(results),
            only_boards=only_boards,
            only_test=only_test,
            force_multiprocessing=force_multiprocessing,
        )
        testrunner = util_testrunner.TestRunner(args=args)
        logger.info(f"{multiprocessing=}")
        logger.info(f"directory_results={args.directory_results}")
        try:
            testrunner.init()
        except MpbuildMpyDirectoryException as e:
            logger.warning(e)
            return

        initfunc = (
            util_multiprocessing.init_logging
            if multiprocessing
            else util_multiprocessing.init_empty
        )
        with util_multiprocessing.TargetCtx(
            multiprocessing=multiprocessing,
            initfunc=initfunc,
        ) as target_ctx:
            testrunner.run_all_in_sequence(target_ctx=target_ctx)
    except util_testrunner.OctoprobeAppExitException as e:
        logger.info(f"Terminating test due to OctoprobeAppExitException: {e}")
        raise typer.Exit(1) from e


if __name__ == "__main__":
    app()
