from __future__ import annotations

import logging
import sys

from octoprobe.util_constants import relative_cwd
from octoprobe.util_subprocess import subprocess_run

from ..constants import EnumFut
from ..mptest import util_common
from ..multiprocessing.util_multiprocessing import EVENTLOGCALLBACK
from ..testcollection.baseclasses_spec import TentacleVariant
from ..testcollection.testrun_specs import (
    TIMEOUT_FLASH_S,
    TestArgs,
    TestRun,
    TestRunSpec,
)

logger = logging.getLogger(__file__)

NATMOD_LIBS = ("btree", "deflate", "framebuf", "heapq", "random", "re")


class TestRunRunTests(TestRun):
    """
    This tests runs: run-natmodtests.py

    https://github.com/micropython/micropython/blob/master/tests/README.md
    https://github.com/micropython/micropython/blob/master/tests/run-natmodtests.py
    """

    def test(self, testargs: TestArgs) -> None:
        assert len(self.list_tentacle_variant) == 1
        tentacle_variant = self.list_tentacle_variant[0]
        assert isinstance(tentacle_variant, TentacleVariant)
        tentacle = tentacle_variant.tentacle
        tentacle_spec = tentacle.tentacle_spec
        assert tentacle_spec.mcu_config is not None

        # Work out which tests can be run.
        tests_base_dir = testargs.repo_micropython_tests / "tests"
        tests_extmod_dir = tests_base_dir / "extmod"
        tests_natmod = [
            file.relative_to(tests_base_dir).as_posix()
            for file in tests_extmod_dir.glob("*.py")
            if file.stem.startswith(NATMOD_LIBS)
        ]

        serial_port = tentacle.dut.get_tty()

        # Run tests
        logfile = testargs.testresults_directory("testresults.txt").filename
        EVENTLOGCALLBACK.log(msg=f"Logfile: {relative_cwd(logfile)}")
        args = [
            sys.executable,
            *self.testrun_spec.command,
            f"--result-dir={testargs.testresults_directory.directory_test}",
            "--pyboard",
            f"--device={serial_port}",
        ] + tests_natmod
        subprocess_run(
            args=args,
            cwd=testargs.repo_micropython_tests / "tests",
            env=util_common.ENV_PYTHONUNBUFFERED,
            logfile=logfile,
            timeout_s=self.timeout_s,
            # TODO: Remove the following line as soon returncode of 'run-natmodtests.py' is fixed.
            success_returncodes=[0, 1],
        )


TESTRUNSPEC_RUN_NATMODTESTS = TestRunSpec(
    label="RUN-NATMODTESTS",
    helptext="Run tests using native modules in external .mpy files",
    command=["run-natmodtests.py"],
    required_fut=EnumFut.FUT_MCU_ONLY,
    required_tentacles_count=1,
    testrun_class=TestRunRunTests,
    timeout_s=1 * 60.0 + TIMEOUT_FLASH_S,
)
