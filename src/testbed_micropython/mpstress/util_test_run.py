from __future__ import annotations

import dataclasses
import enum
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


class EnumTest(enum.StrEnum):
    RUN_TESTS_ALL = enum.auto()
    RUN_TESTS_BASIC = enum.auto()
    RUN_TESTS_BASIC_B = enum.auto()
    RUN_TESTS_BASIC_B_INT = enum.auto()
    RUN_TESTS_BASIC_B_INT_POW = enum.auto()
    RUN_TESTS_EXTMOD = enum.auto()

    @property
    def test_params(self) -> TestArgs:
        if self is EnumTest.RUN_TESTS_ALL:
            return TestArgs(
                timeout_s=240.0 * 1.5,
                files=["--exclude=ports/rp2/rp2_lightsleep_thread.py"],  # Broken test
            )
        if self is EnumTest.RUN_TESTS_BASIC:
            return TestArgs(
                timeout_s=61.0 * 1.5,
                files=["--include=basics/*"],
            )
        if self is EnumTest.RUN_TESTS_EXTMOD:
            return TestArgs(
                timeout_s=77.0 * 1.5,
                files=["--include=extmod/*"],
            )
        if self is EnumTest.RUN_TESTS_BASIC_B:
            return TestArgs(
                timeout_s=17.0 * 1.5,
                files=["--include=basics/b"],
            )
        if self is EnumTest.RUN_TESTS_BASIC_B_INT:
            return TestArgs(
                timeout_s=22.0 * 1.5,
                files=[
                    "--include=basics/(b|int_)",
                ],
            )
        if self is EnumTest.RUN_TESTS_BASIC_B_INT_POW:
            return TestArgs(
                timeout_s=13.0 * 1.5,
                files=[
                    "--include=basics/(b|int_)",
                    "--exclude=basics/builtin_pow",
                ],
            )
        raise ValueError(self)


@dataclasses.dataclass(repr=True, frozen=True)
class TestArgs:
    timeout_s: float
    files: list[str]


def run_test(
    tentacle_test: TentacleMicropython,
    repo_micropython_tests: pathlib.Path,
    directory_results: pathlib.Path,
    test: EnumTest,
) -> None:
    assert isinstance(tentacle_test, TentacleMicropython)
    assert isinstance(repo_micropython_tests, pathlib.Path)
    assert isinstance(directory_results, pathlib.Path)
    assert isinstance(test, EnumTest)

    # tentacle_test.power.dut = True
    with UdevPoller() as udev:
        tty = tentacle_test.dut.dut_mcu.application_mode_power_up(
            tentacle=tentacle_test, udev=udev
        )

    test_params = test.test_params

    args = [
        sys.executable,
        "run-tests.py",
        f"--result-dir={directory_results}",
        f"--test-instance=port:{tty}",
        "--jobs=1",
        *test_params.files,
        # "misc/cexample_class.py",
    ]
    env = ENV_PYTHONUNBUFFERED
    subprocess_run(
        args=args,
        cwd=repo_micropython_tests / MICROPYTHON_DIRECTORY_TESTS,
        env=env,
        # logfile=testresults_directory(f"run-tests-{test_dir}.txt").filename,
        logfile=directory_results / "testresults.txt",
        timeout_s=test_params.timeout_s,
        # TODO: Remove the following line as soon returncode of 'run-multitest.py' is fixed.
        success_returncodes=[0, 1],
    )
