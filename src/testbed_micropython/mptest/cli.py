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
import sys

import typer
import typing_extensions
from mpbuild.board_database import MpbuildMpyDirectoryException
from octoprobe import util_baseclasses
from octoprobe.scripts.commissioning import init_logging
from octoprobe.util_constants import DIRECTORY_OCTOPROBE_DOWNLOADS, ExitCode
from octoprobe.util_pyudev import UDEV_POLLER_LAZY
from octoprobe.util_tentacle_label import label_renderer

from testbed_micropython.constants import DIRECTORY_TESTRESULTS_DEFAULT, EnumFut
from testbed_micropython.report_test.renderer import ReportRenderer
from testbed_micropython.report_test.util_push_testresults import TarAndHttpsPush

from .. import constants, util_multiprocessing
from ..mptest import util_testrunner
from ..mptest.util_common import ArgsMpTest
from ..tentacles_inventory import TENTACLES_INVENTORY
from ..util_firmware_mpbuild_interface import ArgsFirmware
from .util_baseclasses import ArgsQuery
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


def complete_only_test() -> list[str]:
    testrun_specs = util_testrunner.get_testrun_specs()
    return sorted([x.label for x in testrun_specs])


def complete_only_fut() -> list[str]:
    return sorted([fut.name for fut in EnumFut])


def complete_only_board() -> list[str]:
    if False:
        args = util_testrunner.Args.get_default_args(
            pathlib.Path.cwd(), pathlib.Path.cwd()
        )
        testrunner = util_testrunner.TestRunner(args=args)

        connected_tentacles = testrunner.bartender.connected_tentacles
    else:
        connected_tentacles = util_testrunner.query_connected_tentacles_fast()

    return sorted({t.tentacle_spec.board for t in connected_tentacles})

    tsvs = connected_tentacles.get_tsvs()
    return sorted([t.board_variant for t in tsvs])


def assert_valid_testresults(testresults: str) -> pathlib.Path:
    assert isinstance(testresults, str)

    _testresults = pathlib.Path(testresults).resolve()
    if not _testresults.is_dir():
        print(f"Directory does not exist: {_testresults}")
        typer.Exit(1)  # pylint: disable=pointless-exception-statement
    return _testresults


@app.command(help="Create a pdf with lables for the bolzone_due")
def labels() -> None:
    filename = DIRECTORY_OCTOPROBE_DOWNLOADS / "testbed_labels.pdf"
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


@app.command(help="List supportet tests")
def list_tests() -> None:
    # args = util_testrunner.Args.get_default_args()
    # testrunner = util_testrunner.TestRunner(args=args)
    init_logging()
    for testrun_spec in util_testrunner.get_testrun_specs():
        print(f"  {testrun_spec.label}")
        print(f"    help={testrun_spec.helptext}")
        print(f"    executable={testrun_spec.command_executable}")
        print(f"      args={testrun_spec.command_args}")
        print(f"    required_fut={testrun_spec.required_fut.name}")
        print(f"    tests_todo={testrun_spec.tests_todo}")
        print("    tests")
        for tsv in testrun_spec.tsvs_todo:
            print(f"      {tsv}")


