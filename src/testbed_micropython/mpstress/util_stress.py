from __future__ import annotations

import enum
import logging
import pathlib
import threading
import time

from testbed_micropython.testcollection.baseclasses_spec import ConnectedTentacles

logger = logging.getLogger(__file__)


class EnumScenario(enum.StrEnum):
    NONE = enum.auto()
    DUT_ON_OFF = enum.auto()
    INFRA_MPREMOTE = enum.auto()


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

        assert False

    def _scenario_NONE(self) -> None:
        return

    def _scenario_INFRA_MPREMOTE(self) -> None:
        print("on")
        for t in self._tentacles_stress:
            t.infra.power.dut = True

        while True:
            if self._stopping:
                return
            print("cycle")
            for t in self._tentacles_stress:
                t.infra.mp_remote_close()
                t.infra.connect_mpremote_if_needed()
                print(t.infra.mp_remote._tty)
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
