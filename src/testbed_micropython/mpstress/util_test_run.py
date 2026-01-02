from __future__ import annotations

import dataclasses
import enum
import logging
import pathlib
import sys
import time

from octoprobe.util_pyudev import UdevPoller
from octoprobe.util_subprocess import subprocess_run

from testbed_micropython.tentacle_spec import TentacleMicropython

from ..testcollection.constants import (
    ENV_PYTHONUNBUFFERED,
    MICROPYTHON_DIRECTORY_TESTS,
)

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent

logger = logging.getLogger(__file__)


class EnumTest(enum.StrEnum):
    RUN_TESTS_ALL = enum.auto()
    RUN_TESTS_BASIC = enum.auto()
    RUN_TESTS_BASIC_B = enum.auto()
    RUN_TESTS_BASIC_B_INT = enum.auto()
    RUN_TESTS_BASIC_B_INT_POW = enum.auto()
    RUN_TESTS_EXTMOD = enum.auto()
    SERIAL_TEST = enum.auto()
    SIMPLE_SERIAL_WRITE = enum.auto()

    def get_test_args(self, tentacle_test: TentacleMicropython) -> TestArgs:
        serial_speed_default = 249  # kByts/s
        serial_speed = serial_speed_default
        for mcu, _serial_speed in (
            ("ESP32", 12),
            ("LOLIN_D1", 12),
            ("WB55", 12),
            ("ADA_ITSYBITSY_M0", 140),
        ):
            if mcu in tentacle_test.description_short:
                serial_speed = _serial_speed
                print(
                    f"*** {mcu}: serial_speed_default={serial_speed_default}, serial_speed={serial_speed}kBytes/s"
                )
                break

        if self is EnumTest.RUN_TESTS_ALL:
            return TestArgs(
                timeout_s=240.0 * 1.5,
                program=["run-tests.py", "--jobs=1"],
                files=[
                    "--exclude=ports/rp2/rp2_lightsleep_thread.py",  # Broken test
                ],
            )
        if self is EnumTest.RUN_TESTS_BASIC:
            return TestArgs(
                timeout_s=61.0 * 1.5,
                program=["run-tests.py", "--jobs=1"],
                files=[
                    "--include=basics/*",
                ],
            )
        if self is EnumTest.RUN_TESTS_EXTMOD:
            return TestArgs(
                timeout_s=77.0 * 1.5,
                program=["run-tests.py", "--jobs=1"],
                files=[
                    "--include=extmod/*",
                ],
            )
        if self is EnumTest.RUN_TESTS_BASIC_B:
            return TestArgs(
                program=["run-tests.py", "--jobs=1"],
                timeout_s=17.0 * 1.5,
                files=[
                    "--include=basics/b",
                ],
            )
        if self is EnumTest.RUN_TESTS_BASIC_B_INT:
            return TestArgs(
                program=["run-tests.py", "--jobs=1"],
                timeout_s=22.0 * 1.5,
                files=[
                    "--include=basics/(b|int_)",
                ],
            )
        if self is EnumTest.RUN_TESTS_BASIC_B_INT_POW:
            return TestArgs(
                program=["run-tests.py", "--jobs=1"],
                timeout_s=13.0 * 1.5,
                files=[
                    "--include=basics/(b|int_)",
                    "--exclude=basics/builtin_pow",
                ],
            )
        if self is EnumTest.SERIAL_TEST:
            return TestArgs(
                program=["serial_test.py", "--time-per-subtest=10"],
                timeout_s=90.0 * 1.5,
                files=[],
            )
        if self is EnumTest.SIMPLE_SERIAL_WRITE:
            duration_factor = 1
            duration_factor = 5
            duration_factor = 2
            # duration_factor = 100
            count = int(duration_factor * 10000 * serial_speed / serial_speed_default)
            count = max(1000, count)
            return TestArgs(
                program=[
                    "simple_serial_write.py",
                    f"--count={count}",
                ],
                timeout_s=duration_factor * 3.4 * 1.5 + 10.0,
                files=[],
            )
        raise ValueError(self)


@dataclasses.dataclass(repr=True, frozen=True)
class TestArgs:
    program: list[str]
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

    print(f"*** power up tentacle_test: {tentacle_test.label_short}")

    # tentacle_test.power.dut = True
    with UdevPoller() as udev:
        tty = tentacle_test.dut.dut_mcu.application_mode_power_up(
            tentacle=tentacle_test,
            udev=udev,
        )
    time.sleep(1.0)

    test_args = test.get_test_args(tentacle_test)
    # timeout_s = test_params.timeout_s
    # for mcu in ("ESP32", "LOLIN_D1", "WB55"):
    #     if mcu in tentacle_test.description_short:
    #         timeout_s *= 15
    #         logger.info(f"*** {mcu}: timeout_s={timeout_s:0.0f}s")

    args_aux: list[str] = []
    cwd = repo_micropython_tests / MICROPYTHON_DIRECTORY_TESTS
    if test == EnumTest.SERIAL_TEST:
        pass
    elif test == EnumTest.SIMPLE_SERIAL_WRITE:
        cwd = DIRECTORY_OF_THIS_FILE
    else:
        args_aux = [f"--result-dir={directory_results}"]
    args = [
        sys.executable,
        *test_args.program,
        f"--test-instance=port:{tty}",
        *args_aux,
        *test_args.files,
        # "misc/cexample_class.py",
    ]
    env = ENV_PYTHONUNBUFFERED
    print(f"*** RUN: run_test(): subprocess_run({args})")
    begin_s = time.monotonic()
    subprocess_run(
        args=args,
        cwd=cwd,
        env=env,
        # logfile=testresults_directory(f"run-tests-{test_dir}.txt").filename,
        logfile=directory_results
        / f"testresults_{tentacle_test.tentacle_serial_number}_{tentacle_test.tentacle_spec_base.tentacle_tag}.txt",
        timeout_s=test_args.timeout_s,
        # TODO: Remove the following line as soon returncode of 'run-multitest.py' is fixed.
        # success_returncodes=[0, 1],
    )
    duration_s = time.monotonic() - begin_s
    if duration_s > test_args.timeout_s * 0.5:
        print(
            f"*** WARNING: {tentacle_test.description_short}: duration_s={duration_s:0.0f}s > timeout*0.5={test_args.timeout_s * 0.5:0.0f}s"
        )
    print(f"DONE: run_test(): subprocess_run({args})")
