from __future__ import annotations

import dataclasses
import itertools
import pathlib
import sys
import typing

import pytest
from octoprobe.usb_tentacle.usb_baseclasses import Location, TENTACLE_VERSION_V03
from octoprobe.usb_tentacle.usb_tentacle import UsbPico, UsbTentacle
from octoprobe.util_baseclasses import TentacleInstance

from testbed_micropython import constants
from testbed_micropython.bartenders import test_bartender
from testbed_micropython.mptest import util_testrunner
from testbed_micropython.tentacle_spec import (
    TentacleMicropython,
    TentacleSpecMicropython,
)
from testbed_micropython.tentacle_specs import LOLIN_C3_MINI, LOLIN_D1_MINI, RPI_PICO
from testbed_micropython.testcollection import baseclasses_run, testrun_specs
from testbed_micropython.testcollection.baseclasses_spec import ConnectedTentacles
from testbed_micropython.testrunspecs import runtests
from testbed_micropython.util_pytest_git import assert_git_unchanged

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent
DIRECTORY_TESTRESULTS = DIRECTORY_OF_THIS_FILE / "test_collection_testresults"
DIRECTORY_TESTRESULTS.mkdir(parents=True, exist_ok=True)


class ForkTextIO(typing.TextIO):  # pylint: disable=abstract-method
    __slots__ = ("files",)

    def __init__(self, files: list[typing.TextIO]) -> None:
        super().__init__()
        self.files = files

    @typing.override
    def write(self, msg: typing.AnyStr) -> int:  # pylint: disable=deprecated-attribute
        assert isinstance(msg, str)
        for file in self.files:
            file.write(msg)
        return 0


