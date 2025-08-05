"""
Ths module was copied from run_multinet.py.

There is the DUT and a reference PICO.

The reference PICO may be
* a PICO board (calling run-multitests.py from the command line)
* the PICO-infra on the tentacle (when running from octoprobe)

Side effect:
As the PICO-infra is used by octoprobe, there will only one powercycle at the start of the whole testrun.
Between the tests, the PICO-infra will NOT be powercycled.

This requires, that the tests should NOT break the PICO-infra NOR leave state like interupt handlers, pull up resisters etc. behind.

This may probably be accomplished by doing a soft- or hard-reset after every test.

The tests require
* A FUT to be set. For example `EnumFut.FUT_I2C_EXTERNAL`
* Electrical connections corresponding this FUT. These connections are specified in `src/testbed_micropython/tentacle_specs.py`
"""

from __future__ import annotations

import logging
import sys

from octoprobe.util_subprocess import subprocess_run

from ..constants import EnumFut
from ..tentacle_spec import TentacleMicropython
from ..testcollection.constants import (
    ENV_MICROPYTHON_TESTS,
    MICROPYTHON_DIRECTORY_TESTS,
    TIMEOUT_FLASH_S,
)
from ..testcollection.testrun_specs import (
    TestArgs,
    TestRun,
    TestRunSpec,
)
from ..util_multiprocessing import EVENTLOGCALLBACK

logger = logging.getLogger(__file__)


class TestRunMultiI2cExternal(TestRun):
    def test(self, testargs: TestArgs) -> None:
        tentacle = self.tentacle_variant.tentacle
        assert isinstance(tentacle, TentacleMicropython)

        file_pattern = self.testrun_spec.command[1]
        assert isinstance(file_pattern, str)
        assert file_pattern != ""

        with tentacle.infra.borrow_tty() as serial_port_infra:
            serial_port_dut = tentacle.dut.get_tty()
            print(f"Go for it! {serial_port_dut} {serial_port_infra}")

            # Run tests
            cwd = testargs.repo_micropython_tests / MICROPYTHON_DIRECTORY_TESTS
            list_tests = [str(f.relative_to(cwd)) for f in cwd.glob(file_pattern)]
            logfile = testargs.testresults_directory("testresults.txt").filename
            EVENTLOGCALLBACK.log(
                msg=f"Logfile: {testargs.testresults_directory.render_relative(logfile)}"
            )
            args = [
                sys.executable,
                self.testrun_spec.command_executable,
                f"--result-dir={testargs.testresults_directory.directory_test}",
                f"--instance=pyb:{serial_port_dut}",
                f"--instance=pyb:{serial_port_infra}",
                *list_tests,
            ]
            subprocess_run(
                args=args,
                cwd=cwd,
                env=ENV_MICROPYTHON_TESTS,
                # logfile=testresults_directory(f"run-tests-{test_dir}.txt").filename,
                logfile=logfile,
                timeout_s=self.timeout_s,
                # TODO: Remove the following line as soon returncode of 'run-multitest.py' is fixed.
                success_returncodes=[0, 1],
            )


TESTRUNSPEC_RUNTESTS_MULTI2C = TestRunSpec(
    label="RUN-MULTITESTS_I2C_EXTERNAL",
    helptext="See https://github.com/octoprobe/testbed_micropython/issues/57",
    command=["run-multitests.py", "multi_i2c/*.py"],
    required_fut=EnumFut.FUT_I2C_EXTERNAL,
    requires_reference_infra_pico=True,
    testrun_class=TestRunMultiI2cExternal,
    timeout_s=4 * 60.0 + 2 * TIMEOUT_FLASH_S,
)
