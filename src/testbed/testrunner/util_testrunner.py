from __future__ import annotations

import dataclasses
import itertools
import logging
import pathlib
import shutil
import sys
import time

from octoprobe.lib_tentacle import Tentacle
from octoprobe.lib_testbed import Testbed
from octoprobe.octoprobe import NTestRun
from octoprobe.util_dut_programmers import FirmwareSpecBase
from octoprobe.util_pytest import util_logging
from octoprobe.util_pytest.util_resultdir import ResultsDir
from octoprobe.util_testbed_lock import TestbedLock
from octoprobe.util_usb_serial import QueryResultTentacles
from tests.micropython_repo.test_run import subprocess_run, un_monkey_patch

from testbed.constants import (
    DIRECTORY_GIT_CACHE,
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
from testbed.testcollection.baseclasses_run import TestRunSpecs
from testbed.testcollection.baseclasses_spec import (
    ConnectedTentacles,
)
from testbed.testcollection.testrun_specs import TestRun, TestRunSpec
from testbed.util_firmware_mpbuild import CachedGitRepo, collect_firmware_specs
from testbed.util_github_micropython_org import PYTEST_OPT_DIR_MICROPYTHON_TESTS

logger = logging.getLogger(__file__)

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent


_TESTBED_LOCK = TestbedLock()


@dataclasses.dataclass
class Args:
    micropython_tests_git: str | None
    micropython_tests: str | None
    firmware_build_git: str | None
    firmware_build: str | None
    only_boards: list[str] | None


def clone_git_micropython_tests(args: Args) -> pathlib.Path:
    """
    We have to clone the micropython git repo and use the tests from the subfolder "test".
    """
    # directory = request.config.getoption(PYTEST_OPT_DIR_MICROPYTHON_TESTS)
    if args.micropython_tests is not None:
        _directory = pathlib.Path(args.micropython_tests).expanduser().resolve()
        if not _directory.is_dir():
            raise ValueError(
                f"pytest parameter '{PYTEST_OPT_DIR_MICROPYTHON_TESTS}': Directory does not exist: {_directory}"
            )
        return _directory

    # git_spec = request.config.getoption(PYTEST_OPT_GIT_MICROPYTHON_TESTS)
    # if git_spec is None:
    if args.micropython_tests_git is None:
        raise ValueError(
            "MicroPython repo not cloned - argument '{PYTEST_OPT_GIT_MICROPYTHON_TESTS}'not given to pytest !"
        )

    git_repo = CachedGitRepo(
        directory_cache=DIRECTORY_GIT_CACHE,
        git_spec=args.micropython_tests_git,
        prefix="micropython_tests_",
    )
    git_repo.clone()

    # Avoid hanger in run-perfbench.py/run-tests.py
    un_monkey_patch()

    return git_repo.directory


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


def setup_tentacles(
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
            ntest_run.function_build_firmwares(
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

            test_perf_bench(
                testrun=testrun,
                mcu=testrun.tentacles[0],
                testresults_directory=testresults_directory,
            )

        except Exception as e:
            logger.warning(f"Exception during test: {e!r}")
            logger.exception(e)
            raise
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

    _testbed = Testbed(
        workspace="based-on-connected-boards",
        tentacles=connected_tentacles,
    )

    _testrun = NTestRun(
        testbed=_testbed,
        firmware_git_url=args.firmware_build_git,
    )

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

    git_micropython_tests = clone_git_micropython_tests(args=args)
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

            def get_firmware_spec(tentacle: Tentacle) -> FirmwareSpecBase:
                """
                Given: arguments to pytest, for example PYTEST_OPT_FIRMWARE.
                Now we create firmware specs.
                In case of PYTEST_OPT_FIRMWARE:
                The firmware has to be downloaded.
                In case of PYTEST_OPT_FIRMWARE-TODO:
                The firmware has to be compiled.
                If nothing is specified, we do not flash any firmware: Return None
                """
                assert isinstance(tentacle, Tentacle)

                if args.firmware_build_git is not None:
                    #
                    # Collect firmware specs by connected tentacles
                    #
                    specs = collect_firmware_specs(tentacles=[tentacle])
                    return specs[0]

                firmware_download_json = config.getoption(PYTEST_OPT_DOWNLOAD_FIRMWARE)
                if firmware_download_json is not None:
                    #
                    # Donwnload firmware and return the spec
                    #
                    assert firmware_download_json is not None
                    spec = FirmwareDownloadSpec.factory(filename=firmware_download_json)
                    spec.download()
                    return spec

                #
                # Nothing was specified: We do not flash any firmware
                #
                return FirmwareNoFlashingSpec.factory()

            tentacle._firmware_spec = get_firmware_spec(tentacle=tentacle)

        print(testrun.testid)

        # TODO: remove hardcoded EnumFut.FUT_MCU_ONLY
        testresults_directory = ResultsDir(
            directory_top=DIRECTORY_TESTRESULTS,
            test_name=testrun.testid,
            test_nodeid=testrun.testid,
        )
        setup_tentacles(
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
    testrun_spec_container = TestRunSpecs(
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
        testrun_specs=testrun_spec_container,
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
