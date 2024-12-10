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
from octoprobe.util_subprocess import SubprocessExitCodeException
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
from testbed.testcollection.baseclasses_spec import ConnectedTentacles
from testbed.testcollection.testrun_specs import TestRun, TestRunSpec
from testbed.testrunner.util_common import ArgsMpTest
from testbed.testrunner.util_testrun import TestRunPerfTest, TestRunRunTests
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


class TestRunner:
    def __init__(self, args: Args) -> None:
        """
        Initialize logging
        Query the tentacles.
        Clone github.
        """
        assert isinstance(args, Args)
        self.args = args
        _TESTBED_LOCK.acquire(FILENAME_TESTBED_LOCK)

        if DIRECTORY_TESTRESULTS.exists():
            shutil.rmtree(DIRECTORY_TESTRESULTS, ignore_errors=False)
        DIRECTORY_TESTRESULTS.mkdir(parents=True, exist_ok=True)

        util_logging.init_logging()
        util_logging.Logs(DIRECTORY_TESTRESULTS)

        query_result_tentacles = NTestRun.session_powercycle_tentacles()

        self.connected_tentacles = instantiate_tentacles(
            query_result_tentacles=query_result_tentacles
        )
        if len(self.connected_tentacles) == 0:
            logger.warning("No tentacles discovered!")
            raise SystemExit(0)

        self.ntestrun = NTestRun(connected_tentacles=self.connected_tentacles)
        args.firmware.setup()

        # _testrun.session_powercycle_tentacles()
        testrun_specs = TestRunSpecs(
            [
                TestRunSpec(
                    subprocess_args=["run-perfbench.py"],
                    tentacles_required=1,
                    tsvs_tbt=self.connected_tentacles.tsvs,
                    testrun_class=TestRunPerfTest,
                ),
                TestRunSpec(
                    subprocess_args=["run-tests.py", "--test-dirs=extmod_hardware"],
                    tentacles_required=1,
                    tsvs_tbt=self.connected_tentacles.tsvs,
                    testrun_class=TestRunRunTests,
                ),
                TestRunSpec(
                    subprocess_args=["run-tests.py", "--test-dirs=misc"],
                    tentacles_required=1,
                    tsvs_tbt=self.connected_tentacles.tsvs,
                    testrun_class=TestRunRunTests,
                ),
            ]
        )
        self.bartender = TestBartender(
            connected_tentacles=self.connected_tentacles,
            testrun_specs=testrun_specs,
        )

        self.git_micropython_tests = args.mp_test.clone_git_micropython_tests(
            directory_git_cache=DIRECTORY_GIT_CACHE
        )

    def run_all_in_sequence(self) -> None:
        while True:
            try:
                testrun = self.bartender.testrun_next()
            except WaitForTestsToTerminateException:
                print("WaitForTestsToTerminateException: Should never happen!")

            except AllTestsDoneException:
                print("Done")
                assert len(self.bartender.actual_runs) == 0
                break

            #
            # Run test
            #
            try:
                self.run_one_test(testrun=testrun)
            finally:
                self.bartender.testrun_done(test_run=testrun)

        self.ntestrun.session_teardown()

    def run_one_test(self, testrun: TestRun) -> None:
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
        assert isinstance(testrun, TestRun)
        assert len(testrun.list_tentacle_variant) > 0

        logger.info(testrun.testid)

        # TODO: remove hardcoded EnumFut.FUT_MCU_ONLY
        required_futs = (EnumFut.FUT_MCU_ONLY,)

        self.assign_firmware_specs(testrun=testrun)

        testresults_directory = ResultsDir(
            directory_top=DIRECTORY_TESTRESULTS,
            test_name=testrun.testid,
            test_nodeid=testrun.testid,
        )

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
                self.args.firmware.build_firmwares(
                    active_tentacles=testrun.tentacles,
                    testresults_mpbuild=testresults_directory.directory_top / "mpbuild",
                )
                self.ntestrun.function_prepare_dut()
                self.ntestrun.function_setup_infra()
                self.ntestrun.function_setup_dut(active_tentacles=testrun.tentacles)

                self.ntestrun.setup_relays(
                    futs=required_futs, tentacles=testrun.tentacles
                )
                logger.info(
                    f"TEST BEGIN {duration_text()} {testresults_directory.test_nodeid}"
                )

                try:
                    testrun.test(
                        testresults_directory=testresults_directory,
                        git_micropython_tests=self.git_micropython_tests,
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
                    self.ntestrun.function_teardown(active_tentacles=testrun.tentacles)
                except Exception as e:
                    logger.exception(e)
                logger.info(
                    f"TEST END {duration_text()} {testresults_directory.test_nodeid}"
                )

    def assign_firmware_specs(self, testrun: TestRun) -> None:
        """
        For a test, the firmwarespec is assigned to each tentacle (which is a bit hacky).
        For not changing the pool of connected_tentacles, each tentacle will be cloned.
        """
        testrun.copy_tentacles()
        # Assign firmware_spec to each tentacle
        for tentacle_variant in testrun.list_tentacle_variant:
            tentacle_variant.tentacle._firmware_spec = (
                self.args.firmware.get_firmware_spec(
                    tentacle=tentacle_variant.tentacle,
                    variant=tentacle_variant.variant,
                )
            )
