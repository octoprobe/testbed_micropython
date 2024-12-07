from __future__ import annotations

import dataclasses
import enum

from octoprobe import util_mcu_esp32C3, util_mcu_esp8266, util_mcu_pyboard, util_mcu_rp2
from octoprobe.util_baseclasses import TentacleSpec

from testbed.constants import TentacleType


class EnumTentacleTag(enum.StrEnum):
    MCU_LOLIN_C3_MINI = "lolin_C3"
    MCU_LOLIN_D1_MINI = "lolin_D1"
    MCU_PYBV11 = "pybv11"
    MCU_RPI_PICO = "pico"
    MCU_RPI_PICO2 = "pico2"
    MCU_RPI_PICO2W = "pico2W"


class EnumFut(enum.StrEnum):
    FUT_MCU_ONLY = enum.auto()
    """
    Do not provide a empty list, use FUT_MCU_ONLY instead!
    """
    FUT_EXTMOD_HARDWARE = enum.auto()
    """
    rx-tx loopback connection
    """
    FUT_WLAN_STA = enum.auto()
    FUT_WLAN_AP = enum.auto()
    FUT_BLE = enum.auto()


@dataclasses.dataclass
class McuConfig:
    """
    These variables will be replaced in micropython code
    """


tentacle_spec_mcu_pybv11 = TentacleSpec(
    doc="""
See: https://github.com/octoprobe/testbed_tutorial/tree/main/docs/tentacle_MCU_PYBV11

TODO: Connections
""",
    tentacle_type=TentacleType.TENTACLE_MCU,
    tentacle_tag=EnumTentacleTag.MCU_PYBV11,
    futs=[
        EnumFut.FUT_MCU_ONLY,
        EnumFut.FUT_EXTMOD_HARDWARE,
    ],
    mcu_usb_id=util_mcu_pyboard.PYBOARD_USB_ID,
    tags="boards=PYBV11:PYBV11-DP:PYBV11-THREAD:PYBV11-DP_THREAD,mcu=stm32,programmer=dfu-util",
    mcu_config=McuConfig(),
)


tentacle_spec_mcu_rpi_pico = TentacleSpec(
    doc="""
See: https://github.com/octoprobe/testbed_tutorial/tree/main/docs/tentacle_MCU_RPI_PICO

Connections: The same as EnumTentacleTag.MCU_RPI_PICO2W
""",
    tentacle_type=TentacleType.TENTACLE_MCU,
    tentacle_tag=EnumTentacleTag.MCU_RPI_PICO,
    futs=[
        EnumFut.FUT_MCU_ONLY,
        EnumFut.FUT_EXTMOD_HARDWARE,
    ],
    mcu_usb_id=util_mcu_rp2.RPI_PICO_USB_ID,
    tags="boards=RPI_PICO,mcu=rp2,programmer=picotool",
    mcu_config=McuConfig(),
)


tentacle_spec_mcu_rpi_pico2w = TentacleSpec(
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
    tentacle_type=TentacleType.TENTACLE_MCU,
    tentacle_tag=EnumTentacleTag.MCU_RPI_PICO2W,
    futs=[
        EnumFut.FUT_MCU_ONLY,
        EnumFut.FUT_EXTMOD_HARDWARE,
        EnumFut.FUT_WLAN_STA,
        EnumFut.FUT_WLAN_AP,
        EnumFut.FUT_BLE,
    ],
    mcu_usb_id=util_mcu_rp2.RPI_PICO2_USB_ID,
    tags="boards=RPI_PICO2:RPI_PICO2-RISCV,mcu=rp2,programmer=picotool",
    mcu_config=McuConfig(),
)

tentacle_spec_mcu_lolin_d1_mini = TentacleSpec(
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
    tentacle_type=TentacleType.TENTACLE_MCU,
    tentacle_tag=EnumTentacleTag.MCU_LOLIN_D1_MINI,
    futs=[
        EnumFut.FUT_MCU_ONLY,
        EnumFut.FUT_EXTMOD_HARDWARE,
        EnumFut.FUT_WLAN_STA,
        EnumFut.FUT_WLAN_AP,
        EnumFut.FUT_BLE,
    ],
    mcu_usb_id=util_mcu_esp8266.LOLIN_D1_MINI_USB_ID,
    tags="boards=ESP8266_GENERIC,mcu=esp8266,programmer=esptool",
    micropython_perftest_args=["50", "36"],
    programmer_args=[
        "--baud=1000000",
        "write_flash",
        "--flash_size=4MB",
        "--flash_mode=dio",
        "0",
    ],
    mcu_config=McuConfig(),
)


tentacle_spec_mcu_lolin_c3_mini = TentacleSpec(
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
    tentacle_type=TentacleType.TENTACLE_MCU,
    tentacle_tag=EnumTentacleTag.MCU_LOLIN_C3_MINI,
    futs=[
        EnumFut.FUT_MCU_ONLY,
        EnumFut.FUT_EXTMOD_HARDWARE,
        EnumFut.FUT_WLAN_STA,
        EnumFut.FUT_WLAN_AP,
        EnumFut.FUT_BLE,
    ],
    mcu_usb_id=util_mcu_esp32C3.LOLIN_C3_MINI_USB_ID,
    tags="boards=LOLIN_C3_MINI,mcu=esp32,programmer=esptool",
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

TENTACLES_SPECS: dict[str, TentacleSpec] = {
    tentacle_spec.tentacle_tag: tentacle_spec
    for tentacle_spec in (
        tentacle_spec_mcu_pybv11,
        tentacle_spec_mcu_rpi_pico,
        tentacle_spec_mcu_rpi_pico2w,
        tentacle_spec_mcu_lolin_d1_mini,
        tentacle_spec_mcu_lolin_c3_mini,
    )
}
