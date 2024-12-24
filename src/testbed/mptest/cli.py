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

import typer
import typing_extensions
from mpbuild.board_database import MpbuildMpyDirectoryException
from octoprobe.util_tentacle_label import label_renderer

from testbed.constants import DIRECTORY_DOWNLOADS, URL_FILENAME_DEFAULT
from testbed.mptest import util_testrunner
from testbed.mptest.util_common import ArgsMpTest
from testbed.multiprocessing import util_multiprocessing
from testbed.tentacles_inventory import TENTACLES_INVENTORY
from testbed.testcollection.baseclasses_spec import tentacle_spec_2_tsvs
from testbed.util_firmware_mpbuild_interface import ArgsFirmware

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


def complete_only_variant():
    if False:
        args = util_testrunner.Args.get_default_args()
        testrunner = util_testrunner.TestRunner(args=args)

        connected_tentacles = testrunner.bartender.connected_tentacles
    else:
        connected_tentacles = util_testrunner.query_connected_tentacles_fast()

    tsvs = connected_tentacles.get_tsvs(flash_skip=False)
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
        for tsvs in testrun_spec.list_tsvs_todo:
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
) -> None:

    args = util_testrunner.Args(
        mp_test=None,
        firmware=ArgsFirmware(
            firmware_build=firmware_build,
            flash_skip=False,
            flash_force=True,
        ),
        only_variants=None,
        only_test=None,
        force_multiprocessing=False,
    )
    try:
        testrunner = util_testrunner.TestRunner(args=args)
    except MpbuildMpyDirectoryException as e:
        logger.warning(e)
        return

    args.firmware.flash_force = True
    testrunner.flash(last_variant=last_variant)
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
    only_variant: TyperAnnotated[
        str | None,
        typer.Option(
            help="Only run these on this board variants.",
            autocompletion=complete_only_variant,
        ),
    ] = None,  # noqa: UNoneP007
    only_test: TyperAnnotated[
        str | None,
        typer.Option(help="Only run this test.", autocompletion=complete_only_test),
    ] = None,  # noqa: UP007
    flash_force: TyperAnnotated[
        bool | None,
        typer.Option(help="Will flash all firmare and run tests."),
    ] = None,  # noqa: UP007
    multiprocessing: TyperAnnotated[
        bool,
        typer.Option(
            help="Use python module 'multiprocessing'. This allows parallel processing. Disable to ease debugging.",
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
) -> None:
    only_variants = None if only_variant is None else [only_variant]

    args = util_testrunner.Args(
        mp_test=ArgsMpTest(
            micropython_tests=micropython_tests,
        ),
        firmware=ArgsFirmware(
            firmware_build=firmware_build,
            flash_skip=flash_skip,
            flash_force=flash_force,
        ),
        only_variants=only_variants,
        only_test=only_test,
        force_multiprocessing=force_multiprocessing,
    )
    try:
        testrunner = util_testrunner.TestRunner(args=args)

    except MpbuildMpyDirectoryException as e:
        logger.warning(e)
        return

    cls_process_pool = (
        util_multiprocessing.ProcessPoolAsync
        if multiprocessing
        else util_multiprocessing.ProcessPoolSync
    )
    with cls_process_pool(
        processes=len(testrunner.test_bartender.connected_tentacles) + 1,
        initializer=util_multiprocessing.init_logging,
    ) as process_pool:
        testrunner.run_all_in_sequence(process_pool=process_pool)


if __name__ == "__main__":
    app()
