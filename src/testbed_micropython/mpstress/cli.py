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
from octoprobe.scripts.commissioning import init_logging
from octoprobe.usb_tentacle.usb_tentacle import serial_short_from_delimited

from testbed_micropython.tentacle_spec import TentacleMicropython
from testbed_micropython.testcollection.baseclasses_spec import ConnectedTentacles

from .. import constants
from ..mptest import util_testrunner
from .util_stress import EnumScenario, StressThread
from .util_test_run import run_test

logger = logging.getLogger(__file__)

# 'typer' does not work correctly with typing.Annotated
# Required is: typing_extensions.Annotated
TyperAnnotated = typing_extensions.Annotated

# mypy: disable-error-code="valid-type"
# This will disable this warning:
#   op.py:58: error: Variable "octoprobe.scripts.op.TyperAnnotated" is not valid as a type  [valid-type]
#   op.py:58: note: See https://mypy.readthedocs.io/en/stable/common_issues.html#variables-vs-type-aliases

app = typer.Typer(pretty_exceptions_enable=False)

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent
DIRECTORY_RESULTS = DIRECTORY_OF_THIS_FILE / "testresults"
DIRECTORY_RESULTS.mkdir(parents=True, exist_ok=True)


def complete_scenario():
    return sorted([scenario.name for scenario in EnumScenario])


def complete_only_tentacle():
    connected_tentacles = util_testrunner.query_connected_tentacles_fast()

    return sorted(
        {
            serial_short_from_delimited(t.tentacle_instance.serial)
            for t in connected_tentacles
        }
    )


@app.command(help="Put load on all tentacles to provoke stress")
def stress(
    micropython_tests: TyperAnnotated[
        str,
        typer.Option(
            envvar="TESTBED_MICROPYTHON_MICROPYTHON_TESTS",
            help="Directory of MicroPython-Repo with the tests. Example ~/micropython or https://github.com/micropython/micropython.git@v1.24.1",
        ),
    ] = constants.URL_FILENAME_DEFAULT,
    tentacle: TyperAnnotated[
        list[str],
        typer.Option(
            help="Run tests only on these tentacles. All other tentacles are used to create stress",
            autocompletion=complete_only_tentacle,
        ),
    ] = None,  # noqa: UP007
    scenario: TyperAnnotated[
        str,
        typer.Option(
            help="Run this FUT (feature under test).", autocompletion=complete_scenario
        ),
    ] = EnumScenario.DUT_ON_OFF,
) -> None:
    init_logging()

    try:
        connected_tentacles = util_testrunner.query_connected_tentacles_fast()
        tentacle_test: TentacleMicropython | None = None
        tentacles_load: ConnectedTentacles = ConnectedTentacles()
        for t in connected_tentacles:
            serial_short = serial_short_from_delimited(t.tentacle_instance.serial)
            if serial_short in tentacle:
                tentacle_test = t
                continue
            tentacles_load.append(t)
        assert tentacle_test is not None, f"Tentacle not connected: {tentacle}"
        for t in connected_tentacles:
            t.power.set_default_infra_on()

        repo_micropython_tests = pathlib.Path(micropython_tests).resolve()
        assert repo_micropython_tests.is_dir(), repo_micropython_tests

        st = StressThread(
            scenario=EnumScenario[scenario],
            tentacles_stress=tentacles_load,
            directory_results=DIRECTORY_RESULTS,
        )
        st.start()
        run_test(
            tentacle_test=tentacle_test,
            repo_micropython_tests=repo_micropython_tests,
            directory_results=DIRECTORY_RESULTS,
        )
        st.stop()

    except util_testrunner.OctoprobeAppExitException as e:
        logger.info(f"Terminating test due to OctoprobeAppExitException: {e}")
        raise typer.Exit(1) from e


if __name__ == "__main__":
    app()
