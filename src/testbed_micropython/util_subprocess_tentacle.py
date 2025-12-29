from __future__ import annotations

import io
import logging
import pathlib
import subprocess
import threading
import time
import typing

from testbed_micropython.testcollection.testrun_specs import TestRun

logger = logging.getLogger(__file__)


class SubprocessExitCodeException(Exception):
    pass


class TentaclePowerOffTimer:
    """
    Background thread that powers off DUT after a timeout unless cancelled.

    - Starts on context enter and fires after `timeout_s`.
    - Calling `cancel()` (or leaving the context) prevents power-off.
    """

    PRE_TIMEOUT_S = 10.0

    def __init__(
        self,
        testrun: TestRun,
        timeout_s: float,
        f: io.TextIOWrapper,
    ) -> None:
        assert isinstance(testrun, TestRun)
        assert isinstance(timeout_s, float)
        assert timeout_s >= 0.0
        self._testrun = testrun
        self._timeout_s = timeout_s
        self._timeout_powerdown_s = max(0.0, timeout_s - self.PRE_TIMEOUT_S)
        self._cancel_event = threading.Event()
        self._thread = threading.Thread(
            target=self._run, name="TentaclePowerOffTimer", daemon=True
        )
        self._f = f

    def _run(self) -> None:
        # Wait until timeout or cancellation
        cancelled = self._cancel_event.wait(timeout=self._timeout_s)
        if cancelled:
            return
        try:
            self.power_off()
        except Exception as e:  # Be robust; never crash the process due to timer
            logger.exception(e)

    def power_off(self) -> None:
        """
        Power off DUT for all tentacles in this testrun.
        """
        for tentacle in self._testrun.tentacles:
            try:
                msg = f"{tentacle.label}: TentaclePowerOffTimer: Powering off DUT after {self._timeout_powerdown_s:0.0f}s just before {self._timeout_s:0.0f}s when subprocess will be killed. This is done in the hope to clean up the usb stack properly. See ticket https://github.com/octoprobe/testbed_micropython/issues/67."
                logger.warning(msg)
                self._f.flush()
                self._f.write(f"\n\n\n{msg}\n\n\n")
                self._f.flush()
                tentacle.infra.switches.dut = False
            except Exception as e:
                logger.exception(e)

    def __enter__(self) -> TentaclePowerOffTimer:
        # Start timer thread
        if not self._thread.is_alive():
            self._thread.start()
        return self

    def __exit__(self, exc_type:typing.Any, value:typing.Any, traceback:typing.Any) -> None:
        # Ensure timer is cancelled and thread is finished
        self.cancel()

    def cancel(self) -> None:
        self._cancel_event.set()
        if self._thread.is_alive():
            self._thread.join(timeout=1.0)


