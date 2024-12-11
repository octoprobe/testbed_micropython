from __future__ import annotations

import logging
import sys

from octoprobe.util_subprocess import subprocess_run

from testbed.testcollection.baseclasses_spec import TentacleVariant
from testbed.testcollection.testrun_specs import TestArgs, TestRun, TestRunSpec

logger = logging.getLogger(__file__)


class TestRunWlan(TestRun):
    """
    This tests runs: wlan
    """

    def test(self, testargs: TestArgs) -> None:
        assert len(self.list_tentacle_variant) == 2
        tentacle_variant_first = self.list_tentacle_variant[0]
        tentacle_variant_second = self.list_tentacle_variant[1]
        assert isinstance(tentacle_variant_first, TentacleVariant)
        assert isinstance(tentacle_variant_second, TentacleVariant)
        tentacle_first = tentacle_variant_first.tentacle
        tentacle_second = tentacle_variant_second.tentacle
        tentacle_spec_first = tentacle_first.tentacle_spec
        tentacle_spec_second = tentacle_second.tentacle_spec
        assert tentacle_spec_first.mcu_config is not None
        assert tentacle_spec_second.mcu_config is not None

        serial_port_first = tentacle_first.dut.get_tty()
        serial_port_second = tentacle_second.dut.get_tty()

        # Run tests
        args = [
            sys.executable,
            *self.testrun_spec.subprocess_args,
            f"-t=port:{serial_port_first}",
            # f"--target={target}",
            "--jobs=1",
            f"--result-dir={testargs.testresults_directory.directory_test}",
            # "misc/cexample_class.py",
        ]
        subprocess_run(
            args=args,
            cwd=testargs.git_micropython_tests / "tests",
            # logfile=testresults_directory(f"run-tests-{test_dir}.txt").filename,
            logfile=testargs.testresults_directory("run-tests-wlan.txt").filename,
            timeout_s=60.0,
        )


TESTRUNSPEC_RUNTESTS_WLAN = TestRunSpec(
    subprocess_args=["run-tests.py", "--test-dirs=extmod_hardware"],
    tentacles_required=2,
    testrun_class=TestRunWlan,
)
