from __future__ import annotations

import logging
import sys

from octoprobe.util_subprocess import subprocess_run

from testbed.testcollection.baseclasses_spec import TentacleVariant
from testbed.testcollection.testrun_specs import TestArgs, TestRun, TestRunSpec
from testbed.testrunner.util_testrunspec import mip_install

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
            *self.testrun_spec.subprocess_args,
            f"-t=port:{serial_port}",
            # f"--target={target}",
            "--jobs=1",
            f"--result-dir={testargs.testresults_directory.directory_test}",
            # "misc/cexample_class.py",
        ]
        subprocess_run(
            args=args,
            cwd=testargs.git_micropython_tests / "tests",
            # logfile=testresults_directory(f"run-tests-{test_dir}.txt").filename,
            logfile=testargs.testresults_directory("run-tests.txt").filename,
            timeout_s=60.0,
        )


TESTRUNSPEC_RUNTESTS_EXTMOD_HARDWARE = TestRunSpec(
    subprocess_args=["run-tests.py", "--test-dirs=extmod_hardware"],
    tentacles_required=1,
    testrun_class=TestRunRunTests,
)


TESTRUNSPEC_RUNTESTS_MISC = TestRunSpec(
    subprocess_args=["run-tests.py", "--test-dirs=misc"],
    tentacles_required=1,
    testrun_class=TestRunRunTests,
)
