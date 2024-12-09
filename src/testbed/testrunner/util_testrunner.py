from __future__ import annotations

import dataclasses
import logging
import pathlib
import shutil
import sys
import time

from octoprobe.lib_tentacle import Tentacle
from octoprobe.octoprobe import NTestRun
from octoprobe.util_pytest import util_logging
from octoprobe.util_pytest.util_resultdir import ResultsDir
from octoprobe.util_subprocess import SubprocessExitCodeException, subprocess_run
from octoprobe.util_testbed_lock import TestbedLock
from octoprobe.util_usb_serial import QueryResultTentacles

from testbed.constants import (
    DIRECTORY_GIT_CACHE,
    DIRECTORY_TESTRESULTS,
    EnumFut,
    EnumTentacleType,
    FILENAME_TESTBED_LOCK,
)
from testbed.tentacles_inventory import TENTACLES_INVENTORY
from testbed.tentacles_spec import McuConfig, TENTACLES_SPECS
from testbed.testcollection.bartender import (
    AllTestsDoneException,
    TestBartender,
    WaitForTestsToTerminateException,
)
from testbed.testcollection.baseclasses_run import TestRunSpecs
from testbed.testcollection.baseclasses_spec import (
    ConnectedTentacles,
)
from testbed.testcollection.testrun_specs import TestRun, TestRunSpec
from testbed.testrunner.utils_common import ArgsMpTest
from testbed.util_firmware_mpbuild_interface import ArgsFirmware

logger = logging.getLogger(__file__)

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent


_TESTBED_LOCK = TestbedLock()


@dataclasses.dataclass
class Args:
    mp_test: ArgsMpTest
    firmware: ArgsFirmware
    only_boards: list[str] | None


def instantiate_tentacles(
    query_result_tentacles: QueryResultTentacles,
) -> ConnectedTentacles:
    tentacles = ConnectedTentacles()
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


def run_single_test_parallel(
    ntest_run: NTestRun,
    required_futs: tuple[EnumFut],
    active_tentacles: list[Tentacle],
    testresults_directory: ResultsDir,
    testrun: TestRun,
    args: Args,
    git_micropython_tests: pathlib.Path,
) -> None:
    """
    Runs setup and teardown for every single test:

    * Setup

      * powercycle the tentacles
      * Turns on the 'active' LED on the tentacles involved
      * Flash firmware
      * Set the relays according to `@pytest.mark.required_futs(EnumFut.FUT_I2C)`.

    * yields to the test function
    * Teardown

      * Resets the relays.

    :param testrun: The structure created by `testrun()`
    :type testrun: NTestRun
    """
    assert len(active_tentacles) > 0

    with util_logging.Logs(testresults_directory.directory_test):
        begin_s = time.monotonic()

        def duration_text(duration_s: float | None = None) -> str:
            if duration_s is None:
                duration_s = time.monotonic() - begin_s
            return f"{duration_s:2.0f}s"

        try:
            logger.info(
                f"TEST SETUP {duration_text(0.0)} {testresults_directory.test_nodeid}"
            )
            args.firmware.build_firmwares(
                active_tentacles=active_tentacles,
                testresults_mpbuild=testresults_directory.directory_top / "mpbuild",
            )
            ntest_run.function_prepare_dut()
            ntest_run.function_setup_infra()
            ntest_run.function_setup_dut(active_tentacles=active_tentacles)

            ntest_run.setup_relays(futs=required_futs, tentacles=active_tentacles)
            logger.info(
                f"TEST BEGIN {duration_text()} {testresults_directory.test_nodeid}"
            )
            # TODO: Run test

            def test_perf_bench(
                testrun: TestRun,
                mcu: Tentacle,
                testresults_directory: ResultsDir,
            ) -> None:
                """
                This tests runs: run-perfbench.py

                * https://github.com/micropython/micropython/blob/master/tests/README.md
                * https://github.com/micropython/micropython/blob/master/tests/run-perfbench.py
                """
                assert mcu.tentacle_spec.mcu_config is not None
                perftest_args = mcu.tentacle_spec.mcu_config.micropython_perftest_args
                if perftest_args is None:
                    perftest_args = ["100", "100"]

                args = [
                    sys.executable,
                    # "run-perfbench.py",
                    *testrun.testrun_spec.subprocess_args,
                    "--pyboard",
                    f"--device={mcu.dut.get_tty()}",
                    *perftest_args,
                ]
                subprocess_run(
                    args=args,
                    cwd=git_micropython_tests / "tests",
                    logfile=testresults_directory("run-perfbench.txt").filename,
                    timeout_s=300.0,
                )

            try:
                test_perf_bench(
                    testrun=testrun,
                    mcu=testrun.tentacles[0],
                    testresults_directory=testresults_directory,
                )
                logger.warning("Test SUCCESS")
            except SubprocessExitCodeException as e:
                logger.warning(f"Test returned exit code: {e!r}")
            except Exception as e:
                logger.warning(f"Test failed: {e}")
                logger.exception(e)

        except Exception as e:
            logger.warning(f"Exception during test: {e!r}")
            logger.exception(e)
        finally:
            logger.info(
                f"TEST TEARDOWN {duration_text()} {testresults_directory.test_nodeid}"
            )
            try:
                ntest_run.function_teardown(active_tentacles=active_tentacles)
            except Exception as e:
                logger.exception(e)
            logger.info(
                f"TEST END {duration_text()} {testresults_directory.test_nodeid}"
            )


