from __future__ import annotations

import logging
import re
import sys

from octoprobe.util_subprocess import subprocess_run

from testbed_micropython import constants
from testbed_micropython.util_mpycross import get_filename_mpycross

from ..constants import EnumFut
from ..mptest import util_common
from ..testcollection.baseclasses_spec import TentacleSpecVariant
from ..testcollection.constants import (
    ENV_PYTHONUNBUFFERED,
    MICROPYTHON_DIRECTORY_TESTS,
    TIMEOUT_FLASH_S,
)
from ..testcollection.testrun_specs import (
    TestArgs,
    TestRun,
    TestRunSpec,
)
from ..util_multiprocessing import EVENTLOGCALLBACK

logger = logging.getLogger(__file__)

_LIST_MOCKED_ERRORS: list[str] = [
    # r"RUN-TESTS_EXTMOD_HARDWARE@\w+-ESP32_C3_DEVKIT",
]


class TestRunRunTests(TestRun):
    """
    This tests runs: run-tests.py

    https://github.com/micropython/micropython/blob/master/tests/README.md
    https://github.com/micropython/micropython/blob/master/tests/run-tests.py
    """

    def test(self, testargs: TestArgs) -> None:
        if testargs.debug_skip_tests_with_message:
            return

        tentacle_variant = self.tentacle_variant
        assert isinstance(tentacle_variant, TentacleSpecVariant)

        for mocked_error in _LIST_MOCKED_ERRORS:
            if re.match(mocked_error, self.testid):
                logger.error(f"Test ID matches '{mocked_error}")
                raise ValueError(f"Mocked error for testid='{mocked_error}'")

        tentacle = tentacle_variant.tentacle
        tentacle_spec = tentacle.tentacle_spec
        assert tentacle_spec.mcu_config is not None

        def env_for_mpycross() -> dict[str, str]:
            env = ENV_PYTHONUNBUFFERED

            if "--via-mpy" not in self.testrun_spec.command_args:
                return env

            directory_mpbuild_artifacts = (
                testargs.testresults_directory.directory_top
                / constants.SUBDIR_MPBUILD
                / tentacle_variant.board_variant
            )
            filename_mpycross = get_filename_mpycross(
                directory_mpbuild_artifacts=directory_mpbuild_artifacts,
                repo_micropython=testargs.repo_micropython_tests,
            )
            env["MICROPY_MPYCROSS"] = str(filename_mpycross)
            return env

        # LOLIN_D1_MINI 512k: 'unittest' is included frozen into the firmware
        unittest_already_installed = tentacle.dut.mpremote_success("import unittest")
        if not unittest_already_installed:
            self.skip_if_no_filesystem()

        if "native" in self.testrun_spec.command_args:
            self.skip_missing_support_native()

        if "--via-mpy" in self.testrun_spec.command_args:
            self.skip_missing_support_mpy()

        serial_port = tentacle.dut.get_tty()

        # Install mip
        if not unittest_already_installed:
            util_common.mip_install(
                testargs=testargs,
                tentacle=tentacle,
                serial_port=serial_port,
                mip_package="unittest",
            )

        # Run tests
        logfile = testargs.testresults_directory("testresults.txt").filename
        EVENTLOGCALLBACK.log(
            msg=f"Logfile: {testargs.testresults_directory.render_relative(logfile)}"
        )
        args = [
            sys.executable,
            *self.testrun_spec.command,
            f"--result-dir={testargs.testresults_directory.directory_test}",
            f"-t=port:{serial_port}",
            # f"--target={target}",
            "--jobs=1",
            # "misc/cexample_class.py",
        ]
        env = env_for_mpycross()
        subprocess_run(
            args=args,
            cwd=testargs.repo_micropython_tests / MICROPYTHON_DIRECTORY_TESTS,
            env=env,
            # logfile=testresults_directory(f"run-tests-{test_dir}.txt").filename,
            logfile=logfile,
            timeout_s=self.timeout_s,
            # TODO: Remove the following line as soon returncode of 'run-multitest.py' is fixed.
            success_returncodes=[0, 1],
        )


TESTRUNSPEC_RUNTESTS_STANDARD = TestRunSpec(
    label="RUN-TESTS_STANDARD",
    helptext="Run the standard set of tests",
    command=["run-tests.py"],
    required_fut=EnumFut.FUT_MCU_ONLY,
    requires_reference_tentacle=False,
    testrun_class=TestRunRunTests,
    timeout_s=60 * 60.0 + TIMEOUT_FLASH_S,
)

TESTRUNSPEC_RUNTESTS_STANDARD_VIA_MPY = TestRunSpec(
    label="RUN-TESTS_STANDARD_VIA_MPY",
    helptext="Run the standard set of tests via .mpy",
    command=["run-tests.py", "--via-mpy"],
    required_fut=EnumFut.FUT_MCU_ONLY,
    requires_reference_tentacle=False,
    testrun_class=TestRunRunTests,
    timeout_s=60 * 60.0 + TIMEOUT_FLASH_S,
)

TESTRUNSPEC_RUNTESTS_STANDARD_NATIVE = TestRunSpec(
    label="RUN-TESTS_STANDARD_NATIVE",
    helptext="Run the standard set of tests with the native emitter",
    command=["run-tests.py", "--via-mpy", "--emit", "native"],
    required_fut=EnumFut.FUT_MCU_ONLY,
    requires_reference_tentacle=False,
    testrun_class=TestRunRunTests,
    timeout_s=60 * 60.0 + TIMEOUT_FLASH_S,
)

TESTRUNSPEC_RUNTESTS_EXTMOD_HARDWARE = TestRunSpec(
    label="RUN-TESTS_EXTMOD_HARDWARE",
    helptext="Run hardware specific tests",
    command=["run-tests.py", "--test-dirs=extmod_hardware"],
    required_fut=EnumFut.FUT_EXTMOD_HARDWARE,
    requires_reference_tentacle=False,
    testrun_class=TestRunRunTests,
    timeout_s=30.0 + TIMEOUT_FLASH_S,
)

TESTRUNSPEC_RUNTESTS_EXTMOD_HARDWARE_NATIVE = TestRunSpec(
    label="RUN-TESTS_EXTMOD_HARDWARE_NATIVE",
    helptext="Run hardware specific tests with the native emitter",
    command=[
        "run-tests.py",
        "--via-mpy",
        "--emit",
        "native",
        "--test-dirs=extmod_hardware",
    ],
    required_fut=EnumFut.FUT_EXTMOD_HARDWARE,
    requires_reference_tentacle=False,
    testrun_class=TestRunRunTests,
    timeout_s=30.0 + TIMEOUT_FLASH_S,
)
