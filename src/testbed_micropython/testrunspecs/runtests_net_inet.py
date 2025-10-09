from __future__ import annotations

import logging
import sys

from octoprobe.util_subprocess import subprocess_run

from ..constants import EnumFut
from ..mptest import util_common
from ..testcollection.baseclasses_spec import TentacleSpecVariant
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


class TestRunRunTests(TestRun):
    """
    This tests runs: run-tests.py

    https://github.com/micropython/micropython/blob/master/tests/README.md
    https://github.com/micropython/micropython/blob/master/tests/run-tests.py
    """

    def test(self, testargs: TestArgs) -> None:
        if testargs.debug_skip_tests_with_message:
            return

        assert isinstance(self.tentacle_variant, TentacleSpecVariant)
        tentacle = self.tentacle_variant.tentacle
        tentacle_spec = tentacle.tentacle_spec
        assert tentacle_spec.mcu_config is not None

        self.skip_if_no_filesystem()

        # for tests 'net_hosted', this call is irrelevant
        util_common.copy_certificates(
            dut=tentacle.dut,
            src=testargs.repo_micropython_tests
            / MICROPYTHON_DIRECTORY_TESTS
            / "net_inet",
        )

        util_common.init_wlan(dut=tentacle.dut)

        serial_port = tentacle.dut.get_tty()

        util_common.mip_install(
            testargs=testargs,
            tentacle=tentacle,
            serial_port=serial_port,
            mip_package="unittest",
        )

        # Run tests
        logfile = testargs.testresults_directory("testresults.txt").filename
        EVENTLOGCALLBACK.log(
            msg=f"Logfile: {testargs.testresults_directory.render_relative(logfile)}"
        )
        args = [
            sys.executable,
            *self.testrun_spec.command,
            f"--test-instance=port:{serial_port}",
            "--jobs=1",
            f"--result-dir={testargs.directory_test}",
        ]
        subprocess_run(
            args=args,
            cwd=testargs.repo_micropython_tests / MICROPYTHON_DIRECTORY_TESTS,
            env=ENV_MICROPYTHON_TESTS,
            logfile=logfile,
            timeout_s=self.timeout_s,
        )


TESTRUNSPEC_RUNTESTS_NET_INET = TestRunSpec(
    label="RUN-TESTS_NET_INET",
    helptext="TODO: help net inet",
    command=["run-tests.py", "--test-dirs=net_inet"],
    required_fut=EnumFut.FUT_WLAN,
    requires_reference_tentacle=False,
    testrun_class=TestRunRunTests,
    timeout_s=60.0 + TIMEOUT_FLASH_S,
)

TESTRUNSPEC_RUNTESTS_NET_HOSTED = TestRunSpec(
    label="RUN-TESTS_NET_HOSTED",
    helptext="TODO: help net hosted",
    command=["run-tests.py", "--test-dirs=net_hosted"],
    required_fut=EnumFut.FUT_WLAN,
    requires_reference_tentacle=False,
    testrun_class=TestRunRunTests,
    timeout_s=60.0 + TIMEOUT_FLASH_S,
)
