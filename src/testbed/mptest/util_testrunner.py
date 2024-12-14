from __future__ import annotations

import dataclasses
import logging
import pathlib
import shutil
import time

from testbed.mpbuild import build_api

from octoprobe.lib_tentacle import Tentacle
from octoprobe.octoprobe import NTestRun
from octoprobe.util_pytest import util_logging
from octoprobe.util_pytest.util_resultdir import ResultsDir
from octoprobe.util_subprocess import SubprocessExitCodeException
from octoprobe.util_testbed_lock import TestbedLock
from octoprobe.util_usb_serial import QueryResultTentacles

from testbed import constants
from testbed.mptest.util_common import ArgsMpTest
from testbed.tentacles_inventory import TENTACLES_INVENTORY
from testbed.tentacles_spec import McuConfig
from testbed.testcollection.bartender import (
    AllTestsDoneException,
    TestBartender,
    WaitForTestsToTerminateException,
)
from testbed.testcollection.baseclasses_run import TestRunSpecs
from testbed.testcollection.baseclasses_spec import ConnectedTentacles
from testbed.testcollection.testrun_specs import TestArgs, TestRun
from testbed.testrunspecs import multinet, none, perftest, runtests, runtests_net_inet
from testbed.util_firmware_mpbuild_interface import ArgsFirmware

logger = logging.getLogger(__file__)

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent


_TESTBED_LOCK = TestbedLock()


def get_testrun_specs(only_test: str | None = None) -> TestRunSpecs:
    specs = [
        multinet.TESTRUNSPEC_RUNTESTS_MULTBLUETOOTH,
        multinet.TESTRUNSPEC_RUNTESTS_MULTINET,
        perftest.TESTRUNSPEC_PERFTEST,
        runtests_net_inet.TESTRUNSPEC_RUNTESTS_NET_HOSTED,
        runtests_net_inet.TESTRUNSPEC_RUNTESTS_NET_INET,
        runtests.TESTRUNSPEC_RUNTESTS_BASICS,
        runtests.TESTRUNSPEC_RUNTESTS_EXTMOD_HARDWARE,
        none.TESTRUNSPEC_RUNTESTS_NONE,
    ]

    if only_test is not None:
        err_msg = f"Test '{only_test}' not found. Valid tests are {','.join([s.label for s in specs])}"
        for spec in specs:
            if spec.label == only_test:
                return TestRunSpecs([spec])

        raise ValueError(err_msg)

    return TestRunSpecs(specs)


@dataclasses.dataclass
class Args:
    mp_test: ArgsMpTest
    firmware: ArgsFirmware
    only_variants: list[str] | None
    only_test: str | None

    @staticmethod
    def get_default_args() -> Args:
        return Args(
            mp_test=ArgsMpTest(
                micropython_tests=constants.URL_FILENAME_DEFAULT,
            ),
            firmware=ArgsFirmware(
                firmware_build=constants.URL_FILENAME_DEFAULT,
                flash_skip=True,
                flash_force=False,
            ),
            only_variants=None,
            only_test=None,
        )


def instantiate_tentacles(
    query_result_tentacles: QueryResultTentacles,
) -> ConnectedTentacles:
    assert isinstance(query_result_tentacles, QueryResultTentacles)

    tentacles = ConnectedTentacles()
    for query_result_tentacle in query_result_tentacles:
        serial = query_result_tentacle.rp2_serial_number
        assert serial is not None
        try:
            hw_version, tentacle_spec = TENTACLES_INVENTORY[serial]
        except KeyError:
            logger.warning(
                f"Tentacle with serial {serial} is not specified in TENTACLES_INVENTORY."
            )
            continue

        tentacle = Tentacle[McuConfig, constants.EnumTentacleType, constants.EnumFut](
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
        _TESTBED_LOCK.acquire(constants.FILENAME_TESTBED_LOCK)

        if constants.DIRECTORY_TESTRESULTS.exists():
            shutil.rmtree(constants.DIRECTORY_TESTRESULTS, ignore_errors=False)
        constants.DIRECTORY_TESTRESULTS.mkdir(parents=True, exist_ok=True)

        util_logging.init_logging()
        util_logging.Logs(constants.DIRECTORY_TESTRESULTS)

        query_result_tentacles = NTestRun.session_powercycle_tentacles()

        connected_tentacles = instantiate_tentacles(
            query_result_tentacles=query_result_tentacles
        )
        if len(connected_tentacles) == 0:
            logger.warning("No tentacles discovered!")
            raise SystemExit(0)

        connected_tentacles = connected_tentacles.get_only(
            board_variants=args.only_variants
        )

        self.ntestrun = NTestRun(connected_tentacles=connected_tentacles)
        args.firmware.setup()

        # _testrun.session_powercycle_tentacles()

        testrun_specs = get_testrun_specs(only_test=args.only_test)
        testrun_specs.assign_tentacles(
            tentacles=connected_tentacles, only_board_variants=args.only_variants
        )
        self.bartender = TestBartender(
            connected_tentacles=connected_tentacles,
            testrun_specs=testrun_specs,
        )

    def run_all_in_sequence(self) -> None:
        git_micropython_tests = self.args.mp_test.clone_git_micropython_tests(
            directory_git_cache=constants.DIRECTORY_GIT_CACHE
        )
        while True:
            try:
                testrun = self.bartender.testrun_next()
            except WaitForTestsToTerminateException:
                print("WaitForTestsToTerminateException: Should never happen!")
                time.sleep(10)
                continue

            except AllTestsDoneException:
                print("Done")
                assert len(self.bartender.actual_runs) == 0
                break

            #
            # Run test
            #
            try:
                self.run_one_test(
                    testrun=testrun,
                    git_micropython_tests=git_micropython_tests,
                )
            finally:
                self.bartender.testrun_done(test_run=testrun)

        self.ntestrun.session_teardown()

    def run_one_test(
        self, testrun: TestRun, git_micropython_tests: pathlib.Path
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
        assert isinstance(testrun, TestRun)
        assert len(testrun.list_tentacle_variant) > 0

        logger.info(testrun.testid)

        self.assign_firmware_specs(testrun=testrun)

        testresults_directory = ResultsDir(
            directory_top=constants.DIRECTORY_TESTRESULTS,
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
                    futs=(testrun.testrun_spec.required_fut,),
                    tentacles=testrun.tentacles,
                )
                logger.info(
                    f"TEST BEGIN {duration_text()} {testresults_directory.test_nodeid}"
                )

                try:
                    testrun.test(
                        testargs=TestArgs(
                            testresults_directory=testresults_directory,
                            git_micropython_tests=git_micropython_tests,
                        )
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
