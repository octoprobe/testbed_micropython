from __future__ import annotations

import enum
import logging
import os
import pathlib
import subprocess
import sys
import threading
import time

from octoprobe.usb_tentacle.usb_tentacle import serial_short_from_delimited
from octoprobe.util_subprocess import subprocess_run

from testbed_micropython.testcollection.baseclasses_spec import ConnectedTentacles

from ..testcollection.constants import ENV_PYTHONUNBUFFERED

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent

logger = logging.getLogger(__file__)

# pylint: disable=invalid-name
# pylint: disable=no-member
# pylint: disable=protected-access

def print_fds() -> None:
    cmd = f"ls -l /proc/{os.getpid()}/fd"
    fd_text = subprocess.check_output(cmd, shell=True)
    print(f"  {cmd}: {len(fd_text.splitlines())} lines")
    print(fd_text.decode("ascii"))


class EnumScenario(enum.StrEnum):
    NONE = enum.auto()
    DUT_ON_OFF = enum.auto()
    INFRA_MPREMOTE = enum.auto()
    SUBPROCESS_INFRA_MPREMOTE = enum.auto()
    SUBPROCESS_INFRA_MPREMOTE_C = enum.auto()


class StressThread(threading.Thread):
    def __init__(
        self,
        scenario: EnumScenario,
        stress_tentacle_count: int,
        tentacles_stress: ConnectedTentacles,
        directory_results: pathlib.Path,
    ):
        assert isinstance(scenario, EnumScenario)
        assert isinstance(stress_tentacle_count, int)
        assert isinstance(tentacles_stress, ConnectedTentacles)
        assert isinstance(directory_results, pathlib.Path)
        super().__init__(daemon=True, name="stress")
        self._stopping = False
        self._stress_tentacle_count = stress_tentacle_count
        self._scenario = scenario
        self._directory_results = directory_results
        print(
            f"Found {len(tentacles_stress)} tentacle to create stress. stress_tentacle_count={self._stress_tentacle_count}."
        )
        self._tentacles_stress = tentacles_stress[: self._stress_tentacle_count]
        print(
            f"Tentacles to generate stress: {[serial_short_from_delimited(t.tentacle_instance.serial) for t in self._tentacles_stress]}"
        )

    def run(self) -> None:
        """
        Power up all duts on all tentacles.
        Now loop over all tentacles and power down dut for a short time
        """
        if self._scenario is EnumScenario.NONE:
            return self._scenario_NONE()

        if self._scenario is EnumScenario.DUT_ON_OFF:
            return self._scenario_DUT_ON_OFF()

        if self._scenario is EnumScenario.INFRA_MPREMOTE:
            return self._scenario_INFRA_MPREMOTE()

        if self._scenario is EnumScenario.SUBPROCESS_INFRA_MPREMOTE:
            return self._scenario_SUBPROCESS_INFRA_MPREMOTE()

        if self._scenario is EnumScenario.SUBPROCESS_INFRA_MPREMOTE_C:
            return self._scenario_SUBPROCESS_INFRA_MPREMOTE_C()

        raise ValueError(f"Not handled: scenario {self._scenario}!")

    def _scenario_NONE(self) -> None:
        return

    def _scenario_SUBPROCESS_INFRA_MPREMOTE_C(self) -> None:
        i = 0
        while True:
            print("cycle")
            for t in self._tentacles_stress:
                if self._stopping:
                    return
                i += 1
                assert t.infra.usb_tentacle.serial_port is not None
                args = [
                    str(DIRECTORY_OF_THIS_FILE / "c" / "mpremote_c"),
                    t.infra.usb_tentacle.serial_port,
                ]
                env = ENV_PYTHONUNBUFFERED
                subprocess_run(
                    args=args,
                    cwd=self._directory_results,
                    env=env,
                    logfile=self._directory_results / f"mpremote_c_{i:04d}.txt",
                    timeout_s=1.0,
                )

    def _scenario_SUBPROCESS_INFRA_MPREMOTE(self) -> None:
        i = 0
        while True:
            print("cycle")
            for t in self._tentacles_stress:
                if self._stopping:
                    return
                i += 1
                assert t.infra.usb_tentacle.serial_port is not None
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
                    logfile=self._directory_results / f"mpremote_{i:04d}.txt",
                    timeout_s=5.0,
                )

    def _scenario_INFRA_MPREMOTE(self) -> None:
        print("off")
        for t in self._tentacles_stress:
            t.infra.switches.dut = False

        i = 0
        while True:
            print("cycle")
            print_fds()

            for _idx, t in enumerate(self._tentacles_stress):
                if self._stopping:
                    return
                i += 1
                # if idx > 5:
                #     continue
                serial_closed = t.infra.mp_remote_close()
                t.infra.connect_mpremote_if_needed()
                assert t.infra._mp_remote is not None
                assert t.infra._mp_remote.state.transport is not None
                serial = t.infra._mp_remote.state.transport.serial
                fds = (
                    serial.fd,
                    serial.pipe_abort_read_r,
                    serial.pipe_abort_read_w,
                    serial.pipe_abort_write_r,
                    serial.pipe_abort_write_w,
                )
                print(
                    f"count={i:03d}",
                    f"pyserial.fds:{fds}",
                    f"close:{serial_closed}",
                    f"open:{t.infra.mp_remote._tty}",
                )
                if False:
                    rc = t.infra.mp_remote.exec_raw("print('Hello')")
                    assert rc == "Hello\r\n"
                # print(rc)

    def _scenario_DUT_ON_OFF(self) -> None:
        sleep_s = 1.0
        while not self._stopping:
            print("on")
            for t in self._tentacles_stress:
                t.infra.switches.dut = True
            time.sleep(sleep_s)

            print("off")
            for t in self._tentacles_stress:
                t.infra.switches.dut = False
            time.sleep(sleep_s)

    def stop(self) -> None:
        self._stopping = True
        self.join()