@app.command(help="List connected tentacles")
def list_tentacles() -> None:
    # args = util_testrunner.Args.get_default_args()
    # testrunner = util_testrunner.TestRunner(args=args)
    init_logging()
    try:
        connected_tentacles = util_testrunner.query_connected_tentacles_fast()
    except Exception as e:
        logger.error(f"Terminating test due to: {e!r}")
        raise typer.Exit(1) from e

    print("")
    print("Connected")
    for tentacle in connected_tentacles:
        print(f"  {tentacle.label}")
        print(
            f"      infra: {tentacle.infra.usb_location_infra} {tentacle.infra.usb_tentacle.pico_infra.serial_port}"
        )
        print(
            f"      dut:   {tentacle.infra.usb_location_dut} {tentacle.infra.usb_tentacle.usb_port_dut.device_text}"
        )

        variants = ",".join(tentacle.tentacle_spec.board_build_variants)
        print(f"    variants={variants}")
        futs = ",".join([fut.name for fut in tentacle.tentacle_spec.futs])
        print(f"    futs={futs}")


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
    ] = constants.URL_FILENAME_DEFAULT,
    testresults: TyperAnnotated[
        str,
        typer.Option(
            envvar="TESTBED_MICROPYTHON_TESTRESULTS",
            help="Directory for the testresults",
        ),
    ] = constants.DIRECTORY_TESTRESULTS_DEFAULT,
) -> None:
    directory_results = assert_valid_testresults(testresults)
    args = util_testrunner.Args(
        mp_test=None,
        firmware=ArgsFirmware(
            firmware_build=firmware_build,
            flash_skip=False,
            flash_force=True,
            git_clean=False,
            directory_git_cache=constants.DIRECTORY_GIT_CACHE,
        ),
        directory_results=directory_results,
        query_board=ArgsQuery(),
        query_test=ArgsQuery(),
        force_multiprocessing=False,
        debug_skip_tests=False,
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
    ] = constants.URL_FILENAME_DEFAULT,
    firmware_build: TyperAnnotated[
        str,
        typer.Option(
            envvar="TESTBED_MICROPYTHON_FIRMWARE_BUILD",
            help="Directory of MicroPython-Repo to build the firmware from. Example: ~/micropython or  https://github.com/micropython/micropython.git@v1.24.1",
        ),
    ] = constants.URL_FILENAME_DEFAULT,
    testresults: TyperAnnotated[
        str,
        typer.Option(
            envvar="TESTBED_MICROPYTHON_TESTRESULTS",
            help="Directory for the testresults",
        ),
    ] = constants.DIRECTORY_TESTRESULTS_DEFAULT,
    only_board: TyperAnnotated[
        list[str],
        typer.Option(
            help="Run tests only on this board (tentacles). Examples: 'RPI-PICO2-RISCV' will only test variant 'RISCV'. 'RPI_PICO2-' will only test variant ''. 'RPI_PICO2' will test all variants.",
            autocompletion=complete_only_board,
        ),
    ] = None,  # noqa: UP007
    skip_board: TyperAnnotated[
        list[str],
        typer.Option(
            help="Skip tests on this board (tentacles).",
            autocompletion=complete_only_board,
        ),
    ] = None,  # noqa: UP007
    reference_board: TyperAnnotated[
        str | None,
        typer.Option(
            help=f"The board to be used as WLAN/bluetooth reference. Any board is used as reference if this parameter is set to '{constants.ANY_REFERENCE_BOARD}'.",
            autocompletion=complete_only_board,
        ),
    ] = constants.DEFAULT_REFERENCE_BOARD,  # noqa: UP007
    only_test: TyperAnnotated[
        list[str],
        typer.Option(help="Run this test only.", autocompletion=complete_only_test),
    ] = None,  # noqa: UP007
    skip_test: TyperAnnotated[
        list[str],
        typer.Option(help="Skip this test.", autocompletion=complete_only_test),
    ] = None,  # noqa: UP007
    only_fut: TyperAnnotated[
        list[str],
        typer.Option(
            help="Run this FUT (feature under test).", autocompletion=complete_only_fut
        ),
    ] = None,  # noqa: UP007
    skip_fut: TyperAnnotated[
        list[str],
        typer.Option(
            help="Skip this FUT (feature under test).", autocompletion=complete_only_fut
        ),
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
    ] = True,  # noqa: UP007
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
    count: TyperAnnotated[
        int | None,
        typer.Option(help="Run every test multiple times to detect flakiness"),
    ] = 1,  # noqa: UP007
    debug_skip_tests: TyperAnnotated[
        bool | None,
        typer.Option(help="Skip the test execution"),
    ] = False,  # noqa: UP007
    debug_skip_usb_error: TyperAnnotated[
        bool | None,
        typer.Option(
            help="The tests aborts if an error appears in journalctl. Setting this option will just print a warning but the test will continue."
        ),
    ] = False,  # noqa: UP007
) -> None:
    try:
        directory_results = assert_valid_testresults(testresults)
        args = util_testrunner.Args(
            mp_test=ArgsMpTest(
                micropython_tests=micropython_tests,
            ),
            firmware=ArgsFirmware(
                firmware_build=firmware_build,
                flash_skip=flash_skip,
                flash_force=flash_force,
                git_clean=git_clean,
                directory_git_cache=constants.DIRECTORY_GIT_CACHE,
            ),
            directory_results=directory_results,
            query_test=ArgsQuery.factory(
                only_test=only_test,
                skip_test=skip_test,
                only_fut=only_fut,
                skip_fut=skip_fut,
                arg="tests",
                count=count,
            ),
            query_board=ArgsQuery.factory(
                only_test=only_board,
                skip_test=skip_board,
                only_fut=only_fut,
                skip_fut=skip_fut,
                arg="board",
            ),
            force_multiprocessing=force_multiprocessing,
            debug_skip_tests=debug_skip_tests,
            debug_skip_usb_error=debug_skip_usb_error,
            reference_board=reference_board,
        )
        testrunner = util_testrunner.TestRunner(args=args)
        logger.info(f"{' '.join(sys.argv)}")
        logger.info(f"{multiprocessing=}")
        logger.info(f"{count=}")
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
            assert target_ctx is not None
            testrunner.run_all_in_sequence(target_ctx=target_ctx)
    except util_baseclasses.OctoprobeAppExitException as e:
        logger.info(f"Terminating test due to OctoprobeAppExitException: {e}")
        raise typer.Exit(1) from e


@app.command(help="Collect json files and create a report")
def report(
    testresults: TyperAnnotated[
        str,
        typer.Option(
            envvar="TESTBED_MICROPYTHON_TESTRESULTS",
            help="Directory containing results",
        ),
    ] = DIRECTORY_TESTRESULTS_DEFAULT,
    url: TyperAnnotated[
        str,
        typer.Option(
            envvar="TESTBED_MICROPYTHON_RESULTS_URL",
            help="Where to push the results. Empty string will skip.",
        ),
    ] = "https://reports.octoprobe.org/upload",
    label: TyperAnnotated[
        str,
        typer.Option(
            help="Label to be used for store the results. For example 'notebook_hans-2025_04_22-12_33_22'.",
        ),
    ] = None,
    action_url: TyperAnnotated[
        str,
        typer.Option(
            help="The url which points back to the github action. For example '://github.com/octoprobe/testbed_micropython_runner/actions/runs/14647476492'.",
        ),
    ] = None,
) -> None:
    init_logging()
    directory_results = assert_valid_testresults(testresults)

    tar = TarAndHttpsPush(directory=directory_results, label=label)
    renderer = ReportRenderer(directory_results=directory_results, label=label)
    renderer.render(action_url=action_url)
    if url == "":
        logger.info("Skipped pushing of the reports: --url=''")
        raise typer.Exit(ExitCode.SUCCESS)

    rc = tar.https_push(url=url)
    raise typer.Exit(rc)


if __name__ == "__main__":
    app()
