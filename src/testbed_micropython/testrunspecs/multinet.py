from __future__ import annotations

import abc
import logging
import sys

from octoprobe.util_subprocess import subprocess_run

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
        tentacle_first = self.tentacle_first
        tentacle_second = self.tentacle_second

        file_pattern = self.testrun_spec.command[1]
        assert isinstance(file_pattern, str)
        assert file_pattern != ""

        self.setup(testargs=testargs)

        serial_port_first = tentacle_first.dut.get_tty()
        serial_port_second = tentacle_second.dut.get_tty()
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
            f"--instance=pyb:{serial_port_first}",
            f"--instance=pyb:{serial_port_second}",
            *list_tests,
        ]
        subprocess_run(
            args=args,
            cwd=cwd,
            env=ENV_MICROPYTHON_TESTS,
            # logfile=testresults_directory(f"run-tests-{test_dir}.txt").filename,
            logfile=logfile,
            timeout_s=self.timeout_s,
        )

    @property
    def tentacle_first(self) -> TentacleMicropython:
        assert self.tentacle_reference is not None
        return (
            self.tentacle_variant.tentacle
            if self.tentacle_variant.role is TestRole.ROLE_FIRST
            else self.tentacle_reference
        )

    @property
    def tentacle_second(self) -> TentacleMicropython:
        assert self.tentacle_reference is not None
        return (
            self.tentacle_variant.tentacle
            if self.tentacle_variant.role is TestRole.ROLE_SECOND
            else self.tentacle_reference
        )


class TestRunRefernceMultinet(TestRunReference):
    def setup(self, testargs: TestArgs) -> None:
        util_common.skip_if_no_filesystem(tentacle=self.tentacle_variant.tentacle)

        dut = self.tentacle_variant.tentacle.dut
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
    testrun_class=TestRunRefernceMultinet,
    timeout_s=4 * 60.0 + 2 * TIMEOUT_FLASH_S,
)

TESTRUNSPEC_RUNTESTS_MULTBLUETOOTH = TestRunSpec(
    label="RUN-MULTITESTS_MULTIBLUETOOTH",
    helptext="One board connects to another using bluetooth",
    # command=["run-multitests.py", "multi_bluetooth/*.py"],
    command=["run-multitests.py", "multi_bluetooth/ble_characteristic.py"],
    required_fut=EnumFut.FUT_BLE,
    requires_reference_tentacle=True,
    testrun_class=TestRunReferenceBluetooth,
    timeout_s=4 * 60.0 + 2 * TIMEOUT_FLASH_S,
)
