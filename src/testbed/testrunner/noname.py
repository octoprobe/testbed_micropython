from __future__ import annotations

import copy
import itertools
import logging
import pathlib
import shutil
import time
from collections.abc import Iterator

from octoprobe.lib_tentacle import Tentacle
from octoprobe.lib_testbed import Testbed
from octoprobe.octoprobe import NTestRun
from octoprobe.util_dut_programmers import FirmwareSpecBase
from octoprobe.util_pytest import util_logging
from octoprobe.util_pytest.util_resultdir import ResultsDir
from octoprobe.util_testbed_lock import TestbedLock

import testbed.util_testbed
from testbed.constants import (
    DIRECTORY_TESTRESULTS,
    EnumFut,
    EnumTentacleType,
    FILENAME_TESTBED_LOCK,
)
from testbed.tentacles_inventory import TENTACLES_INVENTORY
from testbed.tentacles_spec import (
    McuConfig,
    TENTACLES_SPECS,
    tentacle_spec_mcu_lolin_c3_mini,
    tentacle_spec_mcu_lolin_d1_mini,
    tentacle_spec_mcu_rpi_pico2w,
)
from testbed.testcollection.bartender import (
    AllTestsDoneException,
    TestBartender,
    WaitForTestsToTerminateException,
)
from testbed.testcollection.baseclasses_run import RunSpecContainer
from testbed.testcollection.baseclasses_spec import (
    ConnectedTentacles,
)
from octoprobe.util_usb_serial import QueryResultTentacles

from testbed.testcollection.testrun_specs import (
    TestRunSpecSingle,
    TestRunSpecDouble,
)
from testbed.util_firmware_specs import (
    PYTEST_OPT_BUILD_FIRMWARE,
)
from testbed.util_github_micropython_org import (
    DEFAULT_GIT_MICROPYTHON_TESTS,
    PYTEST_OPT_DIR_MICROPYTHON_TESTS,
    PYTEST_OPT_GIT_MICROPYTHON_TESTS,
)

logger = logging.getLogger(__file__)

# TESTBED = testbed.util_testbed.get_testbed()
TESTBED: Testbed | None = None
DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent


_TESTBED_LOCK = TestbedLock()


def instantiate_tentacles(
    query_result_tentacles: QueryResultTentacles,
) -> list[Tentacle]:
    tentacles: list[Tentacle] = []
    for query_result_tentacle in query_result_tentacles:
        serial = query_result_tentacle.rp2_serial_number
        assert serial is not None
        try:
            hw_version, enum_tag = TENTACLES_INVENTORY[serial]
        except KeyError:
            logger.warning(
                f"Tentacle with serial {serial} is not specified in TENTACLES_INVENTORY."
            )
            continue

        tentacle_spec = TENTACLES_SPECS[enum_tag]

        tentacle = Tentacle[McuConfig, EnumTentacleType, EnumFut](
            tentacle_serial_number=serial,
            tentacle_spec=tentacle_spec,
            hw_version=hw_version,
        )
        tentacle.assign_connected_hub(query_result_tentacle=query_result_tentacle)
        tentacles.append(tentacle)

        if len(tentacles) == 0:
            raise ValueError("No tentacles are connected!")

    return tentacles


def run_tests():
    _TESTBED_LOCK.acquire(FILENAME_TESTBED_LOCK)

    if DIRECTORY_TESTRESULTS.exists():
        shutil.rmtree(DIRECTORY_TESTRESULTS, ignore_errors=False)
    DIRECTORY_TESTRESULTS.mkdir(parents=True, exist_ok=True)

    util_logging.init_logging()
    util_logging.Logs(DIRECTORY_TESTRESULTS)

    query_result_tentacles = NTestRun.session_powercycle_tentacles()

    tentacles = instantiate_tentacles(query_result_tentacles=query_result_tentacles)

    global TESTBED  # pylint: disable=W0603:global-statement
    assert TESTBED is None
    TESTBED = Testbed(workspace="based-on-connected-boards", tentacles=tentacles)

    firmware_git_url = request.config.getoption(PYTEST_OPT_BUILD_FIRMWARE)
    _testrun = NTestRun(testbed=TESTBED, firmware_git_url=firmware_git_url)

    # _testrun.session_powercycle_tentacles()

    _testrun.session_teardown()

    return
    connected_tentacles = ConnectedTentacles(
        [
            Tentacle(
                tentacle_spec=tentacle_spec_mcu_rpi_pico2w,
                tentacle_serial_number="1c4a",
                hw_version="1.0",
            ),
            Tentacle(
                tentacle_spec=tentacle_spec_mcu_rpi_pico2w,
                tentacle_serial_number="1c4b",
                hw_version="1.0",
            ),
            Tentacle(
                tentacle_spec=tentacle_spec_mcu_lolin_d1_mini,
                tentacle_serial_number="1c4c",
                hw_version="1.0",
            ),
            Tentacle(
                tentacle_spec=tentacle_spec_mcu_lolin_c3_mini,
                tentacle_serial_number="1c4d",
                hw_version="1.0",
            ),
        ]
    )
    testrun_spec_container = RunSpecContainer(
        [
            TestRunSpecSingle(
                subprocess_args=["perftest.py"],
                tsvs_tbt=connected_tentacles.tsvs,
            ),
            TestRunSpecDouble(
                subprocess_args=["wlantest.py"],
                tsvs_tbt=connected_tentacles.tsvs,
            ),
        ]
    )
    if False:
        test_runs = list(
            testrun_spec_container.generate(available_tentacles=connected_tentacles)
        )
        for test_run in test_runs:
            print(test_run)
        return

    bartender = TestBartender(
        connected_tentacles=connected_tentacles,
        testrun_spec_container=testrun_spec_container,
    )
    print(f"START: test_dbd={bartender.tests_tbd}")
    for testrun_spec in bartender.testrun_spec_container:
        print(f"  {testrun_spec!r} tests_tbd={testrun_spec.tests_tbd}")
        for tsv in testrun_spec.iter_text_tsvs:
            print(f"    tsv={tsv}")

    for i in itertools.count():
        # if i == 10:
        #     break
        try:
            test_run_next = bartender.test_run_next()
            print(f"{i} test_dbd:{bartender.tests_tbd} test_run_next:{test_run_next}")
            for test_run in bartender.actual_runs:
                print("   ", test_run)
            if len(bartender.actual_runs) >= 3:
                test_run_done = bartender.actual_runs[-1]
                print("  test_run_done:", test_run_done)
                bartender.test_run_done(test_run_done)
            if test_run_next is None:
                return
        except WaitForTestsToTerminateException:
            print(i, "WaitForTestsToTerminateException")
            if len(bartender.actual_runs) == 0:
                print("DONE")
                break
            test_run_done = bartender.actual_runs[-1]
            bartender.test_run_done(test_run_done)
            print("  test_run_done:", test_run_done)

        except AllTestsDoneException:
            print("Done")
            for test_run in bartender.actual_runs:
                print("   ", test_run)
            break


if __name__ == "__main__":

    run_tests()
