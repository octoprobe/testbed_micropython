from __future__ import annotations

import pathlib
import sys

from octoprobe.util_pytest.util_resultdir import ResultsDir
from octoprobe.util_subprocess import subprocess_run

from testbed.testcollection.baseclasses_spec import TentacleVariant
from testbed.testcollection.testrun_specs import TestRun


class TestRunPerfTest(TestRun):
    """
    This tests runs: run-perfbench.py

    * https://github.com/micropython/micropython/blob/master/tests/README.md
    * https://github.com/micropython/micropython/blob/master/tests/run-perfbench.py
    """

    def test(
        self,
        testresults_directory: ResultsDir,
        git_micropython_tests: pathlib.Path,
    ) -> None:
        """
        This tests runs: run-perfbench.py

        * https://github.com/micropython/micropython/blob/master/tests/README.md
        * https://github.com/micropython/micropython/blob/master/tests/run-perfbench.py
        """
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
            cwd=git_micropython_tests / "tests",
            logfile=testresults_directory("run-perfbench.txt").filename,
            timeout_s=300.0,
        )


class TestRunRunTests(TestRun):
    """
    This tests runs: run-tests.py
    https://github.com/micropython/micropython/blob/master/tests/README.md
    https://github.com/micropython/micropython/blob/master/tests/run-tests.py
    """

    def test(
        self,
        testresults_directory: ResultsDir,
        git_micropython_tests: pathlib.Path,
    ) -> None:
        """
        This tests runs: run-perfbench.py

        * https://github.com/micropython/micropython/blob/master/tests/README.md
        * https://github.com/micropython/micropython/blob/master/tests/run-perfbench.py
        """
        assert len(self.list_tentacle_variant) == 1
        tentacle_variant = self.list_tentacle_variant[0]
        assert isinstance(tentacle_variant, TentacleVariant)
        tentacle = tentacle_variant.tentacle
        tentacle_spec = tentacle.tentacle_spec
        assert tentacle_spec.mcu_config is not None

        args = [
            sys.executable,
            *self.testrun_spec.subprocess_args,
            f"-t=port:{tentacle.dut.get_tty()}",
            # f"--target={target}",
            "--jobs=1",
            f"--result-dir={testresults_directory.directory_test}",
            # "misc/cexample_class.py",
        ]
        subprocess_run(
            args=args,
            cwd=git_micropython_tests / "tests",
            # logfile=testresults_directory(f"run-tests-{test_dir}.txt").filename,
            logfile=testresults_directory("run-tests.txt").filename,
            timeout_s=60.0,
        )
