from __future__ import annotations

import logging
import sys

from octoprobe.util_subprocess import subprocess_run

from testbed.constants import EnumFut
from testbed.mptest.util_common import mip_install
from testbed.testcollection.baseclasses_spec import TentacleVariant
from testbed.testcollection.testrun_specs import (
    TIMEOUT_FLASH_S,
    TestArgs,
    TestRun,
    TestRunSpec,
)

logger = logging.getLogger(__file__)


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
        tentacle = tentacle_variant.tentacle
        tentacle_spec = tentacle.tentacle_spec
        assert tentacle_spec.mcu_config is not None

        serial_port = tentacle.dut.get_tty()

        # Install mip
        mip_install(
            testargs=testargs,
            tentacle=tentacle,
            serial_port=serial_port,
            mip_package="unittest",
        )

        # Run tests
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
            cwd=testargs.repo_micropython_tests / "tests",
            # logfile=testresults_directory(f"run-tests-{test_dir}.txt").filename,
            logfile=testargs.testresults_directory("testresults.txt").filename,
            timeout_s=self.timeout_s,
        )


TESTRUNSPEC_RUNTESTS_EXTMOD_HARDWARE = TestRunSpec(
    label="RUN-TESTS_EXTMOD_HARDWARE",
    helptext="On each board, do test on a gpio feedback loop",
    command=["run-tests.py", "--test-dirs=extmod_hardware"],
    required_fut=EnumFut.FUT_EXTMOD_HARDWARE,
    required_tentacles_count=1,
    testrun_class=TestRunRunTests,
    timeout_s=30.0 + TIMEOUT_FLASH_S,
)


TESTRUNSPEC_RUNTESTS_BASICS = TestRunSpec(
    label="RUN-TESTS_BASICS",
    helptext="On each board, do some basic python language tests",
    # TODO: Allow overwrite by command line
    command=["run-tests.py"],
    required_fut=EnumFut.FUT_MCU_ONLY,
    required_tentacles_count=1,
    testrun_class=TestRunRunTests,
    timeout_s=5 * 60.0 + TIMEOUT_FLASH_S,
)
