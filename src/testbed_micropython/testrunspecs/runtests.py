from __future__ import annotations

import logging
import pathlib
import re
import sys

from octoprobe.util_baseclasses import OctoprobeTestSkipException
from octoprobe.util_subprocess import subprocess_run

from ..constants import EnumFut
from ..mptest.util_common import mip_install, skip_if_no_filesystem
from ..multiprocessing.util_multiprocessing import EVENTLOGCALLBACK
from ..testcollection.baseclasses_spec import TentacleVariant
from ..testcollection.testrun_specs import (
    MICROPYTHON_DIRECTORY_TESTS,
    TIMEOUT_FLASH_S,
    TestArgs,
    TestRun,
    TestRunSpec,
)

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
        assert len(self.list_tentacle_variant) == 1
        tentacle_variant = self.list_tentacle_variant[0]
        assert isinstance(tentacle_variant, TentacleVariant)

        for mocked_error in _LIST_MOCKED_ERRORS:
            if re.match(mocked_error, self.testid):
                logger.error(f"Test ID matches '{mocked_error}")
                raise ValueError(f"Mocked error for testid='{mocked_error}'")

        tentacle = tentacle_variant.tentacle
        tentacle_spec = tentacle.tentacle_spec
        assert tentacle_spec.mcu_config is not None

        skip_if_no_filesystem(tentacle=tentacle)

        def env_for_mpycross() -> dict[str, str]:
            if "--via-mpy" not in self.testrun_spec.command_args:
                return {}

            tentacle_state = tentacle.tentacle_state

            def firmware_not_build() -> bool:
                if not tentacle_state.has_firmware_spec:
                    return True
                if not tentacle_state.firmware_spec.do_flash:
                    return True
                return False

            if firmware_not_build():
                raise OctoprobeTestSkipException(
                    "It looks like the firmware has not been compiled, but the test requires '--via-mpy'!"
                )

            def mpycross_filename() -> pathlib.Path:
                """
                We know the filename of the firmware and start here to find mpy-cross.
                However, it would be a cleaner solutions to start from the firmware-repo top!
                """
                firmware_filename = tentacle_state.firmware_spec.filename
                # firmware_filename: <micropython>/ports/rp2/build-RPI_PICO/firmware.uf2
                mpy_cross_filename = firmware_filename.parent
                while mpy_cross_filename.name != "ports":
                    mpy_cross_filename = mpy_cross_filename.parent
                # mpy_cross_filename: <micropython>/ports/
                mpy_cross_filename = (
                    mpy_cross_filename.parent / "mpy-cross" / "build" / "mpy-cross"
                )
                # mpy_cross_filename: <micropython>/mpy-cross/build/mpy-cross
                assert mpy_cross_filename.is_file(), mpy_cross_filename
                return mpy_cross_filename

            return {"MICROPY_MPYCROSS": str(mpycross_filename())}

        serial_port = tentacle.dut.get_tty()

        # Install mip
        mip_install(
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
            f"-t=port:{serial_port}",
            # f"--target={target}",
            "--jobs=1",
            f"--result-dir={testargs.testresults_directory.directory_test}",
            # "misc/cexample_class.py",
        ]
        subprocess_run(
            args=args,
            cwd=testargs.repo_micropython_tests / MICROPYTHON_DIRECTORY_TESTS,
            env=env_for_mpycross(),
            # logfile=testresults_directory(f"run-tests-{test_dir}.txt").filename,
            logfile=logfile,
            timeout_s=self.timeout_s,
            # TODO: Remove the following line as soon returncode of 'run-perfbench.py' is fixed.
            success_returncodes=[0, 1],
        )


TESTRUNSPEC_RUNTESTS_STANDARD = TestRunSpec(
    label="RUN-TESTS_STANDARD",
    helptext="Run the standard set of tests",
    # TODO: Allow overwrite by command line
    command=["run-tests.py"],
    required_fut=EnumFut.FUT_MCU_ONLY,
    required_tentacles_count=1,
    testrun_class=TestRunRunTests,
    timeout_s=10 * 60.0 + TIMEOUT_FLASH_S,
)

TESTRUNSPEC_RUNTESTS_STANDARD_VIA_MPY = TestRunSpec(
    label="RUN-TESTS_STANDARD_VIA_MPY",
    helptext="Run the standard set of tests via .mpy",
    command=["run-tests.py", "--via-mpy"],
    required_fut=EnumFut.FUT_MCU_ONLY,
    required_tentacles_count=1,
    testrun_class=TestRunRunTests,
    timeout_s=10 * 60.0 + TIMEOUT_FLASH_S,
)

TESTRUNSPEC_RUNTESTS_STANDARD_NATIVE = TestRunSpec(
    label="RUN-TESTS_STANDARD_NATIVE",
    helptext="Run the standard set of tests with the native emitter",
    command=["run-tests.py", "--via-mpy", "--emit", "native"],
    required_fut=EnumFut.FUT_MCU_ONLY,
    required_tentacles_count=1,
    testrun_class=TestRunRunTests,
    timeout_s=10 * 60.0 + TIMEOUT_FLASH_S,
)

TESTRUNSPEC_RUNTESTS_EXTMOD_HARDWARE = TestRunSpec(
    label="RUN-TESTS_EXTMOD_HARDWARE",
    helptext="Run hardware specific tests",
    command=["run-tests.py", "--test-dirs=extmod_hardware"],
    required_fut=EnumFut.FUT_EXTMOD_HARDWARE,
    required_tentacles_count=1,
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
    required_tentacles_count=1,
    testrun_class=TestRunRunTests,
    timeout_s=30.0 + TIMEOUT_FLASH_S,
)