@dataclasses.dataclass
class Ttestparam:
    label: str
    specs: list[TentacleSpecMicropython]
    testrun_specs: baseclasses_run.TestRunSpecs
    count: int = 1
    flash_skip: bool = False

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
    testrun_specs_ = testparam.testrun_specs

    def factory() -> list[TentacleMicropython]:
        tentacle_list = []
        for i, spec in enumerate(specs):
            serial = f"1c4{i}"
            tentacle_instance = TentacleInstance(
                serial=serial,
                tentacle_spec=spec,
                hw_version="1.0",
                testbed_name="testbed_micropython",
                testbed_instance="ch_hans_1",
            )
            tentacle_list.append(
                TentacleMicropython(
                    tentacle_instance=tentacle_instance,
                    tentacle_serial_number=serial,
                    usb_tentacle=UsbTentacle(
                        hub4_location=Location(3, [1, i]),
                        pico_infra=UsbPico(
                            location=Location(bus=1, path=[]),
                            serial=None,
                            serial_port=None,
                        ),
                        pico_probe=None,
                        tentacle_version=TENTACLE_VERSION_V03,
                    ),
                )
            )
        # Sort tentacles by their serial for deterministic output
        tentacle_list.sort(key=lambda t: t.tentacle_serial_number)
        return tentacle_list

    connected_tentacles = ConnectedTentacles(factory())

    testrun_specs_.assign_tentacles(
        tentacles=connected_tentacles,
        flash_skip=testparam.flash_skip,
        count=testparam.count,
    )

    print("## testrun_specs", file=file)
    testrun_specs_.pytest_print(indent=1, file=file)

    bartender = test_bartender.TestBartender(
        connected_tentacles=connected_tentacles,
        tentacle_reference=None,
        testrun_specs=testrun_specs_,
        priority_sorter=baseclasses_run.TestRun.priority_sorter,
        directory_results=DIRECTORY_TESTRESULTS,
    )
    print(f"## START: test_todo={bartender.tests_todo}")

    firmwares_built: set[str] = {
        constants.DEFAULT_REFERENCE_BOARD,
        "LOLIN_C3_MINI",
        "ESP8266_GENERIC",
        "ESP8266_GENERIC-FLASH_512K",
    }
    args = util_testrunner.Args.get_default_args(
        directory_git_cache=constants.DIRECTORY_GIT_CACHE,
        directory_results=constants.DIRECTORY_TESTRESULTS_DEFAULT,
    )
    args.firmware.flash_skip = False
    ctxtestrun = util_testrunner.CtxTestRun(connected_tentacles=connected_tentacles)
    repo_micropython_tests = pathlib.Path("/dummy_path")

    def testrun_done(len_actual_testruns_at_least: int) -> None:
        """
        We set a testrun to done if the len
        """
        actual_testruns = bartender.actual_testruns
        if len(actual_testruns) <= len_actual_testruns_at_least:
            return
        testrun_done = actual_testruns[-1]
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
        if i >= 30:
            print("ERROR: should never get here!", file=file)
            break

        try:
            print(f"## {i}: testrun_specs", file=file)
            testrun_specs_.pytest_print(indent=1, file=file)

            possible_testruns = bartender.possible_testruns(
                firmwares_built=firmwares_built,
                flash_skip=args.firmware.flash_skip,
            )
            print(f"## {i}: possible_testruns", file=file)
            for possible_testrun in possible_testruns:
                possible_testrun.pytest_print(indent=1, file=file)

            async_target = bartender.testrun_next(
                firmwares_built=firmwares_built,
                args=args,
                ctxtestrun=ctxtestrun,
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
        except test_bartender.CurrentlyNoTestsException:
            print(i, "CurrentlyNoTestsException")
            testrun_done(len_actual_testruns_at_least=0)

        if bartender.tests_todo == 0:
            print("Done")
            for testrun in bartender.actual_testruns:
                print("   ", testrun)
            break


_TESTRUNSPEC_PERFBENCH = testrun_specs.TestRunSpec(
    label="TESTPERF",
    helptext="Run perftest on each board.",
    command=["perfbench.py", "run-perfbench.py"],
    required_fut=constants.EnumFut.FUT_MCU_ONLY,
    requires_reference_tentacle=False,
    testrun_class=runtests.TestRunRunTests,
    timeout_s=60.0,
)
_TESTRUNSPEC_WLAN = testrun_specs.TestRunSpec(
    label="TESTWLAN",
    helptext="Two boards have to access a AP",
    command=["wlan.py", "wlantest.py"],
    required_fut=constants.EnumFut.FUT_WLAN,
    requires_reference_tentacle=False,
    testrun_class=runtests.TestRunRunTests,
    timeout_s=5 * 60.0,
)


_TESTPARAM_WLAN_ASYMMETRICAL = Ttestparam(
    label="wlan_asymmetrical",
    specs=[LOLIN_D1_MINI, LOLIN_C3_MINI],
    testrun_specs=baseclasses_run.TestRunSpecs([_TESTRUNSPEC_WLAN]),
)
_TESTPARAM_WLAN_SYMMETRICAL2 = Ttestparam(
    label="wlan_symmetrical2",
    specs=[LOLIN_C3_MINI, LOLIN_C3_MINI],
    testrun_specs=baseclasses_run.TestRunSpecs([_TESTRUNSPEC_WLAN]),
)
_TESTPARAM_WLAN_SYMMETRICAL3 = Ttestparam(
    label="wlan_symmetrical3",
    specs=[LOLIN_C3_MINI, LOLIN_C3_MINI, LOLIN_C3_MINI],
    testrun_specs=baseclasses_run.TestRunSpecs([_TESTRUNSPEC_WLAN]),
)
_TESTPARAM_POTPOURRY = Ttestparam(
    label="potpourry",
    specs=[RPI_PICO, RPI_PICO, LOLIN_D1_MINI, LOLIN_C3_MINI],
    testrun_specs=baseclasses_run.TestRunSpecs(
        [_TESTRUNSPEC_WLAN, _TESTRUNSPEC_PERFBENCH]
    ),
)
_TESTPARAMS = [
    _TESTPARAM_WLAN_ASYMMETRICAL,
    _TESTPARAM_WLAN_SYMMETRICAL2,
    _TESTPARAM_WLAN_SYMMETRICAL3,
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
