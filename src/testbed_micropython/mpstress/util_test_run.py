from __future__ import annotations

import logging
import pathlib
import sys

from octoprobe.util_pyudev import UdevPoller
from octoprobe.util_subprocess import subprocess_run

from testbed_micropython.tentacle_spec import TentacleMicropython

from ..testcollection.constants import (
    ENV_PYTHONUNBUFFERED,
    MICROPYTHON_DIRECTORY_TESTS,
)

logger = logging.getLogger(__file__)


def run_test(
    tentacle_test: TentacleMicropython,
    repo_micropython_tests: pathlib.Path,
    directory_results: pathlib.Path,
) -> None:
    assert isinstance(tentacle_test, TentacleMicropython)
    assert isinstance(repo_micropython_tests, pathlib.Path)
    assert isinstance(directory_results, pathlib.Path)

    # tentacle_test.power.dut = True
    with UdevPoller() as udev:
        tty = tentacle_test.dut.dut_mcu.application_mode_power_up(
            tentacle=tentacle_test, udev=udev
        )

    if True:
        timeout_s = 240.0 * 1.5
        files = []
    if True:
        timeout_s = 61.0 * 1.5
        files = ["--include=basic/"]
    if True:
        timeout_s = 77.0 * 1.5
        files = ["--include=extmod/"]
    if True:
        timeout_s = 17.0 * 1.5
        files = ["--include=basics/b"]
    if True:
        timeout_s = 22.0 * 1.5
        files = ["--include=basics/(b|int_)"]

    args = [
        sys.executable,
        "run-tests.py",
        f"--result-dir={directory_results}",
        f"--test-instance=port:{tty}",
        "--jobs=1",
        *files,
        # "misc/cexample_class.py",
    ]
    env = ENV_PYTHONUNBUFFERED
    subprocess_run(
        args=args,
        cwd=repo_micropython_tests / MICROPYTHON_DIRECTORY_TESTS,
        env=env,
        # logfile=testresults_directory(f"run-tests-{test_dir}.txt").filename,
        logfile=directory_results / "testresults.txt",
        timeout_s=timeout_s,
        # TODO: Remove the following line as soon returncode of 'run-multitest.py' is fixed.
        success_returncodes=[0, 1],
    )
