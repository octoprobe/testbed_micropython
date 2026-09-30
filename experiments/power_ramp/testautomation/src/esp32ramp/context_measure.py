from __future__ import annotations

import logging

import dwfpy
from dwfpy_ad3 import dwfpy_ad3

logger = logging.getLogger(__file__)
SKIP_VOLTMETER_CALIBRATION = False


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
