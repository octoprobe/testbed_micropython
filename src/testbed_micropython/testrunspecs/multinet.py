from __future__ import annotations

import abc
import logging
import sys

from octoprobe.util_constants import relative_cwd
from octoprobe.util_subprocess import subprocess_run

from ..constants import EnumFut
from ..mptest import util_common
from ..multiprocessing.util_multiprocessing import EVENTLOGCALLBACK
from ..testcollection.testrun_specs import (
    TIMEOUT_FLASH_S,
    TestArgs,
    TestRun,
    TestRunSpec,
)

logger = logging.getLogger(__file__)


class TestRunMultitestBase(TestRun):
    @abc.abstractmethod
    def setup(self, testargs: TestArgs) -> None: ...

    def test(self, testargs: TestArgs) -> None:
        assert len(self.list_tentacle_variant) == 2
        tentacle_variant_first = self.list_tentacle_variant[0]
        tentacle_variant_second = self.list_tentacle_variant[1]

        file_pattern = self.testrun_spec.command[1]
        assert isinstance(file_pattern, str)
        assert file_pattern != ""

        self.setup(testargs=testargs)

        serial_port_first = tentacle_variant_first.tentacle.dut.get_tty()
        serial_port_second = tentacle_variant_second.tentacle.dut.get_tty()
        # Run tests
        cwd = testargs.repo_micropython_tests / "tests"
        list_tests = [str(f.relative_to(cwd)) for f in cwd.glob(file_pattern)]
        try:
            # This test will make the board disappear and therefore has to be skipped.
            list_tests.remove("multi_bluetooth/stress_deepsleep_reconnect.py")
        except ValueError:
            pass
        logfile = testargs.testresults_directory("testresults.txt").filename
        EVENTLOGCALLBACK.log(msg=f"Logfile: {relative_cwd(logfile)}")
        args = [
            sys.executable,
            self.testrun_spec.command_executable,
            f"--instance=pyb:{serial_port_first}",
            f"--instance=pyb:{serial_port_second}",
            *list_tests,
        ]
        subprocess_run(
            args=args,
            cwd=cwd,
            # logfile=testresults_directory(f"run-tests-{test_dir}.txt").filename,
            logfile=logfile,
            timeout_s=self.timeout_s,
        )


class TestRunMultitestMultinet(TestRunMultitestBase):
    def setup(self, testargs: TestArgs) -> None:
        for tentacle_variant in self.list_tentacle_variant:
            dut = tentacle_variant.tentacle.dut
            util_common.copy_certificates(
                dut=dut,
                src=testargs.repo_micropython_tests / "tests" / "multi_net",
            )

            util_common.init_wlan(dut=dut)


class TestRunMultitestBluetooth(TestRunMultitestBase):
    def setup(self, testargs: TestArgs) -> None:
        pass


TESTRUNSPEC_RUNTESTS_MULTINET = TestRunSpec(
    label="RUN-MULTITESTS_MULTINET",
    helptext="TODO helptext MULTINET",
    command=["run-multitests.py", "multi_net/*.py"],
    required_fut=EnumFut.FUT_WLAN,
    required_tentacles_count=2,
    testrun_class=TestRunMultitestMultinet,
    timeout_s=60.0 + TIMEOUT_FLASH_S,
)

TESTRUNSPEC_RUNTESTS_MULTBLUETOOTH = TestRunSpec(
    label="RUN-MULTITESTS_MULTIBLUETOOTH",
    helptext="One board connects to another using bluetooth",
    command=["run-multitests.py", "multi_bluetooth/*.py"],
    required_fut=EnumFut.FUT_BLE,
    required_tentacles_count=2,
    testrun_class=TestRunMultitestBluetooth,
    timeout_s=60.0 + TIMEOUT_FLASH_S,
)
