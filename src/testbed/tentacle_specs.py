from __future__ import annotations

from octoprobe import util_mcu_pyboard, util_mcu_rp2

from testbed.constants import EnumFut, EnumTentacleType

from .tentacle_spec import McuConfig, TentacleSpecMicropython

LOLIN_D1_MINI = TentacleSpecMicropython(
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
    tentacle_tag="LOLIN_D1_MINI",
    futs=[
        EnumFut.FUT_MCU_ONLY,
        EnumFut.FUT_EXTMOD_HARDWARE,
        EnumFut.FUT_WLAN,
    ],
    tags="board=ESP8266_GENERIC,build_variants=:FLASH_512K,mcu=esp8266,programmer=esptool",
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


LOLIN_C3_MINI = TentacleSpecMicropython(
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
    tags="board=LOLIN_C3_MINI,mcu=esp32,programmer=esptool",
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


UM_TINYPICO = TentacleSpecMicropython(
    doc="""
ESP32_GENERIC firmware using UM_TINYPICO board
See: https://www.tinypico.com/

Connections

* GND
  * Board GND <=> Tentacle GND

* FUT_EXTMOD_HARDWARE
  * Board 4 <=> Board 5

* Testpoints
  * Testpoint "GND" <=> Tentacle GND
  * Testpoint "extmod" <=> Board 4
""",
    tentacle_type=EnumTentacleType.TENTACLE_MCU,
    tentacle_tag="UM_TINYPICO",
    futs=[
        EnumFut.FUT_MCU_ONLY,
        EnumFut.FUT_EXTMOD_HARDWARE,
        # could get these from board.json
        EnumFut.FUT_WLAN,
        EnumFut.FUT_BLE,
    ],
    # mcu_usb_id=,
    tags="board=ESP32_GENERIC,mcu=esp32,programmer=esptool",
    programmer_args=[
        "--chip=esp32",
        "--baud=921600",
        "--port=<port>",
        # PROGRAMMER.PORT,
        "write_flash",
        "--compress",
        "0x1000",
        # PROGRAMMER.FIRMWARE_BIN,
        "<firmware.bin>",
    ],
    mcu_config=McuConfig(),
)


ESP32_GENERIC_C3 = TentacleSpecMicropython(
    doc="""
ESP32_GENERIC_C3 firmware on Lolin C3 Mini
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
    tentacle_tag="ESP32_GENERIC_C3",
    futs=[
        EnumFut.FUT_MCU_ONLY,
        EnumFut.FUT_EXTMOD_HARDWARE,
        EnumFut.FUT_WLAN,
        EnumFut.FUT_BLE,
    ],
    tags="programmer=esptool",
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


UM_FEATHERS2 = TentacleSpecMicropython(
    doc="""
See: https://feathers2.io/

Connections

* GND
  * Board GND <=> Tentacle GND

* FUT_EXTMOD_HARDWARE
  * Board 4 <=> Board 5

* Testpoints
  * Testpoint "GND" <=> Tentacle GND
  * Testpoint "extmod" <=> Board 4
""",
    tentacle_type=EnumTentacleType.TENTACLE_MCU,
    tentacle_tag="UM_FEATHERS2",
    futs=[
        EnumFut.FUT_MCU_ONLY,
        EnumFut.FUT_EXTMOD_HARDWARE,
        EnumFut.FUT_WLAN,
    ],
    # TODO: board_variants=ESP32_GENERIC_S2:UM_FEATHERS2
    tags="mcu=esp32,programmer=esptool",
    programmer_args=[
        "--chip=esp32s2",
        "--port <port>",
        "write_flash",
        "-z",
        "0x1000",
        "<firmware.bin>",
    ],
    mcu_config=McuConfig(),
)


UM_FEATHERS3 = TentacleSpecMicropython(
    doc="""
See: https://feathers3.io

Connections

* GND
  * Board GND <=> Tentacle GND

* FUT_EXTMOD_HARDWARE
  * Board 4 <=> Board 5

* Testpoints
  * Testpoint "GND" <=> Tentacle GND
  * Testpoint "extmod" <=> Board 4
""",
    tentacle_type=EnumTentacleType.TENTACLE_MCU,
    tentacle_tag="UM_FEATHERS3",
    futs=[
        EnumFut.FUT_MCU_ONLY,
        EnumFut.FUT_EXTMOD_HARDWARE,
        EnumFut.FUT_WLAN,
        EnumFut.FUT_BLE,
    ],
    # TODO: board=ESP32_GENERIC_S3:UM_FEATHERS3
    tags="mcu=esp32,programmer=esptool",
    programmer_args=[
        "--chip=esp32s3",
        "--port <port>",
        "write_flash",
        "-z",
        "0x0",
        "<firmware.bin>",
    ],
    mcu_config=McuConfig(),
)


TEENSY40 = TentacleSpecMicropython(
    doc="""
See: https://www.pjrc.com/store/teensy40.html

Connections

* GND
  * Board GND <=> Tentacle GND

* FUT_EXTMOD_HARDWARE
  * Board D0 <=> D1
  * Board D2 <=> D3
  * Board D11 <=> D12

* Testpoints
  * Testpoint "GND" <=> Tentacle GND
  * Testpoint "extmod" <=> Board D0
""",
    tentacle_type=EnumTentacleType.TENTACLE_MCU,
    tentacle_tag="TEENSY40",
    futs=[
        EnumFut.FUT_MCU_ONLY,
        EnumFut.FUT_EXTMOD_HARDWARE,
    ],
    tags="mcu=mimxrt,programmer=teensy_loader_cli",
    # TODO: need to work out how to get it into bootloader mode automatically
    programmer_args=[
        "--mcu=imxrt1062",
        "-v",
        "<firmware.hex>",
    ],
    mcu_config=McuConfig(),
)

RPI_PICO = TentacleSpecMicropython(
    doc="""
See: https://micropython.org/download/RPI_PICO

Connections: The same as EnumTentacleTag.MCU_RPI_PICO2W
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

RPI_PICO2 = TentacleSpecMicropython(
    doc="""
See: https://www.raspberrypi.com/documentation/microcontrollers/pico-series.html#raspberry-pi-pico-2-w24

Connections: The same as EnumTentacleTag.MCU_RPI_PICO2W
""",
    tentacle_type=EnumTentacleType.TENTACLE_MCU,
    tentacle_tag="RPI_PICO2",
    futs=[
        EnumFut.FUT_MCU_ONLY,
        EnumFut.FUT_EXTMOD_HARDWARE,
    ],
    mcu_usb_id=util_mcu_rp2.RPI_PICO2_USB_ID,
    tags="build_variants=:RISCV,mcu=rp2,programmer=picotool",
    mcu_config=McuConfig(),
)

RPI_PICO2W = TentacleSpecMicropython(
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
    tentacle_tag="RPI_PICO2W",
    futs=[
        EnumFut.FUT_MCU_ONLY,
        EnumFut.FUT_EXTMOD_HARDWARE,
        EnumFut.FUT_WLAN,
        EnumFut.FUT_BLE,
    ],
    mcu_usb_id=util_mcu_rp2.RPI_PICO2_USB_ID,
    tags="build_variants=:RISCV,mcu=rp2,programmer=picotool",
    mcu_config=McuConfig(),
)


ADAFRUIT_ITSYBITSY_M0_EXPRESS = TentacleSpecMicropython(
    doc="""
See: https://www.adafruit.com/product/3727

TODO: Connections
""",
    tentacle_type=EnumTentacleType.TENTACLE_MCU,
    tentacle_tag="ADAFRUIT_ITSYBITSY_M0_EXPRESS",
    futs=[
        EnumFut.FUT_MCU_ONLY,
        EnumFut.FUT_EXTMOD_HARDWARE,
    ],
    # mcu_usb_id=,
    tags="mcu=samd,programmer=msc",
    # -  Push the reset button twice or call machine.bootloader(). A drive
    #   icon should appear representing a virtual drive.
    # -  Copy the .uf2 file with the required firmware to that drive.
    mcu_config=McuConfig(),
)


PYBV11 = TentacleSpecMicropython(
    doc="""
See: https://micropython.org/download/PYBV11/

Connections

* Bootmode
  * Board BOOT0 <=> Tentacle Relay 1b
  * Tentacle Relay 1a <=> Board +3V3

* GND
  * Board GND <=> Tentacle GND

* FUT_EXTMOD_HARDWARE
  * Board X1 <=> Board X2

* Testpoints
  * Testpoint "GND" <=> Tentacle GND
  * Testpoint "extmod" <=> Board X1
""",
    tentacle_type=EnumTentacleType.TENTACLE_MCU,
    tentacle_tag="PYBV11",
    futs=[
        EnumFut.FUT_MCU_ONLY,
        EnumFut.FUT_EXTMOD_HARDWARE,
    ],
    mcu_usb_id=util_mcu_pyboard.PYBOARD_USB_ID,
    tags="build_variants=:DP:THREAD:DP_THREAD,mcu=stm32,programmer=dfu-util",
    mcu_config=McuConfig(),
)


PYBLITEV10 = TentacleSpecMicropython(
    doc="""
See: https://store.micropython.org/product/PYBLITEv1.0

Connections: same as PYBV11
""",
    tentacle_type=EnumTentacleType.TENTACLE_MCU,
    tentacle_tag="PYBLITEV10",
    futs=[
        EnumFut.FUT_MCU_ONLY,
        EnumFut.FUT_EXTMOD_HARDWARE,
    ],
    tags="mcu=stm32,programmer=dfu-util",
    mcu_config=McuConfig(),
)


PYBD_SF2 = TentacleSpecMicropython(
    doc="""
See: https://store.micropython.org/product/PYBD-SF2-W4F2

Connections: same as PYBV11
""",
    tentacle_type=EnumTentacleType.TENTACLE_MCU,
    tentacle_tag="PYBD_SF2",
    futs=[
        EnumFut.FUT_MCU_ONLY,
        EnumFut.FUT_EXTMOD_HARDWARE,
        EnumFut.FUT_WLAN,
        EnumFut.FUT_BLE,
    ],
    tags="mcu=stm32,programmer=dfu-util",
    mcu_config=McuConfig(),
)


PYBD_SF6 = TentacleSpecMicropython(
    doc="""
See: https://store.micropython.org/product/PYBD-SF6-W4F2

Connections: same as PYBV11
""",
    tentacle_type=EnumTentacleType.TENTACLE_MCU,
    tentacle_tag="PYBD_SF6",
    futs=[
        EnumFut.FUT_MCU_ONLY,
        EnumFut.FUT_EXTMOD_HARDWARE,
        EnumFut.FUT_WLAN,
        EnumFut.FUT_BLE,
    ],
    tags="mcu=stm32,programmer=dfu-util",
    mcu_config=McuConfig(),
)