def tentacle_subprocess_run(
    args: list[str],
    cwd: pathlib.Path,
    logfile: pathlib.Path,
    testrun: TestRun,
    env: dict[str, str] | None = None,
    timeout_s: float = 10.0,
    success_returncodes: list[int] | None = None,
) -> str | None:
    """
    Wrapper around 'subprocess()'

    There was instability of USB-cdc with many tentacles involved.
    See: https://github.com/octoprobe/testbed_micropython/issues/67
    This method is a blind guess: When a subprocess times out but still has USB-cdc open will lead in some leaks...

    This methods should prevent this. Before the subprocess times out, the
    DUT of the tentacles will be unpowered which might clean up the USB stack
    in a 'better' way. But this is just a guess...
    """
    assert isinstance(args, list)
    assert isinstance(cwd, pathlib.Path)
    assert isinstance(testrun, TestRun)
    assert isinstance(env, dict | None)
    assert isinstance(logfile, pathlib.Path)
    assert isinstance(timeout_s, float | None)
    assert isinstance(success_returncodes, list | None)
    if success_returncodes is None:
        success_returncodes = [0]

    if env is not None:
        for key, value in env.items():
            assert isinstance(key, str)
            assert isinstance(value, str)

    args_text = " ".join(args)

    begin_s = time.monotonic()
    try:
        assert logfile is not None
        logger.info(f"EXEC {args_text}")
        logger.info(f"EXEC     cwd={cwd}")
        logger.info(f"EXEC     stdout: {logfile}")
        logfile.parent.mkdir(parents=True, exist_ok=True)
        with logfile.open("w") as f:
            # Set file to line buffered mode
            f.write(f"cd {cwd}\n")
            f.write(f"{timeout_s=}\n")
            if env is not None:
                for k, v in env.items():
                    f.write(f"export {k}={v}\n")
            f.write("\n")
            f.write(f"{' '.join(args)}\n")
            f.write("\n\n")
            f.flush()
            try:
                # proc = subprocess.run()
                # proc = subprocess.run(
                #     # Common args
                #     args=args,
                #     check=False,
                #     text=True,
                #     cwd=str(cwd),
                #     env=env,
                #     timeout=timeout_s,
                #     # Specific args
                #     stdout=f,
                #     stderr=subprocess.STDOUT,
                # )
                def sub_run() -> subprocess.CompletedProcess[str]:
                    """
                    This corresponds to subprocess.py, def run()
                    """
                    with subprocess.Popen(
                        args=args,
                        text=True,
                        cwd=str(cwd),
                        env=env,
                        stdout=f,
                        stderr=subprocess.STDOUT,
                    ) as process:
                        with TentaclePowerOffTimer(
                            testrun=testrun,
                            timeout_s=timeout_s,
                            f=f,
                        ) as tenacle_power_off_timer:
                            stdout = stderr = "...empty...\n"
                            try:
                                stdout, stderr = process.communicate(timeout=timeout_s)
                            except subprocess.TimeoutExpired:
                                try:
                                    # Before kill(), try terminate()
                                    process.terminate()
                                    process.wait(timeout=3.0)
                                    logger.info("process.terminate() succeeded()")
                                except subprocess.TimeoutExpired:
                                    logger.info(
                                        "process.terminate() was running into a timeout. Now try to use process.kill()"
                                    )
                                    process.kill()
                                    # POSIX _communicate already populated the output so
                                    # far into the TimeoutExpired exception.
                                    process.wait()
                                else:
                                    # The try clause does not raise an exception
                                    raise
                            except:  # Including KeyboardInterrupt, communicate handled that.
                                process.kill()
                                # We don't call process.wait() as .__exit__ does that for us.
                                raise

                            tenacle_power_off_timer.cancel()
                            retcode = process.poll()
                            assert isinstance(retcode, int)
                            return subprocess.CompletedProcess(
                                process.args, retcode, stdout, stderr
                            )

                proc = sub_run()
                f.write(f"\n\nreturncode={proc.returncode}\n")
                f.write(f"duration={time.monotonic() - begin_s:0.3f}s\n")
            except subprocess.TimeoutExpired as e:
                f.write("\n\n")
                f.write(f"TimeoutExpired after {timeout_s=}: {e}\n")
                # Does it take some time for the subprocess to fully die?
                # To be sure, we wait some time.
                # This should avoid to unpower the tentacle before the subprocess really terminated.
                dying_gasp_timeout_s = 10.0
                f.write(f"Waiting for another {dying_gasp_timeout_s=}s\n")
                f.flush()
                time.sleep(dying_gasp_timeout_s)
                f.write("DONE\n")
                f.flush()
                raise

    except subprocess.TimeoutExpired as e:
        logger.info(f"EXEC {e!r}")
        # logger.exception(e)
        raise

    def log(f: typing.Callable[[str], None]) -> None:
        f(f"EXEC {args_text}")
        f(f"  cwd={cwd}")
        f(f"  returncode: {proc.returncode}")
        f(f"  success_codes: {success_returncodes}")
        f(f"  duration: {time.monotonic() - begin_s:0.3f}s")
        if logfile is None:
            stdout = proc.stdout.strip()
            stderr = proc.stderr.strip()
            f(f"  stdout: {stdout}")
            f(f"  stderr: {stderr}")
        else:
            f(f"  logfile: {logfile}")

    if proc.returncode not in success_returncodes:
        log(logger.warning)
        msg = f"EXEC failed with returncode={proc.returncode}: {args_text}"
        if logfile is not None:
            msg += f"\nlogfile={logfile}"
        else:
            msg += f"\n{proc.stdout.strip()}\n{proc.stderr.strip()}"
        raise SubprocessExitCodeException(msg)

    log(logger.debug)

    if logfile is None:
        return proc.stdout.strip()
    return None
