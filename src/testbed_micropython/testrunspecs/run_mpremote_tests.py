from __future__ import annotations

import json
import logging
import pathlib
import re

from octoprobe.util_baseclasses import OctoprobeTestException

from ..constants import EnumFut
from ..testcollection.baseclasses_spec import TentacleVariant
from ..testcollection.constants import (
    ENV_PYTHONUNBUFFERED,
    TIMEOUT_FLASH_S,
)
from ..testcollection.testrun_specs import (
    TestArgs,
    TestRun,
    TestRunSpec,
)
from ..util_multiprocessing import EVENTLOGCALLBACK
from ..util_subprocess_tentacle import tentacle_subprocess_run

logger = logging.getLogger(__file__)

MPREMOTE_TESTS_SUBDIR = "tools/mpremote/tests"
"""
Directory (relative to the micropython repo) which contains 'run-mpremote-tests.sh'.
"""

MPREMOTE_TESTS_COMMAND = "run-mpremote-tests.sh"

_RE_RESULT = re.compile(r"^(?P<name>\S+\.sh):\s+(?P<result>OK|FAIL|CRASH|skip)$")
"""
Matches the per-test result lines emitted by 'run-mpremote-tests.sh'.

Example:
./test_filesystem.sh: OK
./test_run.sh: FAIL
"""

_RESULT_TO_OUTCOME = {
    "OK": "pass",
    "FAIL": "fail",
    "CRASH": "fail",
    "skip": "skip",
}


class TestRunMpremoteTests(TestRun):
    """
    This test runs: tools/mpremote/tests/run-mpremote-tests.sh

    https://github.com/micropython/micropython/blob/master/tools/mpremote/tests/README.md
    https://github.com/micropython/micropython/blob/master/tools/mpremote/tests/run-mpremote-tests.sh
    """

    def test(self, testargs: TestArgs) -> None:
        tentacle_variant = self.tentacle_variant
        assert isinstance(tentacle_variant, TentacleVariant)

        tentacle = tentacle_variant.tentacle
        tentacle_spec = tentacle.tentacle_spec
        assert tentacle_spec.mcu_config is not None

        self.skip_if_no_filesystem()

        serial_port = tentacle.dut.get_tty()

        # Run tests
        logfile = testargs.testresults_directory("testresults.txt").filename
        EVENTLOGCALLBACK.log(
            msg=f"Logfile: {testargs.testresults_directory.render_relative(logfile)}"
        )
        args = [
            f"./{self.testrun_spec.command_executable}",
            *self.testrun_spec.command_args,
            "-t",
            serial_port,
        ]
        tentacle_subprocess_run(
            args=args,
            cwd=testargs.repo_micropython_tests / self.testrun_spec.command_subdir,
            testrun=self,
            env=ENV_PYTHONUNBUFFERED,
            logfile=logfile,
            timeout_s=self.timeout_s,
        )

        self._evaluate_results(testargs=testargs, logfile=logfile)

    def _evaluate_results(self, testargs: TestArgs, logfile: pathlib.Path) -> None:
        """
        'run-mpremote-tests.sh' reports per-test 'OK'/'FAIL'/'CRASH'/'skip' on
        stdout and always exits with returncode 0.

        We parse the output to build '_results.json' (so the outcomes appear in
        the report) and raise an exception if any test failed or crashed.
        """
        results: list[list[str]] = []
        failures: list[str] = []
        for line in logfile.read_text(errors="replace").splitlines():
            match = _RE_RESULT.match(line.strip())
            if match is None:
                continue
            name = match.group("name")
            result = match.group("result")
            outcome = _RESULT_TO_OUTCOME[result]
            results.append([name, outcome, "" if outcome != "fail" else result])
            if outcome == "fail":
                failures.append(f"{name}: {result}")

        filename_results = (
            testargs.testresults_directory.directory_test / "_results.json"
        )
        filename_results.write_text(json.dumps({"args": {}, "results": results}))

        if failures:
            raise OctoprobeTestException(
                f"mpremote tests failed: {', '.join(failures)}"
            )


TESTRUNSPEC_RUN_MPREMOTE_TESTS = TestRunSpec(
    label="RUN-MPREMOTE_TESTS",
    label_intuitive="run-mpremote-tests.sh",
    label_order="c_h",
    helptext="Run the mpremote test suite",
    command=[MPREMOTE_TESTS_COMMAND],
    command_subdir=MPREMOTE_TESTS_SUBDIR,
    required_fut=EnumFut.FUT_MCU_ONLY,
    requires_reference_tentacle=False,
    testrun_class=TestRunMpremoteTests,
    timeout_s=5 * 60.0 + TIMEOUT_FLASH_S,
)
