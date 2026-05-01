from __future__ import annotations

import logging
import pathlib

from octoprobe.util_constants_uart_flakiness import (
    SUBPROCESS_TENTACLE_DUT_TIMEOUT,
)
from octoprobe.util_subprocess import SubprocessExitCodeException, subprocess_run

from . import util_subprocess_tentacle_timeout
from .constants import SUBPROCESS_PROVOKE_RETURNCODE2
from .testcollection.testrun_specs import TestRun

logger = logging.getLogger(__file__)


def tentacle_subprocess_run(
    args: list[str],
    cwd: pathlib.Path,
    logfile: pathlib.Path,
    testrun: TestRun,
    env: dict[str, str] | None = None,
    timeout_s: float = 10.0,
    success_returncodes: list[int] | None = None,
) -> str | None:
    def provoke_error() -> None:
        msg = f"{SUBPROCESS_PROVOKE_RETURNCODE2=}: We force error code 2!"
        if SUBPROCESS_PROVOKE_RETURNCODE2:
            logger.info(msg)
            raise SubprocessExitCodeException(msg)

    if SUBPROCESS_TENTACLE_DUT_TIMEOUT:
        stdout = util_subprocess_tentacle_timeout.tentacle_subprocess_run(
            args=args,
            cwd=cwd,
            env=env,
            # logfile=testresults_directory(f"run-tests-{test_dir}.txt").filename,
            logfile=logfile,
            testrun=testrun,
            timeout_s=timeout_s,
            # TODO: Remove the following line as soon returncode of 'run-multitest.py' is fixed.
            success_returncodes=success_returncodes,
        )
    else:
        stdout = subprocess_run(
            args=args,
            cwd=cwd,
            env=env,
            # logfile=testresults_directory(f"run-tests-{test_dir}.txt").filename,
            logfile=logfile,
            timeout_s=timeout_s,
            # TODO: Remove the following line as soon returncode of 'run-multitest.py' is fixed.
            success_returncodes=success_returncodes,
        )

    provoke_error()

    return stdout
