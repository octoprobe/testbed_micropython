from __future__ import annotations

import abc
import logging
import sys

from testbed_micropython.util_subprocess_tentacle import tentacle_subprocess_run

from ..constants import EnumFut
from ..mptest import util_common
from ..tentacle_spec import TentacleMicropython
from ..testcollection.baseclasses_spec import TestRole
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


class TestRunReference(TestRun):
    """
    These test runs against a reference tentacle
    """

    @abc.abstractmethod
    def setup(self, testargs: TestArgs) -> None: ...

    def test(self, testargs: TestArgs) -> None:
        if testargs.debug_skip_tests_with_message:
            return

        tentacle_instance0 = self.tentacle_instance0
        tentacle_instance1 = self.tentacle_instance1

        file_pattern = self.testrun_spec.command[1]
        assert isinstance(file_pattern, str)
        assert file_pattern != ""

        self.setup(testargs=testargs)

        # Run tests
        cwd = testargs.repo_micropython_tests / MICROPYTHON_DIRECTORY_TESTS
        list_tests = [str(f.relative_to(cwd)) for f in cwd.glob(file_pattern)]
        try:
            # This test will make the board disappear and therefore has to be skipped.
            list_tests.remove("multi_bluetooth/stress_deepsleep_reconnect.py")
        except ValueError:
            pass
        logfile = testargs.testresults_directory("testresults.txt").filename
        EVENTLOGCALLBACK.log(
            msg=f"Logfile: {testargs.testresults_directory.render_relative(logfile)}"
        )
        args = [
            sys.executable,
            self.testrun_spec.command_executable,
            f"--result-dir={testargs.testresults_directory.directory_test}",
            f"--test-instance=port:{tentacle_instance0.dut.get_tty()}",
            f"--test-instance=port:{tentacle_instance1.dut.get_tty()}",
            *list_tests,
        ]
        tentacle_subprocess_run(
            args=args,
            cwd=cwd,
            testrun=self,
            env=ENV_MICROPYTHON_TESTS,
            # logfile=testresults_directory(f"run-tests-{test_dir}.txt").filename,
            logfile=logfile,
            timeout_s=self.timeout_s,
            # TODO: Remove the following line as soon returncode of 'run-multitest.py' is fixed.
            success_returncodes=[0, 1],
        )

    @property
    def tentacle_instance0(self) -> TentacleMicropython:
        assert self.tentacle_reference is not None
        return (
            self.tentacle_variant.tentacle
            if self.tentacle_variant.role is TestRole.ROLE_INSTANCE0
            else self.tentacle_reference
        )

    @property
    def tentacle_instance1(self) -> TentacleMicropython:
        assert self.tentacle_reference is not None
        return (
            self.tentacle_variant.tentacle
            if self.tentacle_variant.role is TestRole.ROLE_INSTANCE1
            else self.tentacle_reference
        )


class TestRunReferenceMultinet(TestRunReference):
    def setup(self, testargs: TestArgs) -> None:
        self.skip_if_no_filesystem()

        assert self.tentacle_reference is not None

        for dut in (self.tentacle_variant.tentacle.dut, self.tentacle_reference.dut):
            util_common.copy_certificates(
                dut=dut,
                src=testargs.repo_micropython_tests
                / MICROPYTHON_DIRECTORY_TESTS
                / "multi_net",
            )

            util_common.init_wlan(dut=dut)


class TestRunReferenceBluetooth(TestRunReference):
    def setup(self, testargs: TestArgs) -> None:
        pass


TESTRUNSPEC_RUNTESTS_MULTINET = TestRunSpec(
    label="RUN-MULTITESTS_MULTINET",
    helptext="TODO helptext MULTINET",
    command=["run-multitests.py", "multi_net/*.py"],
    required_fut=EnumFut.FUT_WLAN,
    requires_reference_tentacle=True,
    testrun_class=TestRunReferenceMultinet,
    timeout_s=4 * 60.0 + 2 * TIMEOUT_FLASH_S,
)

TESTRUNSPEC_RUNTESTS_MULTBLUETOOTH = TestRunSpec(
    label="RUN-MULTITESTS_MULTIBLUETOOTH",
    helptext="One board connects to another using bluetooth",
    command=["run-multitests.py", "multi_bluetooth/*.py"],
    # command=["run-multitests.py", "multi_bluetooth/ble_characteristic.py"],
    required_fut=EnumFut.FUT_BLE,
    requires_reference_tentacle=True,
    testrun_class=TestRunReferenceBluetooth,
    timeout_s=4 * 60.0 + 2 * TIMEOUT_FLASH_S,
)
