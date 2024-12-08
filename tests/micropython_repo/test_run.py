import logging
import pathlib
import sys

import pytest
from octoprobe.lib_tentacle import Tentacle
from octoprobe.util_cached_git_repo import CachedGitRepo
from octoprobe.util_pytest.util_resultdir import ResultsDir
from octoprobe.util_subprocess import subprocess_run
from octoprobe.util_vscode_un_monkey_patch import un_monkey_patch

from testbed.constants import DIRECTORY_GIT_CACHE, EnumFut
from testbed.util_github_micropython_org import (
    PYTEST_OPT_DIR_MICROPYTHON_TESTS,
    PYTEST_OPT_GIT_MICROPYTHON_TESTS,
)

logger = logging.getLogger(__file__)

# pylint: disable=W0621:redefined-outer-name


@pytest.fixture(scope="session", autouse=True)
def git_micropython_tests(request: pytest.FixtureRequest) -> pathlib.Path:
    """
    We have to clone the micropython git repo and use the tests from the subfolder "test".
    """
    directory = request.config.getoption(PYTEST_OPT_DIR_MICROPYTHON_TESTS)
    if directory is not None:
        _directory = pathlib.Path(directory).expanduser().resolve()
        if not _directory.is_dir():
            raise ValueError(
                f"pytest parameter '{PYTEST_OPT_DIR_MICROPYTHON_TESTS}': Directory does not exist: {_directory}"
            )
        return _directory

    git_spec = request.config.getoption(PYTEST_OPT_GIT_MICROPYTHON_TESTS)
    if git_spec is None:
        pytest.skip(
            "MicroPython repo not cloned - argument '{PYTEST_OPT_GIT_MICROPYTHON_TESTS}'not given to pytest !"
        )

    git_repo = CachedGitRepo(
        directory_cache=DIRECTORY_GIT_CACHE,
        git_spec=git_spec,
        prefix="micropython_tests_",
    )
    git_repo.clone()

    # Avoid hanger in run-perfbench.py/run-tests.py
    un_monkey_patch()

    return git_repo.directory


@pytest.mark.required_futs(EnumFut.FUT_MCU_ONLY)
def test_perf_bench(
    mcu: Tentacle,
    testresults_directory: ResultsDir,
    git_micropython_tests: pathlib.Path,
) -> None:
    """
    This tests runs: run-perfbench.py

    * https://github.com/micropython/micropython/blob/master/tests/README.md
    * https://github.com/micropython/micropython/blob/master/tests/run-perfbench.py
    """
    assert mcu.tentacle_spec.mcu_config is not None
    perftest_args = mcu.tentacle_spec.mcu_config.micropython_perftest_args
    if perftest_args is None:
        perftest_args = ["100", "100"]

    args = [
        sys.executable,
        "run-perfbench.py",
        "--pyboard",
        f"--device={mcu.dut.get_tty()}",
        *perftest_args,
    ]
    subprocess_run(
        args=args,
        cwd=git_micropython_tests / "tests",
        logfile=testresults_directory("run-perfbench.txt").filename,
        timeout_s=300.0,
    )


def _run_tests(
    mcu: Tentacle,
    testresults_directory: ResultsDir,
    test_dir: str,
    micropython_tests: pathlib.Path,
) -> None:
    """
    This tests runs: run-tests.py
    https://github.com/micropython/micropython/blob/master/tests/README.md
    https://github.com/micropython/micropython/blob/master/tests/run-tests.py
    """

    args = [
        sys.executable,
        "run-tests.py",
        f"-t=port:{mcu.dut.get_tty()}",
        # f"--target={target}",
        "--jobs=1",
        f"--result-dir={testresults_directory.directory_test}",
        f"--test-dirs={test_dir}",
        # "misc/cexample_class.py",
    ]
    subprocess_run(
        args=args,
        cwd=micropython_tests / "tests",
        logfile=testresults_directory(f"run-tests-{test_dir}.txt").filename,
        timeout_s=60.0,
    )


@pytest.mark.required_futs(EnumFut.FUT_MCU_ONLY)
def test_misc(
    mcu: Tentacle,
    testresults_directory: ResultsDir,
    git_micropython_tests: pathlib.Path,
) -> None:
    _run_tests(
        mcu=mcu,
        testresults_directory=testresults_directory,
        test_dir="misc",
        micropython_tests=git_micropython_tests,
    )


@pytest.mark.required_futs(EnumFut.FUT_EXTMOD_HARDWARE)
def test_extmod_hardware(
    mcu: Tentacle,
    testresults_directory: ResultsDir,
    git_micropython_tests: pathlib.Path,
) -> None:
    _run_tests(
        mcu=mcu,
        testresults_directory=testresults_directory,
        test_dir="extmod_hardware",
        micropython_tests=git_micropython_tests,
    )


# TODO: Remove 'wip_' prefix
# Why does discovery report: ValueError: No TENTACLE_DAQ_SALEAE tentacle was selected. Might be the required FUTS specified for TENTACLE_DAQ_SALEAE
@pytest.mark.required_futs(EnumFut.FUT_EXTMOD_HARDWARE)
def wip_test_wireing_FUT_EXTMOD_HARDWARE(
    mcu: Tentacle,
    daq_saleae: Tentacle,
) -> None:
    """
    With this test, we may verify if the wiring of the tentacles Lolin_D1_MINI and Lonlin_C3_MINI is correct.
    Trigger on channl D0 on saleae.
    Channel D1 (trigger_1) and D2 (signal_1) shoud raise to 1 for some ms time
    """
    cmd = """
import sys
from machine import Pin
if 'esp8266' in sys.platform:
    pin1=0
    pin2=4
if 'esp32' in sys.platform:
    pin1=0
    pin2=4

trigger1 = Pin(pin1, Pin.OUT)
trigger1.on()
signal1 = Pin(pin2, Pin.OUT)
signal1.on()
"""
    mcu.dut.mp_remote.exec_raw(cmd=cmd)

    cmd = """
signal1.off()
trigger1.off()
"""
    mcu.dut.mp_remote.exec_raw(cmd=cmd)
