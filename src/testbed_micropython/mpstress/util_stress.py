from __future__ import annotations

import enum
import logging
import pathlib
import sys
import threading
import time

from octoprobe.util_subprocess import subprocess_run

from testbed_micropython.testcollection.baseclasses_spec import ConnectedTentacles

from ..testcollection.constants import (
    ENV_PYTHONUNBUFFERED,
)

logger = logging.getLogger(__file__)


class EnumScenario(enum.StrEnum):
    NONE = enum.auto()
    DUT_ON_OFF = enum.auto()
    """
    13 tentacles

        timeout_s = 240.0 * 1.5
        files = ["--exclude=ports/rp2/rp2_lightsleep_thread.py"]  # Broken test

    --> no error!
    """
    INFRA_MPREMOTE = enum.auto()
    """
    13 tentacles

        timeout_s = 240.0 * 1.5
        files = []

    --> no error!
    """
    SUBPROCESS_INFRA_MPREMOTE = enum.auto()
    """
    13 tentacles

        timeout_s = 13.0 * 1.5
        files = [
            "--include=basics/(b|int_)",
            "--exclude=basics/builtin_pow",
        ]

    --> error after 20s
    """


class StressThread(threading.Thread):
    def __init__(
        self,
        scenario: EnumScenario,
        tentacles_stress: ConnectedTentacles,
        directory_results: pathlib.Path,
    ):
        assert isinstance(scenario, EnumScenario)
        assert isinstance(tentacles_stress, ConnectedTentacles)
        assert isinstance(directory_results, pathlib.Path)
        super().__init__(daemon=True, name="stress")
        self._stopping = False
        self._scenario = scenario
        self._tentacles_stress = tentacles_stress
        self._directory_results = directory_results

    def run(self) -> None:
        """
        Power up all duts on all tentacles.
        Now loop over all tentacles and power down dut for a short time
        """
        print(f"Found {len(self._tentacles_stress)} tentacle to create stress.")

        if self._scenario is EnumScenario.NONE:
            return self._scenario_NONE()

        if self._scenario is EnumScenario.DUT_ON_OFF:
            return self._scenario_DUT_ON_OFF()

        if self._scenario is EnumScenario.INFRA_MPREMOTE:
            return self._scenario_INFRA_MPREMOTE()
        if self._scenario is EnumScenario.SUBPROCESS_INFRA_MPREMOTE:
            return self._scenario_SUBPROCESS_INFRA_MPREMOTE()

        assert False

    def _scenario_NONE(self) -> None:
        return

    def _scenario_SUBPROCESS_INFRA_MPREMOTE(self) -> None:
        i = 0
        while True:
            print("cycle")
            for t in self._tentacles_stress:
                if self._stopping:
                    return
                i += 1
                args = [
                    sys.executable,
                    "-m",
                    "mpremote",
                    "connect",
                    t.infra.usb_tentacle.serial_port,
                    "eval",
                    "print('Hello MicroPython')",
                ]
                env = ENV_PYTHONUNBUFFERED
                subprocess_run(
                    args=args,
                    cwd=self._directory_results,
                    env=env,
                    # logfile=testresults_directory(f"run-tests-{test_dir}.txt").filename,
                    logfile=self._directory_results / f"mpremote_{i:03d}.txt",
                    timeout_s=5.0,
                )

    def _scenario_INFRA_MPREMOTE(self) -> None:
        print("off")
        for t in self._tentacles_stress:
            t.infra.power.dut = False

        i = 0
        while True:
            print("cycle")
            for idx, t in enumerate(self._tentacles_stress):
                if self._stopping:
                    return
                i += 1
                # if idx > 5:
                #     continue
                serial_closed = t.infra.mp_remote_close()
                t.infra.connect_mpremote_if_needed()
                print(
                    i,
                    t.infra._mp_remote.state.transport.serial.fd,
                    t.infra._mp_remote.state.transport.serial.pipe_abort_read_r,
                    t.infra._mp_remote.state.transport.serial.pipe_abort_read_w,
                    t.infra._mp_remote.state.transport.serial.pipe_abort_write_r,
                    t.infra._mp_remote.state.transport.serial.pipe_abort_write_w,
                    end="",
                )
                print(" ", serial_closed, t.infra.mp_remote._tty)
                rc = t.infra.mp_remote.exec_raw("print('Hello')")
                assert rc == "Hello\r\n"
                # print(rc)

    def _scenario_DUT_ON_OFF(self) -> None:
        sleep_s = 1.0
        while not self._stopping:
            print("on")
            for t in self._tentacles_stress:
                t.infra.power.dut = True
            time.sleep(sleep_s)

            print("off")
            for t in self._tentacles_stress:
                t.infra.power.dut = False
            time.sleep(sleep_s)

    def stop(self) -> None:
        self._stopping = True
        self.join()
