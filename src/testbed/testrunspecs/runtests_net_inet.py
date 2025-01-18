from __future__ import annotations

import logging
import sys

from octoprobe.util_constants import relative_cwd
from octoprobe.util_subprocess import subprocess_run

from testbed.constants import EnumFut
from testbed.mptest import util_common
from testbed.mptest.util_common import mip_install
from testbed.multiprocessing.util_multiprocessing import EVENTLOGCALLBACK
from testbed.testcollection.baseclasses_spec import TentacleVariant
from testbed.testcollection.testrun_specs import (
    TIMEOUT_FLASH_S,
    TestArgs,
    TestRun,
    TestRunSpec,
)

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

        # for tests 'net_hosted', this call is irrelevant
        util_common.copy_certificates(
            dut=tentacle.dut,
            src=testargs.repo_micropython_tests / "tests" / "net_inet",
        )

        util_common.init_wlan(dut=tentacle.dut)

        serial_port = tentacle.dut.get_tty()

        mip_install(
            testargs=testargs,
            tentacle=tentacle,
            serial_port=serial_port,
            mip_package="unittest",
        )

        # Run tests
        logfile = testargs.testresults_directory("testresults.txt").filename
        EVENTLOGCALLBACK.log(msg=f"Logfile: {relative_cwd(logfile)}")
        args = [
            sys.executable,
            *self.testrun_spec.command,
            f"-t=port:{serial_port}",
            "--jobs=1",
            f"--result-dir={testargs.testresults_directory.directory_test}",
        ]
        subprocess_run(
            args=args,
            cwd=testargs.repo_micropython_tests / "tests",
            # logfile=testresults_directory(f"run-tests-{test_dir}.txt").filename,
            logfile=logfile,
            timeout_s=self.timeout_s,
        )


TESTRUNSPEC_RUNTESTS_NET_INET = TestRunSpec(
    label="RUN-TESTS_NET_INET",
    helptext="TODO: help net inet",
    command=["run-tests.py", "--test-dirs=net_inet"],
    required_fut=EnumFut.FUT_WLAN,
    required_tentacles_count=1,
    testrun_class=TestRunRunTests,
    timeout_s=60.0 + TIMEOUT_FLASH_S,
)

TESTRUNSPEC_RUNTESTS_NET_HOSTED = TestRunSpec(
    label="RUN-TESTS_NET_HOSTED",
    helptext="TODO: help net hosted",
    command=["run-tests.py", "--test-dirs=net_hosted"],
    required_fut=EnumFut.FUT_WLAN,
    required_tentacles_count=1,
    testrun_class=TestRunRunTests,
    timeout_s=60.0 + TIMEOUT_FLASH_S,
)
