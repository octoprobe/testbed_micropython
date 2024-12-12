from __future__ import annotations

import logging
import sys

from octoprobe.util_subprocess import subprocess_run

from testbed.constants import EnumFut
from testbed.mptest.util_testrunspec import mip_install
from testbed.testcollection.baseclasses_spec import TentacleVariant
from testbed.testcollection.testrun_specs import TestArgs, TestRun, TestRunSpec
from testbed.testrunspecs.multinet import copy_certificates, init_wlan

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
        copy_certificates(
            dut=tentacle.dut,
            src=testargs.git_micropython_tests / "tests" / "net_inet",
        )

        init_wlan(dut=tentacle.dut)

        serial_port = tentacle.dut.get_tty()

        mip_install(
            testargs=testargs,
            tentacle=tentacle,
            serial_port=serial_port,
            mip_package="unittest",
        )

        # Run tests
        args = [
            sys.executable,
            self.testrun_spec.command,
            *self.testrun_spec.auxiliary_args,
            f"-t=port:{serial_port}",
            "--jobs=1",
            f"--result-dir={testargs.testresults_directory.directory_test}",
        ]
        subprocess_run(
            args=args,
            cwd=testargs.git_micropython_tests / "tests",
            # logfile=testresults_directory(f"run-tests-{test_dir}.txt").filename,
            logfile=testargs.testresults_directory(
                "testresults_subprocess.txt"
            ).filename,
            timeout_s=60.0,
        )


TESTRUNSPEC_RUNTESTS_NET_INET = TestRunSpec(
    label="RUN-TESTS_NET_INET",
    # TODO: refactor as list
    command="run-tests.py",
    auxiliary_args=["--test-dirs=net_inet"],
    required_fut=EnumFut.FUT_WLAN,
    required_tentacles_count=1,
    testrun_class=TestRunRunTests,
)

TESTRUNSPEC_RUNTESTS_NET_HOSTED = TestRunSpec(
    label="RUN-TESTS_NET_HOSTED",
    command="run-tests.py",
    auxiliary_args=["--test-dirs=net_hosted"],
    required_fut=EnumFut.FUT_WLAN,
    required_tentacles_count=1,
    testrun_class=TestRunRunTests,
)
