from __future__ import annotations

import logging
import pathlib
import sys
import tempfile

from octoprobe.util_subprocess import (
    SubprocessExitCodeException,
    extract_test_output,
)

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
from .util_mp_results import MpResults

logger = logging.getLogger(__file__)


MPREMOTE_TESTS_SUBDIR = "tools/mpremote/tests"
"""
Directory (relative to the micropython repo) which contains 'run-mpremote-tests.sh'.
"""

MPREMOTE_TESTS_COMMAND = "run-mpremote-tests.sh"


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

        directory_mpremote_tests = (
            testargs.repo_micropython_tests / MPREMOTE_TESTS_SUBDIR
        )
        assert directory_mpremote_tests.is_dir()
        assert (directory_mpremote_tests / MPREMOTE_TESTS_COMMAND).is_file()
        mp_remote_py = directory_mpremote_tests.parent / "mpremote.py"
        assert mp_remote_py.is_file()

        # Run tests
        logfile = testargs.testresults_directory("testresults.txt").filename
        EVENTLOGCALLBACK.log(
            msg=f"Logfile: {testargs.testresults_directory.render_relative(logfile)}"
        )

        def run_tests() -> None:
            """
            This method mimics MPREMOTE_TESTS_COMMAND = "run-mpremote-tests.sh"
            """

            def run_test(test_sh: pathlib.Path) -> None:
                logger.info(f"Test: {test_sh.name}")

                filename_expected = test_sh.with_suffix(".sh.exp")
                testoutput_expected = filename_expected.read_text()

                logfile_raw_out = logfile.with_stem(test_sh.stem).with_suffix(".txt")
                with tempfile.TemporaryDirectory() as tmp_dir:
                    env = {
                        "MPREMOTE": f"{sys.executable} {mp_remote_py} connect {serial_port}",
                        "TMP": str(tmp_dir),
                        **ENV_PYTHONUNBUFFERED,
                    }
                    try:
                        tentacle_subprocess_run(
                            args=[str(test_sh)],
                            cwd=test_sh.parent,
                            testrun=self,
                            env=env,
                            logfile=logfile_raw_out,
                            timeout_s=self.timeout_s,
                        )
                    except SubprocessExitCodeException:
                        mp_results.add_fail(
                            test_sh.name, f"{test_sh.name} returned with an error!"
                        )
                        return

                testoutput = extract_test_output(logfile=logfile_raw_out)
                testoutput = testoutput.replace(str(tmp_dir), "${TMP}")

                if "SKIP" in testoutput:
                    mp_results.add_skip(test_sh.name)
                    return

                if testoutput == testoutput_expected:
                    # OK: Output matches expected output
                    mp_results.add_pass(test_sh.name)
                    return

                mp_results.add_fail(test_sh.name, "testoutput differs")
                logfile_raw_out.with_suffix(".sh.out").write_text(testoutput)
                # In case of failure, we write the effective output AND the expected output
                logfile_raw_out.with_name(filename_expected.name).write_text(
                    testoutput_expected
                )

            # for test_sh in directory_mpremote_tests.glob("test_filesystem.sh"):
            for test_sh in directory_mpremote_tests.glob("test_*.sh"):
                run_test(test_sh)

        mp_results = MpResults()
        run_tests()
        mp_results.save_results(directory=logfile.parent)


TESTRUNSPEC_RUN_MPREMOTE_TESTS = TestRunSpec(
    label="RUN-MPREMOTE_TESTS",
    label_intuitive="run-mpremote-tests.sh",
    label_order="c_h",
    helptext="Run the mpremote test suite",
    command=[MPREMOTE_TESTS_COMMAND],
    required_fut=EnumFut.FUT_MCU_ONLY,
    requires_reference_tentacle=False,
    testrun_class=TestRunMpremoteTests,
    timeout_s=5 * 60.0 + TIMEOUT_FLASH_S,
)
