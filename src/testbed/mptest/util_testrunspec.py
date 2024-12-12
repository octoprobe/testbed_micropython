"""
These methods may be used by
testbed_showcase and testbed_micropython
"""

from __future__ import annotations

import sys

from octoprobe.lib_tentacle import Tentacle
from octoprobe.util_subprocess import subprocess_run

from testbed.testcollection.testrun_specs import TestArgs


def mip_install(
    testargs: TestArgs, tentacle: Tentacle, serial_port: str, mip_package: str
) -> None:
    assert testargs.__class__.__name__ == "TestArgs"
    assert isinstance(tentacle, Tentacle)
    assert isinstance(serial_port, str)
    assert isinstance(mip_package, str)
    if False:
        # Using internal mp_remote connection
        logger.info(f"{tentacle.dut.label}: mip install {mip_package}")
        tentacle.dut.mp_remote.mip_install_package(mip_package)
        return

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
            f"mip_insall_{mip_package}.txt"
        ).filename,
        timeout_s=60.0,
    )
