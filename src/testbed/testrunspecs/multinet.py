from __future__ import annotations

import abc
import logging
import os
import pathlib
import sys

from octoprobe.util_subprocess import subprocess_run

from testbed.constants import EnumFut
from octoprobe.lib_tentacle_dut import TentacleDut

from testbed.testcollection.testrun_specs import TestArgs, TestRun, TestRunSpec

logger = logging.getLogger(__file__)


class TestRunMultitestBase(TestRun):

    @abc.abstractmethod
    def setup(self, testargs: TestArgs) -> None: ...

    def test(self, testargs: TestArgs) -> None:
        assert len(self.list_tentacle_variant) == 2
        tentacle_variant_first = self.list_tentacle_variant[0]
        tentacle_variant_second = self.list_tentacle_variant[1]

        file_pattern = self.testrun_spec.auxiliary_args[0]
        assert isinstance(file_pattern, str)
        assert file_pattern != ""

        self.setup(testargs=testargs)

        serial_port_first = tentacle_variant_first.tentacle.dut.get_tty()
        serial_port_second = tentacle_variant_second.tentacle.dut.get_tty()
        # Run tests
        cwd = testargs.git_micropython_tests / "tests"
        list_tests = [str(f.relative_to(cwd)) for f in cwd.glob(file_pattern)]
        args = [
            sys.executable,
            self.testrun_spec.command,
            f"--instance=pyb:{serial_port_first}",
            f"--instance=pyb:{serial_port_second}",
            *list_tests,
        ]
        subprocess_run(
            args=args,
            cwd=cwd,
            # logfile=testresults_directory(f"run-tests-{test_dir}.txt").filename,
            logfile=testargs.testresults_directory(
                "testresults_subprocess.txt"
            ).filename,
            timeout_s=60.0,
        )


# TODO: Move to a better location
def copy_certificates(dut: TentacleDut, src: pathlib.Path) -> None:
    assert isinstance(dut, TentacleDut)
    assert isinstance(src, pathlib.Path)

    dut.mp_remote.set_rtc()

    for certificate in src.glob("*.der"):
        dut.mp_remote.cp(certificate, ":")


def init_wlan(dut: TentacleDut) -> None:
    wlan_ssid = os.environ["WLAN_SSID"]
    wlan_key = os.environ["WLAN_PASS"]
    logger.info(f"{dut.label}: Try to connect to WLAN_SSID '{wlan_ssid}'")
    cmd = f"""
import machine, network
wlan = network.WLAN()
wlan.active(1)
wlan.config(txpower=5)
wlan.connect('{wlan_ssid}', '{wlan_key}')
while not wlan.isconnected():
    machine.idle()

config = wlan.ifconfig()
"""
    dut.mp_remote.exec_raw(cmd, timeout=10)
    config = dut.mp_remote.read_str("config")
    logger.info(f"WLAN {config=}")


class TestRunMultitestMultinet(TestRunMultitestBase):
    def setup(self, testargs: TestArgs) -> None:

        for tentacle_variant in self.list_tentacle_variant:
            dut = tentacle_variant.tentacle.dut
            copy_certificates(
                dut=dut,
                src=testargs.git_micropython_tests / "tests" / "multi_net",
            )

            init_wlan(dut=dut)


class TestRunMultitestBluetooth(TestRunMultitestBase):
    def setup(self, testargs: TestArgs) -> None:
        pass


TESTRUNSPEC_RUNTESTS_MULTINET = TestRunSpec(
    label="RUN-MULTITESTS_MULTINET",
    command="run-multitests.py",
    auxiliary_args=["multi_net/*.py"],
    required_fut=EnumFut.FUT_WLAN,
    required_tentacles_count=2,
    testrun_class=TestRunMultitestMultinet,
)
TESTRUNSPEC_RUNTESTS_MULTBLUETOOTH = TestRunSpec(
    label="RUN-MULTITESTS_MULTIBLUETOOTH",
    command="run-multitests.py",
    auxiliary_args=["multi_bluetooth/*.py"],
    required_fut=EnumFut.FUT_BLE,
    required_tentacles_count=2,
    testrun_class=TestRunMultitestBluetooth,
)
