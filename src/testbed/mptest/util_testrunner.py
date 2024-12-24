from __future__ import annotations

import dataclasses
import logging
import pathlib
import shutil
import time

from octoprobe.lib_tentacle import Tentacle
from octoprobe.octoprobe import NTestRun
from octoprobe.util_baseclasses import OctoprobeException
from octoprobe.util_pytest import util_logging
from octoprobe.util_pytest.util_resultdir import ResultsDir
from octoprobe.util_subprocess import SubprocessExitCodeException
from octoprobe.util_testbed_lock import TestbedLock
from octoprobe.util_usb_serial import QueryResultTentacle, QueryResultTentacles

from testbed import constants
from testbed.mptest.util_common import ArgsMpTest
from testbed.multiprocessing import util_multiprocessing
from testbed.multiprocessing.firmware_bartender import (
    AsyncResultFirmware,
    FirmwareBartender,
)
from testbed.multiprocessing.test_bartender import (
    AllTestsDoneException,
    AsyncResultTest,
    CurrentlyNoTestsException,
    TestBartender,
)
from testbed.tentacle_spec import McuConfig, TentacleSpecMicropython
from testbed.tentacles_inventory import TENTACLES_INVENTORY
from testbed.testcollection.baseclasses_run import TestRunSpecs
from testbed.testcollection.baseclasses_spec import ConnectedTentacles
from testbed.testcollection.testrun_specs import TestArgs, TestRun
from testbed.testrunspecs import multinet, perftest, runtests, runtests_net_inet
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
    mp_test: ArgsMpTest | None
    firmware: ArgsFirmware
    only_variants: list[str] | None
    only_test: str | None
    force_multiprocessing: bool

    def __post_init__(self) -> None:
        assert isinstance(self.mp_test, ArgsMpTest | None)
        assert isinstance(self.firmware, ArgsFirmware)
        assert isinstance(self.only_variants, list | None)
        assert isinstance(self.only_test, str | None)
        assert isinstance(self.force_multiprocessing, bool)

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
            force_multiprocessing=False,
        )


def query_connected_tentacles_fast() -> ConnectedTentacles:
    query_result_tentacles = QueryResultTentacle.query_fast()

    return instantiate_tentacles(query_result_tentacles)


