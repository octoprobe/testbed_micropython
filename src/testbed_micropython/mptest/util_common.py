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

from octoprobe.lib_mpremote import ExceptionCmdFailed
from octoprobe.lib_tentacle import TentacleBase
from octoprobe.lib_tentacle_dut import TentacleDut
from octoprobe.util_baseclasses import (
    OctoprobeTestException,
    OctoprobeTestSkipException,
    assert_micropython_repo,
)
from octoprobe.util_subprocess import subprocess_run

from ..constants import is_url
from ..testcollection.testrun_specs import MICROPYTHON_DIRECTORY_TESTS
from ..util_firmware_mpbuild import CachedGitRepo

if typing.TYPE_CHECKING:
    from ..testcollection.testrun_specs import TestArgs

logger = logging.getLogger(__file__)

ENV_PYTHONUNBUFFERED = {"PYTHONUNBUFFERED": "1"}


@dataclasses.dataclass
class ArgsMpTest:
    micropython_tests: str

    def clone_git_micropython_tests(
        self, directory_git_cache: pathlib.Path
    ) -> pathlib.Path:
        """
        We have to clone the micropython git repo and use the tests from the subfolder "test".
        """
        if is_url(self.micropython_tests):
            # 'self.micropython_tests' is a url pointing to a git rep
            git_repo = CachedGitRepo(
                directory_cache=directory_git_cache,
                git_spec=self.micropython_tests,
                prefix="tests_",
            )
            git_repo.clone(git_clean=False)

            _directory = git_repo.directory_git_worktree
        else:
            # 'self.micropython_tests' is a filename.
            _directory = pathlib.Path(self.micropython_tests).expanduser().resolve()
            assert_micropython_repo(_directory)
            if not _directory.is_dir():
                raise ValueError(
                    f"parameter '{self.micropython_tests}': Directory does not exist: {_directory}"
                )

        # Avoid hanger in run-perfbench.py/run-tests.py
        # un_monkey_patch()

        return _directory


def skip_if_no_filesystem(tentacle: TentacleBase) -> None:
    assert isinstance(tentacle, TentacleBase)
    try:
        _ret = tentacle.dut.mp_remote.exec_raw("import os; os.listdir('/')")
    except ExceptionCmdFailed as e:
        msg = f"{tentacle.label_short}: No filesystem: Skip Test!"
        logger.warning(msg)
        raise OctoprobeTestSkipException(msg) from e


def mip_install(
    testargs: TestArgs,
    tentacle: TentacleBase,
    serial_port: str,
    mip_package: str,
) -> None:
    assert testargs.__class__.__name__ == "TestArgs"
    assert isinstance(tentacle, TentacleBase)
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
        cwd=testargs.repo_micropython_tests / MICROPYTHON_DIRECTORY_TESTS,
        env=ENV_PYTHONUNBUFFERED,
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
    try:
        dut.mp_remote.exec_raw(cmd, timeout=10)
    except TimeoutError as e:
        msg = f"Timeout while connecting to WLAN_SSID '{wlan_ssid}'"
        logger.debug(msg, exc_info=e)
        raise OctoprobeTestException(msg) from e
    config = dut.mp_remote.read_str("config")
    logger.info(f"WLAN {config=}")