def run_tests(args: Args):
    _TESTBED_LOCK.acquire(FILENAME_TESTBED_LOCK)

    if DIRECTORY_TESTRESULTS.exists():
        shutil.rmtree(DIRECTORY_TESTRESULTS, ignore_errors=False)
    DIRECTORY_TESTRESULTS.mkdir(parents=True, exist_ok=True)

    util_logging.init_logging()
    util_logging.Logs(DIRECTORY_TESTRESULTS)

    query_result_tentacles = NTestRun.session_powercycle_tentacles()

    connected_tentacles = instantiate_tentacles(
        query_result_tentacles=query_result_tentacles
    )
    if len(connected_tentacles) == 0:
        logger.warning("No tentacles discovered!")
        return

    _testrun = NTestRun(connected_tentacles=connected_tentacles)
    args.firmware.setup()

    # _testrun.session_powercycle_tentacles()
    testrun_specs = TestRunSpecs(
        [
            TestRunSpec(
                subprocess_args=["run-perfbench.py"],
                tentacles_required=1,
                tsvs_tbt=connected_tentacles.tsvs,
            )
        ]
    )
    bartender = TestBartender(
        connected_tentacles=connected_tentacles,
        testrun_specs=testrun_specs,
    )

    git_micropython_tests = args.mp_test.clone_git_micropython_tests(
        directory_git_cache=DIRECTORY_GIT_CACHE
    )
    while True:
        try:
            testrun = bartender.testrun_next()
        except WaitForTestsToTerminateException:
            print("WaitForTestsToTerminateException: Should never happen!")

        except AllTestsDoneException:
            print("Done")
            assert len(bartender.actual_runs) == 0
            break

        #
        # Run test
        #
        testrun.copy_tentacles()

        # Assign firmware_spec to each tentacle
        for tentacle in testrun.tentacles:
            tentacle._firmware_spec = args.firmware.get_firmware_spec(tentacle=tentacle)

        print(testrun.testid)

        testresults_directory = ResultsDir(
            directory_top=DIRECTORY_TESTRESULTS,
            test_name=testrun.testid,
            test_nodeid=testrun.testid,
        )
        # TODO: remove hardcoded EnumFut.FUT_MCU_ONLY
        run_single_test_parallel(
            ntest_run=_testrun,
            required_futs=(EnumFut.FUT_MCU_ONLY,),
            active_tentacles=testrun.tentacles,
            testresults_directory=testresults_directory,
            testrun=testrun,
            args=args,
            git_micropython_tests=git_micropython_tests,
        )

        bartender.testrun_done(test_run=testrun)

    _testrun.session_teardown()
