from __future__ import annotations

import sys

from octoprobe.util_subprocess import subprocess_run

from ..constants import EnumFut
from ..testcollection.baseclasses_spec import TentacleVariant
from ..testcollection.constants import (
    ENV_MICROPYTHON_TESTS,
    MICROPYTHON_DIRECTORY_TESTS,
    TIMEOUT_FLASH_S,
)
from ..testcollection.testrun_specs import (
    TestArgs,
    TestRun,
)
from ..testrunspecs.runtests import TestRunSpec
from ..util_multiprocessing import EVENTLOGCALLBACK


class TestRunPerfTest(TestRun):
    """
    This tests runs: run-perfbench.py

    * https://github.com/micropython/micropython/blob/master/tests/README.md
    * https://github.com/micropython/micropython/blob/master/tests/run-perfbench.py
    """

    def test(self, testargs: TestArgs) -> None:
        assert len(self.tentacle_variant) == 1
        tentacle_variant = self.tentacle_variant[0]
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

        logfile = testargs.testresults_directory("testresults.txt").filename
        EVENTLOGCALLBACK.log(
            msg=f"Logfile: {testargs.testresults_directory.render_relative(logfile)}"
        )
        args = [
            sys.executable,
            *self.testrun_spec.command,
            f"--result-dir={testargs.testresults_directory.directory_test}",
            "--pyboard",
            f"--device={tentacle.dut.get_tty()}",
            *perftest_args,
        ]
        subprocess_run(
            args=args,
            cwd=testargs.repo_micropython_tests / MICROPYTHON_DIRECTORY_TESTS,
            env=ENV_MICROPYTHON_TESTS,
            logfile=logfile,
            timeout_s=self.timeout_s,
        )


TESTRUNSPEC_PERFTEST = TestRunSpec(
    label="RUN-PERFBENCH",
    helptext="Run pertest on each board",
    command=["run-perfbench.py"],
    required_fut=EnumFut.FUT_EXTMOD_HARDWARE,
    requires_reference_tentacle=False,
    testrun_class=TestRunPerfTest,
    # TODO(hans): 2025-07-30: Lower von 10 to 4
    timeout_s=10 * 60.0 + TIMEOUT_FLASH_S,
)
