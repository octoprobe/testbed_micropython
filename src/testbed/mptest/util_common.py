"""
These methods may be used by
testbed_showcase and testbed_micropython
"""

from __future__ import annotations

import dataclasses
import logging
import os
import pathlib
import sys
import typing

from octoprobe.lib_tentacle import Tentacle
from octoprobe.lib_tentacle_dut import TentacleDut
from octoprobe.util_subprocess import subprocess_run
from octoprobe.util_vscode_un_monkey_patch import un_monkey_patch

from testbed.util_firmware_mpbuild import CachedGitRepo

if typing.TYPE_CHECKING:
    from testbed.testcollection.testrun_specs import TestArgs

logger = logging.getLogger(__file__)


@dataclasses.dataclass
class ArgsMpTest:
    micropython_tests_git: str | None
    micropython_tests: str | None

    def clone_git_micropython_tests(
        self, directory_git_cache: pathlib.Path
    ) -> pathlib.Path:
        """
        We have to clone the micropython git repo and use the tests from the subfolder "test".
        """
        if self.micropython_tests is not None:
            _directory = pathlib.Path(self.micropython_tests).expanduser().resolve()
            if not _directory.is_dir():
                raise ValueError(
                    f"parameter '{self.micropython_tests}': Directory does not exist: {_directory}"
                )
            return _directory

        if self.micropython_tests_git is None:
            raise ValueError(
                "MicroPython repo not cloned - argument '{PYTEST_OPT_GIT_MICROPYTHON_TESTS}'not given to pytest !"
            )

        git_repo = CachedGitRepo(
            directory_cache=directory_git_cache,
            git_spec=self.micropython_tests_git,
            prefix="micropython_tests_",
        )
        git_repo.clone()

        # Avoid hanger in run-perfbench.py/run-tests.py
        un_monkey_patch()

        return git_repo.directory


def mip_install(
    testargs: TestArgs, tentacle: Tentacle, serial_port: str, mip_package: str
) -> None:
    assert testargs.__class__.__name__ == "TestArgs"
    assert isinstance(tentacle, Tentacle)
    assert isinstance(serial_port, str)
    assert isinstance(mip_package, str)
    # if False:
    # Using internal mp_remote connection
    # logger.info(f"{tentacle.dut.label}: mip install {mip_package}")
    # tentacle.dut.mp_remote.mip_install_package(mip_package)
    # return

    # Using external mpremote mip install
    args = [
        sys.executable,
        "-m",
        "mpremote",
        "connect",
        serial_port,
        "mip",
        "install",
        mip_package,
    ]
    subprocess_run(
        args=args,
        cwd=testargs.git_micropython_tests / "tests",
        logfile=testargs.testresults_directory(
            f"mip_install_{mip_package}.txt"
        ).filename,
        timeout_s=60.0,
    )


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
