from __future__ import annotations

import logging
import os
import sys

from octoprobe.util_subprocess import subprocess_run

from testbed.testcollection.baseclasses_spec import TentacleVariant
from testbed.testcollection.testrun_specs import TestArgs, TestRun, TestRunSpec

logger = logging.getLogger(__file__)


class TestRunWlan(TestRun):
    """
    This tests runs: wlan
    """

    def test(self, testargs: TestArgs) -> None:
        assert len(self.list_tentacle_variant) == 2
        tentacle_variant_first = self.list_tentacle_variant[0]
        tentacle_variant_second = self.list_tentacle_variant[1]
        assert isinstance(tentacle_variant_first, TentacleVariant)
        assert isinstance(tentacle_variant_second, TentacleVariant)
        tentacle_first = tentacle_variant_first.tentacle
        tentacle_second = tentacle_variant_second.tentacle
        tentacle_spec_first = tentacle_first.tentacle_spec
        tentacle_spec_second = tentacle_second.tentacle_spec
        assert tentacle_spec_first.mcu_config is not None
        assert tentacle_spec_second.mcu_config is not None

        cwd = testargs.git_micropython_tests / "tests"

        for tentacle_variant in self.list_tentacle_variant:
            dut = tentacle_variant.tentacle.dut

            dut.mp_remote.set_rtc()

            for certificate in (cwd / "multi_net").glob("*.der"):
                dut.mp_remote.cp(certificate, ":")

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

        serial_port_first = tentacle_first.dut.get_tty()
        serial_port_second = tentacle_second.dut.get_tty()
        # Run tests
        # multi_lan/*.py
        list_tests = [str(f.relative_to(cwd)) for f in cwd.glob("multi_net/*.py")]
        args = [
            sys.executable,
            "run-multitests.py",
            f"--instance=pyb:{serial_port_first}",
            f"--instance=pyb:{serial_port_second}",
            *list_tests,
        ]
        subprocess_run(
            args=args,
            cwd=cwd,
            # logfile=testresults_directory(f"run-tests-{test_dir}.txt").filename,
            logfile=testargs.testresults_directory("run-tests-wlan.txt").filename,
            timeout_s=60.0,
        )


TESTRUNSPEC_RUNTESTS_WLAN = TestRunSpec(
    subprocess_args=["NET"],
    tentacles_required=2,
    testrun_class=TestRunWlan,
)
