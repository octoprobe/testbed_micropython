from __future__ import annotations

import csv
import logging
import time

import dwfpy
import pandas

from esp32ramp import constants
from esp32ramp.context_measure import MeasureContext, Scope

logger = logging.getLogger(__name__)

BEGIN_V = 0.5
END_V = 5.0
TRIGGER_V = 1.0
EXPERIMENT_DURATION_S = 1.0

LOGGING_FORMAT = "%(asctime)s %(levelname)s %(filename)s:%(lineno)d %(message)s"
LOGGING_DATEFMT = "%H:%M:%S"
logging.basicConfig(
    level=logging.DEBUG,
    format=LOGGING_FORMAT,
    datefmt=LOGGING_DATEFMT,
)
logger_dwfpy = logging.getLogger("dwfpy")
logger_dwfpy.setLevel("INFO")


def ramp_by_step_duration(mtx: MeasureContext, ramp_duration_s: int) -> None:
    steps = (1.0, 2.0, 3.0, 4.0, 5.0)
    step_duration_s = ramp_duration_s / (len(steps) - 1)
    mtx.ad3.supply_P.enable = True
    mtx.ad3.supply_P.V = 0.5
    begin_s = time.monotonic()
    for idx0, voltage in enumerate(steps):
        duration_required_s = idx0 * step_duration_s
        duration_actual_s = time.monotonic() - begin_s
        time_to_wait_s = duration_required_s - duration_actual_s
        if time_to_wait_s > 0:
            time.sleep(time_to_wait_s)
        print(f"{voltage:0.1f}V {1000 * (time.monotonic() - begin_s):0.1f}ms")
        mtx.ad3.supply_P.V = voltage


def ramp_fast(mtx: MeasureContext, ramp_duration_s: int) -> pandas.DataFrame:
    list_time_ms: list[float] = []
    list_ramp_V: list[float] = []

    mtx.ad3.supply_P.V = BEGIN_V
    mtx.ad3.supply_P.enable = True
    begin_s = time.monotonic()
    active = True
    steps = 0
    while active:
        steps += 1
        duration_actual_s = time.monotonic() - begin_s
        try:
            actual_V = BEGIN_V + (END_V - BEGIN_V) * duration_actual_s / ramp_duration_s
        except ZeroDivisionError:
            actual_V = END_V
            active = False

        if actual_V > END_V:
            actual_V = END_V
            active = False

        # print(f"{actual_V:0.3f}V {1000 * (duration_actual_s):0.1f}ms")
        list_time_ms.append(1000 * duration_actual_s)
        list_ramp_V.append(actual_V)
        mtx.ad3.supply_P.V = actual_V

    print(f"{steps=} {1000 * (END_V - BEGIN_V) / steps:0.1f}mV/step")
    return pandas.DataFrame(
        {
            "time_ms": list_time_ms,
            "voltage_v": list_ramp_V,
            "signal": "VCC",
        }
    )


def main():
    ramp_duration_s = 0.2

    with MeasureContext() as mtx:
        supply_pos_eff_V = mtx.power_off(supply_V=BEGIN_V)
        print(f"supply_pos_eff_V={supply_pos_eff_V:0.3f}V")

        scope = Scope(ad3=mtx.ad3)
        scope.channel0.setup()
        scope.channel1.setup()
        # scope.setup_trigger(level_V=TRIGGER_V, duration_s=1.5*ramp_duration_s)
        scope.setup_immediate(duration_s=EXPERIMENT_DURATION_S + ramp_duration_s)

        if False:
            digital_input = mtx.ad3.device.digital_input
            digital_input.setup_trigger(source="none")
            digital_input.setup_acquisition(
                mode="single",
                sample_rate=100_000.0,
                sample_format=8,
                buffer_size=10_000,
                configure=True,
            )

            digital_input.configure(start=True)

        if False:
            print("Scope: Arm")
            scope.arm_trigger()
            print("Scope: Armed")

        print("Scope: Start")
        mtx.ad3.scope.configure(reconfigure=True, start=True)

        # ramp_by_step_duration(mtx=mtx, ramp_duration_s=0.5)
        ramp_data = ramp_fast(mtx=mtx, ramp_duration_s=ramp_duration_s)

        if False:
            digital_input.wait_for_status(dwfpy.Status.DONE, read_data=True)
            digital_samples = digital_input.get_data()
            digital_sample_rate_hz = digital_input.sample_rate
            digital_recording_path = constants.DIRECTORY_TESTRESULTS / "digital_io.csv"
            with digital_recording_path.open("w", encoding="ascii", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(("time_s", "digital_0", "digital_1"))
                writer.writerows(
                    (
                        index / digital_sample_rate_hz,
                        int(sample) & 1,
                        (int(sample) >> 1) & 1,
                    )
                    for index, sample in enumerate(digital_samples)
                )
            print(f"Digital recording saved to {digital_recording_path}")

        status = mtx.ad3.scope.read_status(read_data=False)
        print(f"Scope wait... status={status}")
        assert status in (
            dwfpy.Status.TRIGGERED,
            dwfpy.Status.PREFILL,
            dwfpy.Status.DONE,
        )

        mtx.ad3.scope.wait_for_status(dwfpy.Status.DONE, read_data=True)
        scope.save(
            filename=constants.DIRECTORY_TESTRESULTS / "scope.html", ramp_data=ramp_data
        )


if __name__ == "__main__":
    main()