def instantiate_tentacles(
    query_result_tentacles: QueryResultTentacles,
) -> ConnectedTentacles:
    assert isinstance(query_result_tentacles, QueryResultTentacles)

    if len(query_result_tentacles) == 0:
        raise ValueError("No tentacles are connected!")

    tentacles = ConnectedTentacles()
    for query_result_tentacle in query_result_tentacles:
        serial = query_result_tentacle.rp2_serial_number
        assert serial is not None
        try:
            tentacle_instance = TENTACLES_INVENTORY[serial]
        except KeyError:
            logger.warning(
                f"Tentacle with serial {serial} is not specified in TENTACLES_INVENTORY."
            )
            continue

        tentacle = Tentacle[McuConfig, constants.EnumTentacleType, constants.EnumFut](
            tentacle_serial_number=serial,
            tentacle_spec=tentacle_instance.tentacle_spec,
            hw_version=tentacle_instance.hw_version,
            hub=query_result_tentacle,
        )

        tentacles.append(tentacle)

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
            tentacles=connected_tentacles,
            only_board_variants=args.only_variants,
            flash_skip=self.args.firmware.flash_skip,
        )
        self.test_bartender = TestBartender(
            connected_tentacles=connected_tentacles,
            testrun_specs=testrun_specs,
        )
        self.firmware_bartender = FirmwareBartender(self.test_bartender.testrun_specs)

    def flash(self, last_variant: bool) -> None:
        assert isinstance(last_variant, bool)

        for tentacle in self.test_bartender.connected_tentacles:
            tentacle_spec = tentacle.tentacle_spec
            assert isinstance(tentacle_spec, TentacleSpecMicropython)
            variant = tentacle_spec.get_first_last_variant(last=last_variant)

            tentacle.tentacle_state.firmware_spec = (
                self.args.firmware.get_firmware_spec(
                    board=tentacle_spec.board,
                    variant=variant,
                )
            )
            self.args.firmware.build_firmware(
                tentacle=tentacle,
                mpbuild_artifacts=constants.DIRECTORY_MPBUILD_ARTIFACTS,
            )

            self.ntestrun.function_setup_infa_and_dut(tentacle=tentacle)

    def run_all_in_sequence(
        self,
        process_pool: util_multiprocessing.ProcessPoolAsync,
    ) -> None:
        logging.info(f"Using {process_pool.__class__.__name__}")
        assert self.args.mp_test is not None
        repo_micropython_tests = self.args.mp_test.clone_git_micropython_tests(
            directory_git_cache=constants.DIRECTORY_GIT_CACHE
        )

        while True:
            try:
                testrun = self.test_bartender.testrun_next(
                    firmwares_built=set(self.firmware_bartender.firmwares_built)
                )
                #
                # Run test
                #
                self.run_one_test(
                    testrun=testrun,
                    repo_micropython_tests=repo_micropython_tests,
                    process_pool=process_pool,
                )
            except CurrentlyNoTestsException:
                logger.debug(
                    "CurrentlyNoTestsException: Wait for firmware to be built or tentacles to be freed!"
                )

            except AllTestsDoneException:
                logging.info("All tests done")
                assert len(self.test_bartender.actual_testruns) == 0
                process_pool.write_report_tasks(constants.DIRECTORY_TESTRESULTS)
                break

            async_result = self.firmware_bartender.testrun_next(
                repo_micropython_firmware=self.args.firmware.repo_micropython_firmware
            )
            if async_result is not None:
                process_pool.apply_async(
                    async_result=async_result, bartender=self.firmware_bartender
                )

            for result in process_pool.get_results():
                if isinstance(result, AsyncResultTest):
                    result.done(bartender=self.test_bartender)
                    continue
                if isinstance(result, AsyncResultFirmware):
                    result.done(bartender=self.firmware_bartender)
                    continue
                raise ValueError(f"Unexected result {result!r}")

            time.sleep(0.5)

        process_pool.close_and_join()

        self.ntestrun.session_teardown()

    def run_one_test(
        self,
        testrun: TestRun,
        repo_micropython_tests: pathlib.Path,
        process_pool: util_multiprocessing.ProcessPoolAsync,
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
        assert isinstance(process_pool, util_multiprocessing.ProcessPoolSync)
        assert len(testrun.list_tentacle_variant) > 0

        logger.debug(testrun.testid)

        self._assign_firmware_specs(testrun=testrun)

        async_result = AsyncResultTest(
            args=self.args,
            ntestrun=self.ntestrun,
            testrun=testrun,
            repo_micropython_tests=repo_micropython_tests,
        )
        process_pool.apply_async(
            async_result=async_result, bartender=self.test_bartender
        )

    def _assign_firmware_specs(self, testrun: TestRun) -> None:
        # Assign firmware_spec to each tentacle
        for tentacle_variant in testrun.list_tentacle_variant:
            tentacle = tentacle_variant.tentacle
            tentacle_spec = tentacle.tentacle_spec
            assert isinstance(tentacle_spec, TentacleSpecMicropython)
            tentacle.tentacle_state.firmware_spec = (
                self.args.firmware.get_firmware_spec(
                    board=tentacle_spec.board,
                    variant=tentacle_variant.variant,
                )
            )


def run_one_test_async(
    args: Args,
    ntestrun: NTestRun,
    testrun: TestRun,
    repo_micropython_tests: pathlib.Path,
) -> None:
    """
    This is a 'global' method and as such may be used within process or
    be called by the multiprocessing module.
    """

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

            for tentacle in testrun.tentacles:
                args.firmware.build_firmware(
                    tentacle=tentacle,
                    mpbuild_artifacts=constants.DIRECTORY_MPBUILD_ARTIFACTS,
                )
                ntestrun.function_prepare_dut(tentacle=tentacle)
                ntestrun.function_setup_infra(tentacle=tentacle)
                ntestrun.function_setup_dut_flash(
                    tentacle=tentacle,
                    flash_skip=args.firmware.flash_skip,
                )

            ntestrun.setup_relays(
                futs=(testrun.testrun_spec.required_fut,),
                tentacles=testrun.tentacles,
            )
            logger.info(
                f"TEST BEGIN {duration_text()} {testresults_directory.test_nodeid}"
            )

            try:
                with testrun.active_led_on:
                    testrun.test(
                        testargs=TestArgs(
                            testresults_directory=testresults_directory,
                            repo_micropython_tests=repo_micropython_tests,
                        )
                    )
                logger.warning("Test SUCCESS")

            except SubprocessExitCodeException as e:
                logger.warning(f"Test returned exit code: {e!r}")
            except Exception as e:
                logger.warning(f"Test failed: {e}")
                logger.exception(e)

        except OctoprobeException as e:
            msg = f"Test failed: {e}"
            logger.error(msg)
            logger.debug(msg, exc_info=True)
        except Exception as e:
            logger.warning(f"Exception during test: {e!r}")
            logger.exception(e)
        finally:
            logger.info(
                f"TEST TEARDOWN {duration_text()} {testresults_directory.test_nodeid}"
            )
            try:
                ntestrun.function_teardown(active_tentacles=testrun.tentacles)
            except Exception as e:
                logger.exception(e)
            logger.info(
                f"TEST END {duration_text()} {testresults_directory.test_nodeid}"
            )
