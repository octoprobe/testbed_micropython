from __future__ import annotations

import sys

from octoprobe.util_subprocess import subprocess_run

from testbed.constants import EnumFut
from testbed.testcollection.baseclasses_spec import TentacleVariant
from testbed.testcollection.testrun_specs import TIMEOUT_FLASH_S, TestArgs, TestRun
from testbed.testrunspecs.runtests import TestRunSpec


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
        assert len(perftest_args) == 2
        assert isinstance(perftest_args[0], str)
        assert isinstance(perftest_args[1], str)

        args = [
            sys.executable,
            *self.testrun_spec.command,
            "--pyboard",
            f"--device={tentacle.dut.get_tty()}",
            *perftest_args,
        ]
        subprocess_run(
            args=args,
            cwd=testargs.repo_micropython_tests / "tests",
            logfile=testargs.testresults_directory("testresults.txt").filename,
            timeout_s=self.timeout_s,
        )


TESTRUNSPEC_PERFTEST = TestRunSpec(
    label="RUN-PERFBENCH",
    helptext="Run pertest on each board",
    command=["run-perfbench.py"],
    required_fut=EnumFut.FUT_EXTMOD_HARDWARE,
    required_tentacles_count=1,
    testrun_class=TestRunPerfTest,
    timeout_s=4 * 60.0 + TIMEOUT_FLASH_S,
)
