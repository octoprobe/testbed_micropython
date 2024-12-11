from __future__ import annotations

import dataclasses
import itertools
import pathlib
import sys
import typing

import pytest
from octoprobe.util_usb_serial import QueryResultTentacle
from usbhubctl import Location

from testbed.constants import EnumFut
from testbed.mptest import util_testrunner
from testbed.multiprocessing.test_bartender import (
    CurrentlyNoTestsException,
    TestBartender,
)
from testbed.tentacle_spec import TentacleMicropython, TentacleSpecMicropython
from testbed.tentacle_specs import LOLIN_C3_MINI, LOLIN_D1_MINI, RPI_PICO
from testbed.testcollection.baseclasses_run import TestRun, TestRunSpecs
from testbed.testcollection.baseclasses_spec import ConnectedTentacles
from testbed.testcollection.testrun_specs import TestRunSpec
from testbed.util_pytest_git import assert_git_unchanged

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent
DIRECTORY_TESTRESULTS = DIRECTORY_OF_THIS_FILE / "test_collection_testresults"
DIRECTORY_TESTRESULTS.mkdir(parents=True, exist_ok=True)


class ForkTextIO(typing.TextIO):  # pylint: disable=abstract-method
    __slots__ = ("files",)

    def __init__(self, files: list[typing.TextIO]) -> None:
        super().__init__()
        self.files = files

    @typing.override
    def write(self, msg: typing.AnyStr) -> int:
        assert isinstance(msg, str)
        for file in self.files:
            file.write(msg)
        return 0


@dataclasses.dataclass
class Ttestparam:
    label: str
    specs: list[TentacleSpecMicropython]
    testrun_specs: TestRunSpecs

    @property
    def pytest_id(self) -> str:
        return self.label.replace(" ", "-")

    @property
    def filename_txt(self) -> pathlib.Path:
        return DIRECTORY_TESTRESULTS / f"testresult_{self.label}.txt"


def _test_collection(testparam: Ttestparam) -> None:
    with testparam.filename_txt.open("w") as file:
        fork = ForkTextIO(files=[file, sys.stdout])  # type: ignore[abstract]
        _test_collection2(testparam, file=fork)
    assert_git_unchanged(filename=testparam.filename_txt)


