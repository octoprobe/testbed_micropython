from __future__ import annotations

import logging
import pathlib

import altair
import dwfpy
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

    def setup(self) -> None:
        # seld.ad3.scope.setup_edge_trigger(
        #     channel=0,
        #     slope="rising",
        #     level=0.75,
        #     position=0.01,
        #     mode="auto",
        # )
        self.ad3.scope.setup_edge_trigger(
            channel=0,
            slope="rising",
            level=1.5,
            position=0.0,
            mode="normal",
            # mode="auto",
        )
        self.ad3.scope.setup_acquisition(
            mode="single",
            sample_rate=2e5,
            buffer_size=16384,
            configure=True,
        )


    def save(self, filename: pathlib.Path) -> None:
        sample_rate_hz = self.ad3.device.analog_input.frequency
        scope_data = []
        for channel, signal_name in (
            (self.channel0, "RST"),
            (self.channel1, "BOOT"),
        ):
            samples = channel.channel.get_data()
            scope_data.extend(
                {
                    "time_ms": index / sample_rate_hz * 1000.0 - 10.0,
                    "voltage_v": float(voltage),
                    "signal": signal_name,
                }
                for index, voltage in enumerate(samples)
            )
        chart = (
            altair.Chart(altair.Data(values=scope_data))
            .mark_line()
            .encode(
                x=altair.X("time_ms:Q", title="Time from ramp start (ms)"),
                y=altair.Y("voltage_v:Q", title="Scope voltage (V)"),
                color=altair.Color(
                    "signal:N",
                    scale=altair.Scale(
                        domain=["RST", "BOOT"],
                        range=["#f28e2b", "#808080"],
                    ),
                    legend=altair.Legend(title="Signal"),
                ),
            )
            .properties(title="Positive supply ramp", width=800, height=400)
        )
        chart.save(filename)
        print(f"Scope chart saved to {filename}")


class MeasureContext:
    def __init__(self):
        self.device: dwfpy.Device
        self.ad3: dwfpy_ad3.AD3

    def open(self):
        self.device = dwfpy.Device()
        self.device.open()
        logger.info(f"Found device: {self.device.name} ({self.device.serial_number})")
        self.ad3 = dwfpy_ad3.AD3(device=self.device)
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
