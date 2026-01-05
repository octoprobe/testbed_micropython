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
from octoprobe import util_baseclasses
from octoprobe.scripts.commissioning import init_logging
from octoprobe.usb_tentacle.usb_tentacle import serial_short_from_delimited

from testbed_micropython.tentacle_spec import TentacleMicropython
from testbed_micropython.testcollection.baseclasses_spec import ConnectedTentacles

from .. import constants
from ..mptest import util_testrunner
from .util_stress import EnumStressScenario, StressThread
from .util_test_run import EnumTest, run_test

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
for f in DIRECTORY_RESULTS.glob("*.txt"):
    f.unlink(missing_ok=True)
for f in DIRECTORY_RESULTS.glob("*.out"):
    f.unlink(missing_ok=True)


def complete_scenario() -> list[str]:
    return sorted([scenario.name for scenario in EnumStressScenario])


def complete_test() -> list[str]:
    return sorted([test.name for test in EnumTest])


def complete_only_tentacle() -> list[str]:
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
        str | None,
        typer.Option(
            help="Run tests only on these tentacles. All other tentacles are used to create stress",
            autocompletion=complete_only_tentacle,
        ),
    ] = None,  # noqa: UP007
    stress_tentacle_count: TyperAnnotated[
        int,
        typer.Option(
            help="Use that many tentacles to generate stress. May be less if less tentacles are connected.",
        ),
    ] = 99,  # noqa: UP007
    stress_scenario: TyperAnnotated[
        str,
        typer.Option(
            help="Run this stress scenario.", autocompletion=complete_scenario
        ),
    ] = EnumStressScenario.DUT_ON_OFF,
    test: TyperAnnotated[
        str,
        typer.Option(help="Use these test arguments.", autocompletion=complete_test),
    ] = EnumTest.RUN_TESTS_BASIC_B_INT_POW,
) -> None:
    init_logging()
    logger.info(" ".join(sys.argv))
    connected_tentacles = util_testrunner.query_connected_tentacles_fast()
    # connected_tentacles.sort(
    #     key=lambda t: (t.tentacle_spec_base.tentacle_tag, t.tentacle_serial_number)
    # )
    connected_tentacles.sort(key=lambda t: t.tentacle_serial_number)

    try:
        if tentacle is not None:
            test_one_tentacle(
                connected_tentacles=connected_tentacles,
                micropython_tests=micropython_tests,
                tentacle=tentacle,
                stress_tentacle_count=stress_tentacle_count,
                stress_scenario=stress_scenario,
                test=test,
            )
        else:
            for connected_tentacle in connected_tentacles:
                test_one_tentacle(
                    connected_tentacles=connected_tentacles,
                    micropython_tests=micropython_tests,
                    tentacle=serial_short_from_delimited(
                        connected_tentacle.tentacle_serial_number
                    ),
                    stress_tentacle_count=stress_tentacle_count,
                    stress_scenario=stress_scenario,
                    test=test,
                )

    except util_baseclasses.OctoprobeAppExitException as e:
        logger.info(f"Terminating test due to OctoprobeAppExitException: {e}")
        raise typer.Exit(1) from e


def test_one_tentacle(
    connected_tentacles: ConnectedTentacles,
    micropython_tests: str,
    tentacle: str,
    stress_tentacle_count: int,
    stress_scenario: str,
    test: str,
):
    stress_scenario = EnumStressScenario[stress_scenario]
    tentacle_test: TentacleMicropython | None = None
    tentacles_load: ConnectedTentacles = ConnectedTentacles()
    for t in connected_tentacles:
        serial_short = serial_short_from_delimited(t.tentacle_serial_number)
        if serial_short == tentacle:  # type: ignore[attr-defined]
            tentacle_test = t
            continue
        tentacles_load.append(t)

    assert tentacle_test is not None, f"Tentacle not connected: {tentacle}"
    print(f"*** Initialized {len(connected_tentacles)} tentacles")
    for t in connected_tentacles:
        print(f"**** load_base_code_if_needed  {t.description_short}")
        t.infra.load_base_code_if_needed()
        t.switches.default_off_infra_on()
        # if scenario is EnumScenario.INFRA_MPREMOTE:
        #     # if t == tentacle_test:
        #     #     t.infra.switches.dut = True
        #     # else:
        #     #     t.infra.switches.dut = False
        #     t.infra.switches.dut = False

    repo_micropython_tests = pathlib.Path(micropython_tests).expanduser().resolve()
    assert repo_micropython_tests.is_dir(), repo_micropython_tests

    st = StressThread(
        scenario=stress_scenario,
        stress_tentacle_count=stress_tentacle_count,
        tentacles_stress=tentacles_load,
        directory_results=DIRECTORY_RESULTS,
    )

    print("*** start")
    st.start()
    print("*** run_test")
    run_test(
        tentacle_test=tentacle_test,
        repo_micropython_tests=repo_micropython_tests,
        directory_results=DIRECTORY_RESULTS,
        test=EnumTest[test],
    )
    print("*** stop")
    st.stop()


if __name__ == "__main__":
    app()
