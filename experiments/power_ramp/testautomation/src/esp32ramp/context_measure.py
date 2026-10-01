from __future__ import annotations

import logging
import pathlib
import time

import altair
import dwfpy
import numpy
import pandas
from dwfpy_ad3 import dwfpy_ad3

logger = logging.getLogger(__file__)
SKIP_VOLTMETER_CALIBRATION = False


class ScopeChannel:
    def __init__(self, scope: Scope, channel0: int) -> None:
        self.scope = scope
        self.channel0 = channel0
        self.channel = dwfpy_ad3.ScopeIdx(ad3=self.scope.ad3, idx=self.channel0)

    def setup(self) -> None:
        self.channel.setup(
            range=10.0,
            offset=0.0,
            coupling="dc",
        )


class Scope:
    def __init__(self, ad3: dwfpy_ad3.AD3) -> None:
        self.ad3 = ad3
        self.channel0 = ScopeChannel(scope=self, channel0=0)
        self.channel1 = ScopeChannel(scope=self, channel0=1)

    def setup_trigger(self, level_V: float, duration_s: float) -> None:
        assert isinstance(level_V, float)
        assert isinstance(duration_s, float)

        buffer_size = 16384
        sample_rate = buffer_size / duration_s

        self.ad3.scope.setup_edge_trigger(
            channel=0,
            slope="rising",
            level=level_V,
            position=duration_s / 3.0,
            mode="normal",
            hold_off=None,
            hysteresis=None,
            # mode="auto",
        )
        self.ad3.scope.setup_acquisition(
            mode="single",
            sample_rate=sample_rate,
            buffer_size=buffer_size,
        )

    def setup_immediate(self, duration_s: float) -> None:
        assert isinstance(duration_s, float)

        buffer_size = 16384
        sample_rate = buffer_size / duration_s

        # No trigger: acquisition starts right after `configure(start=True)`.
        self.ad3.scope.ai.trigger.source = dwfpy.TriggerSource.NONE
        self.ad3.scope.setup_acquisition(
            mode="single",
            sample_rate=sample_rate,
            buffer_size=buffer_size,
        )

    def arm_trigger(self) -> None:
        self.ad3.scope.configure(reconfigure=True, start=True)
        while True:
            status = self.ad3.scope.read_status(read_data=False)
            if status == dwfpy.Status.ARMED:
                break

    def save(self, filename: pathlib.Path, ramp_data: pandas.DataFrame) -> None:
        assert isinstance( filename, pathlib.Path)
        assert isinstance(ramp_data, pandas.DataFrame)

        sample_rate_hz = self.ad3.device.analog_input.frequency
        frames: list[pandas.DataFrame] = [ramp_data]
        for channel, signal_name in (
            (self.channel0, "RST"),
            (self.channel1, "BOOT"),
        ):
            samples = numpy.asarray(channel.channel.get_data(), dtype=float)
            time_ms = numpy.arange(samples.size) / sample_rate_hz * 1000.0 - 10.0
            frames.append(
                pandas.DataFrame(
                    {
                        "time_ms": time_ms,
                        "voltage_v": samples,
                        "signal": signal_name,
                    }
                )
            )
        scope_data = pandas.concat(frames, ignore_index=True)
        chart = (
            altair.Chart(scope_data)
            .mark_line()
            .encode(
                x=altair.X("time_ms:Q", title="Time from ramp start (ms)"),
                y=altair.Y("voltage_v:Q", title="Scope voltage (V)"),
                color=altair.Color(
                    "signal:N",
                    scale=altair.Scale(
                        domain=["RST", "BOOT", "VCC"],
                        range=["#f28e2b", "#808080", "#000000"],
                    ),
                    legend=altair.Legend(title="Signal"),
                ),
            )
            .properties(title="Positive supply ramp", width=800, height=400)
        )
        chart.save(filename)
        print(f"Scope chart saved to {filename}")


class MeasureContext:
    def __init__(self) -> None:
        self.device: dwfpy.Device
        self.ad3: dwfpy_ad3.AD3
        self.supplyPos: dwfpy.analog_io.AnalogIoChannelNode

    def open(self):
        self.device = dwfpy.Device()
        self.device.open()
        logger.info(f"Found device: {self.device.name} ({self.device.serial_number})")
        self.ad3 = dwfpy_ad3.AD3(device=self.device)
        self.supplyPos = self.device.analog_io["V+"]["Voltage"]
        assert isinstance(self.supplyPos, dwfpy.analog_io.AnalogIoChannelNode)
        self.init()

    def close(self):
        self.device.close()

    def __enter__(self):
        """
        Used for: with MeasureContext() as mxt
        """
        self.open()
        return self

    def __exit__(self, exception_type, exception_value, traceback) -> None:
        """
        Used for: with MeasureContext() as mxt
        """
        del exception_type, exception_value, traceback
        self.close()

    def init(self, switch=True, relais=True, AWG=True) -> None:
        power_supply = self.ad3.device.analog_io["V+-"]
        power_supply["Limit"].value = 1.0
        self.ad3.device.analog_io.configure()

        self.ad3.supply_N.enable = False
        self.ad3.supply_P.enable = False
        if switch:
            switch_liste = list(range(0, 4)) + list(range(8, 16))
            for i in switch_liste:
                """alle digital_io auf False"""
                self.ad3.device.digital_io[i].setup(
                    enabled=True, state=False, configure=True
                )
        if relais:
            self.ad3.relais_4.status = None
            self.ad3.relais_6.status = None
            self.ad3.relais_4.value(False)
            self.ad3.relais_6.value(False)
        if AWG:
            self.ad3.awg_1.setup(function="dc", offset=0.0, configure=True, start=True)
            self.ad3.awg_2.setup(function="dc", offset=0.0, configure=True, start=True)

    def supply_pos_eff_V(self) -> float:
        self.device.analog_io.read_status()
        return self.supplyPos.status

    def power_off(self, supply_V: float) -> float:
        """
        Make sure power is off so trigger happens
        """
        self.ad3.supply_P.V = supply_V
        self.ad3.supply_P.enable = False
        while True:
            supply_pos_eff_V = self.supply_pos_eff_V()
            if supply_pos_eff_V < supply_V / 2.0:
                return supply_pos_eff_V
            time.sleep(0.1)