def _test_collection2(testparam: Ttestparam, file: typing.TextIO) -> None:

    specs = testparam.specs
    testrun_specs = testparam.testrun_specs

    def factory() -> typing.Iterator[TentacleMicropython]:
        for i, spec in enumerate(specs):
            yield TentacleMicropython(
                tentacle_spec_base=spec,
                tentacle_serial_number=f"1c4{i}",
                hw_version="1.0",
                hub=QueryResultTentacle(hub_location=Location(3, [1, i])),
            )

    connected_tentacles = ConnectedTentacles(factory())

    testrun_specs.assign_tentacles(
        tentacles=connected_tentacles,
        only_board_variants=None,
    )

    print("## testrun_specs", file=file)
    testrun_specs.pytest_print(indent=1, file=file)

    bartender = TestBartender(
        connected_tentacles=connected_tentacles,
        testrun_specs=testrun_specs,
        priority_sorter=TestRun.priority_sorter,
    )
    print(f"## START: test_todo={bartender.tests_todo}")

    firmwares_built: set[str] = {
        "RPI_PICO",
        "LOLIN_C3_MINI",
        "ESP8266_GENERIC",
        "ESP8266_GENERIC-FLASH_512K",
    }
    args = util_testrunner.Args.get_default_args()
    ntestrun = util_testrunner.NTestRun(connected_tentacles=connected_tentacles)
    repo_micropython_tests = pathlib.Path("/dummy_path")

    def testrun_done(len_actual_testruns_at_least: int) -> None:
        """
        We set a testrun to done if the len
        """
        actual_testruns = bartender.actual_testruns
        if len(actual_testruns) < len_actual_testruns_at_least:
            return
        testrun_done = bartender.actual_testruns[-1]
        print(f"###  testrun_done: {testrun_done.testrun.testid}", file=file)

        event = util_testrunner.EventExitRunOneTest(
            target_unique_name=testrun_done.target_unique_name,
            logfile=pathlib.Path("/dummy"),
            success=True,
            testid="Firmware",
        )
        bartender.testrun_done(event)
        testrun_done.fake_join()

    for i in itertools.count():
        if i == 30:
            break
        try:
            print(f"## {i}: testrun_specs", file=file)
            testrun_specs.pytest_print(indent=1, file=file)

            print(f"## {i}: tsvs_combinations", file=file)
            for testrun_spec in bartender.testrun_specs:
                print(f"  TestRunSpec[{testrun_spec.label}]", file=file)
                for tsvs_combination in sorted(
                    testrun_spec.tsvs_combinations(firmwares_built=firmwares_built)
                ):
                    print(f"    {tsvs_combination!r}")

            possible_testruns = bartender.possible_testruns(
                firmwares_built=firmwares_built
            )
            print(f"## {i}: possible_testruns", file=file)
            for possible_testrun in possible_testruns:
                possible_testrun.pytest_print(indent=1, file=file)
                pass

            async_target = bartender.testrun_next(
                firmwares_built=firmwares_built,
                args=args,
                ntestrun=ntestrun,
                repo_micropython_tests=repo_micropython_tests,
            )
            assert async_target is not None
            async_target.fake_start()
            print(
                f"### {i}: fake_start:{bartender.tests_todo} testrun_next: {async_target.testrun.debug_text} / {async_target.testrun.testid}",
                file=file,
            )
            bartender.pytest_print_actual_testruns(
                title="### actual_testruns", indent=2, file=file
            )
            testrun_done(len_actual_testruns_at_least=2)
        except CurrentlyNoTestsException:
            print(i, "CurrentlyNoTestsException")
            testrun_done(len_actual_testruns_at_least=0)

        if bartender.tests_todo == 0:
            print("Done")
            for testrun in bartender.actual_testruns:
                print("   ", testrun)
            break


_TESTRUNSPEC_PERFBENCH = TestRunSpec(
    label="TESTPERF",
    helptext="Run perftest on each board.",
    command=["perfbench.py", "run-perfbench.py"],
    required_fut=EnumFut.FUT_MCU_ONLY,
    required_tentacles_count=1,
    timeout_s=60.0,
)
_TESTRUNSPEC_WLAN = TestRunSpec(
    label="TESTWLAN",
    helptext="Two boards have to access a AP",
    command=["wlan.py", "wlantest.py"],
    required_fut=EnumFut.FUT_WLAN,
    required_tentacles_count=2,
    timeout_s=5 * 60.0,
)


_TESTPARAM_WLAN_ASYMMETRICAL = Ttestparam(
    label="wlan_asymmetrical",
    specs=[LOLIN_D1_MINI, LOLIN_C3_MINI],
    testrun_specs=TestRunSpecs([_TESTRUNSPEC_WLAN]),
)

_TESTPARAM_WLAN_SYMMETRICAL = Ttestparam(
    label="wlan_symmetrical",
    specs=[LOLIN_C3_MINI, LOLIN_C3_MINI],
    testrun_specs=TestRunSpecs([_TESTRUNSPEC_WLAN]),
)
_TESTPARAM_POTPOURRY = Ttestparam(
    label="potpourry",
    specs=[RPI_PICO, RPI_PICO, LOLIN_D1_MINI, LOLIN_C3_MINI],
    testrun_specs=TestRunSpecs([_TESTRUNSPEC_WLAN, _TESTRUNSPEC_PERFBENCH]),
)
_TESTPARAMS = [
    _TESTPARAM_WLAN_ASYMMETRICAL,
    _TESTPARAM_WLAN_SYMMETRICAL,
    _TESTPARAM_POTPOURRY,
]


@pytest.mark.parametrize(
    "testparam", _TESTPARAMS, ids=lambda testparam: testparam.pytest_id
)
def test_collection(testparam: Ttestparam) -> None:
    _test_collection(testparam)


if __name__ == "__main__":
    _test_collection(testparam=_TESTPARAM_WLAN_ASYMMETRICAL)
    # _test_collection(testparam=_TESTPARAM_POTPOURRY)
