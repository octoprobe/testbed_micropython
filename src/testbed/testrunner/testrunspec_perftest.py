from __future__ import annotations

import sys

from octoprobe.util_subprocess import subprocess_run

from testbed.testcollection.baseclasses_spec import TentacleVariant
from testbed.testcollection.testrun_specs import TestArgs, TestRun
from testbed.testrunner.testrunspec_runtests import TestRunSpec


class TestRunPerfTest(TestRun):
    """
    This tests runs: run-perfbench.py

    * https://github.com/micropython/micropython/blob/master/tests/README.md
    * https://github.com/micropython/micropython/blob/master/tests/run-perfbench.py
    """

    def test(self, testargs: TestArgs) -> None:
        assert len(self.list_tentacle_variant) == 1
        tentacle_variant = self.list_tentacle_variant[0]
        assert isinstance(tentacle_variant, TentacleVariant)
        tentacle = tentacle_variant.tentacle
        tentacle_spec = tentacle.tentacle_spec
        assert tentacle_spec.mcu_config is not None
        perftest_args = tentacle_spec.mcu_config.micropython_perftest_args

        if perftest_args is None:
            perftest_args = ["100", "100"]

        args = [
            sys.executable,
            *self.testrun_spec.subprocess_args,
            "--pyboard",
            f"--device={tentacle.dut.get_tty()}",
            *perftest_args,
        ]
        subprocess_run(
            args=args,
            cwd=testargs.git_micropython_tests / "tests",
            logfile=testargs.testresults_directory("run-perfbench.txt").filename,
            timeout_s=300.0,
        )


TESTRUNSPEC_PERFTEST = TestRunSpec(
    subprocess_args=["run-perfbench.py"],
    tentacles_required=1,
    testrun_class=TestRunPerfTest,
)
