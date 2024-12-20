from __future__ import annotations

import dataclasses

from octoprobe import util_mcu_esp32C3, util_mcu_esp8266, util_mcu_pyboard, util_mcu_rp2
from octoprobe.util_baseclasses import TentacleSpec

from testbed.constants import EnumFut, EnumTentacleType


@dataclasses.dataclass
class McuConfig:
    """
    These variables will be replaced in micropython code
    """

    micropython_perftest_args: list[str] | None = None

    def __post_init__(self) -> None:
        assert isinstance(self.micropython_perftest_args, list | None)


PYBV11 = TentacleSpec(
    doc="""
See: https://github.com/octoprobe/testbed_tutorial/tree/main/docs/tentacle_MCU_PYBV11

TODO: Connections
""",
    tentacle_type=EnumTentacleType.TENTACLE_MCU,
    tentacle_tag="PYBV11",
    futs=[
        EnumFut.FUT_MCU_ONLY,
        EnumFut.FUT_EXTMOD_HARDWARE,
    ],
    mcu_usb_id=util_mcu_pyboard.PYBOARD_USB_ID,
    tags="variants=:DP:THREAD:DP_THREAD,mcu=stm32,programmer=dfu-util",
    mcu_config=McuConfig(),
)


RPI_PICO = TentacleSpec(
    doc="""
See: https://github.com/octoprobe/testbed_tutorial/tree/main/docs/tentacle_MCU_RPI_PICO

Connections: The same as "MCU_RPI_PICO2W
""",
    tentacle_type=EnumTentacleType.TENTACLE_MCU,
    tentacle_tag="RPI_PICO",
    futs=[
        EnumFut.FUT_MCU_ONLY,
        EnumFut.FUT_EXTMOD_HARDWARE,
    ],
    mcu_usb_id=util_mcu_rp2.RPI_PICO_USB_ID,
    tags="mcu=rp2,programmer=picotool",
    mcu_config=McuConfig(),
)


RPI_PICO2 = TentacleSpec(
    doc="""
See: https://www.raspberrypi.com/documentation/microcontrollers/pico-series.html#raspberry-pi-pico-2-w24

Connections

* Bootmode
  * Board TP6 (Bootsel) <=> Tentacle Relay 1b
  * Tentacle Relay 1a <=> Tentacle GND

* GND
  * Board GND <=> Tentacle GND

* FUT_EXTMOD_HARDWARE
  * Board GPIO0 <=> Board GPIO1

* Testpoints
  * Testpoint "GND" <=> Tentacle GND
  * Testpoint "extmod" <=> Board GPIO0
""",
    tentacle_type=EnumTentacleType.TENTACLE_MCU,
    tentacle_tag="RPI_PICO2",
    futs=[
        EnumFut.FUT_MCU_ONLY,
        EnumFut.FUT_EXTMOD_HARDWARE,
    ],
    mcu_usb_id=util_mcu_rp2.RPI_PICO2_USB_ID,
    tags="variants=:RISCV,mcu=rp2,programmer=picotool",
    mcu_config=McuConfig(),
)

ESP8266_GENERIC = TentacleSpec(
    doc="""
See: https://www.wemos.cc/en/latest/d1/d1_mini.html
See: https://www.wemos.cc/en/latest/tutorials/d1/get_started_with_micropython_d1.html

Connections

* GND
  * Board GND <=> Tentacle GND

* FUT_EXTMOD_HARDWARE
  * Board D1/5/rx <=> Board D2/4/tx

* Testpoints
  * Testpoint "GND" <=> Tentacle GND
  * Testpoint "extmod" <=> Board D1/5/rx
""",
    tentacle_type=EnumTentacleType.TENTACLE_MCU,
    tentacle_tag="ESP8266_GENERIC",
    futs=[
        EnumFut.FUT_MCU_ONLY,
        EnumFut.FUT_EXTMOD_HARDWARE,
        EnumFut.FUT_WLAN,
    ],
    mcu_usb_id=util_mcu_esp8266.LOLIN_D1_MINI_USB_ID,
    tags="mcu=esp8266,programmer=esptool",
    programmer_args=[
        "--baud=1000000",
        "write_flash",
        "--flash_size=4MB",
        "--flash_mode=dio",
        "0",
    ],
    mcu_config=McuConfig(
        micropython_perftest_args=["50", "36"],
    ),
)


LOLIN_C3_MINI = TentacleSpec(
    doc="""
See: https://www.wemos.cc/en/latest/c3/c3_mini.html

Connections

* GND
  * Board GND <=> Tentacle GND

* FUT_EXTMOD_HARDWARE
  * Board 5/U0RXD/RX <=> 4/U0TXD/TX

* Testpoints
  * Testpoint "GND" <=> Tentacle GND
  * Testpoint "extmod" <=> Board 5/U0RXD/RX
""",
    tentacle_type=EnumTentacleType.TENTACLE_MCU,
    tentacle_tag="LOLIN_C3_MINI",
    futs=[
        EnumFut.FUT_MCU_ONLY,
        EnumFut.FUT_EXTMOD_HARDWARE,
        EnumFut.FUT_WLAN,
        EnumFut.FUT_BLE,
    ],
    mcu_usb_id=util_mcu_esp32C3.LOLIN_C3_MINI_USB_ID,
    tags="mcu=esp32,programmer=esptool",
    programmer_args=[
        "--chip=esp32c3",
        "--baud=460800",
        "--before=default_reset",
        "--after=hard_reset",
        "write_flash",
        "-z",
        "0x0",
    ],
    mcu_config=McuConfig(),
)
