"""
*: Board suggested for testbed_ch_hans_1

class EnumTentacleTag(enum.StrEnum):
    # esp32
    ESP32_GENERIC = enum.auto()
*   ESP32_GENERIC_C3 = enum.auto()  # Lolin C3 Mini
    #ESP32_GENERIC_C6 = enum.auto() TODO
    UM_FEATHERS2 = enum.auto()
*   ESP32_GENERIC_S3 = enum.auto()  # ESP32-S3-DevKitC-1-N8R8
    # esp8266
*   LOLIN_D1_MINI = enum.auto()
    # mimxrt
*   TEENSY40 = enum.auto()
    # nrf
*   ARDUINO_NANO_33_BLE_SENSE = enum.auto()
    # renesas-ra
    #EK_RA6M # (with UART REPL on P411/P410)
    # rp2
*   RPI_PICO = enum.auto()
    RPI_PICO_W = enum.auto()                WLAN BLE
*   RPI_PICO2 = enum.auto() RISCV
*   RPI_PICO2_W = enum.auto() RISCV         WLAN BLE
    # samd
*   ADAFRUIT_ITSYBITSY_M0_EXPRESS = enum.auto()
    # stm32
*   PYBV11 = enum.auto()
    PYBLITEV10 = enum.auto()
    PYBD_SF2 = enum.auto()
    PYBD_SF6 = enum.auto()

12pin Testpoints
----------------
These connectors match with https://github.com/WeActStudio/LogicAnalyzerV1.
These are the pins looking towards a connector soldered to a tentacle:
  GND, CH3, CH2, CH1, CH0, GND - top row, from left to right
  GND, CH7, CH6, CH5, CH4, CND - bottom row, from left to right

Assignments
  CH0: Trigger (not defined yet which gpio to use)
  CH1: extmod_a (signals for FUT_EXTMOD_HARDWARE)
  CH2: extmod_b (signals for FUT_EXTMOD_HARDWARE)
  CH3: extmod_c (signals for FUT_EXTMOD_HARDWARE)
"""

from __future__ import annotations

from octoprobe import (
    util_mcu_mimxrt,
    util_mcu_nrf,
    util_mcu_pico,
    util_mcu_pyboard,
    util_mcu_samd,
)

from .constants import EnumFut, EnumTentacleType
from .tentacle_spec import McuConfig, TentacleSpecMicropython

AA_UNASSEMBLED = TentacleSpecMicropython(
    doc="""This tentacle has not been assembled yet""",
    tentacle_type=EnumTentacleType.TENTACLE_MCU,
    tentacle_tag="",
    futs=[],
    tags="",
)

ADA_ITSYBITSY_M0 = TentacleSpecMicropython(
    doc="""
See: https://www.adafruit.com/product/3727
See: https://learn.adafruit.com/introducing-itsy-bitsy-m0
See: https://cdn-learn.adafruit.com/assets/assets/000/110/623/original/adafruit_products_Adafruit_ItsyBitsy_M0_pinout.png
See: https://micropython.org/download/ADAFRUIT_ITSYBITSY_M0_EXPRESS/


* GND
  * Board GND <=> Tentacle GND

* Bootmode
  * Board RESET <=> Tentacle Relay 1b
  * Tentacle Relay 1a <=> Tentacle GND

* FUT_EXTMOD_HARDWARE
  * Board D0 <=> Board D1

* Testpoints
  * Testpoint "GND" <=> Tentacle GND
  * Testpoint CH0/trigger <=> Board TODO
  * Testpoint CH1/extmod_a <=> Board D0
""",
    tentacle_type=EnumTentacleType.TENTACLE_MCU,
    tentacle_tag="ADA_ITSYBITSY_M0",  # ADAFRUIT_ITSYBITSY_M0_EXPRESS
    futs=[
        EnumFut.FUT_MCU_ONLY,
        EnumFut.FUT_EXTMOD_HARDWARE,
    ],
    mcu_usb_id=util_mcu_samd.ADAFRUIT_ITSYBITSY_M0_EXPRESS_USB_ID,
    tags="board=ADAFRUIT_ITSYBITSY_M0_EXPRESS,mcu=samd,programmer=samd_bossac",
    programmer_args=["--offset=0x2000"],
    # -  Push the reset button twice or call machine.bootloader(). A drive
    #   icon should appear representing a virtual drive.
    # -  Copy the .uf2 file with the required firmware to that drive.
    mcu_config=McuConfig(),
)


ARDUINO_NANO_33 = TentacleSpecMicropython(
    doc="""
See: https://www.wemos.cc/en/latest/d1/d1_mini.html
See: https://www.wemos.cc/en/latest/tutorials/d1/get_started_with_micropython_d1.html

TODO: State of the board
TODO: Programming (double tabbing the boot button) works but should be heavely tested
TODO: RUN-TESTS_STANDARD: The board crashes
TODO: RUN-TESTS_EXTMOD_HARDWARE: Not tested and no gpios connected
Connections

* Bootmode
  * Board RESET  <=> Tentacle Relay 1b
  * Tentacle Relay 1a <=> Tentacle GND

* GND
  * Board GND <=> Tentacle GND

* FUT_EXTMOD_HARDWARE
  * TODO

* Testpoints
  * Testpoint "GND" <=> Tentacle GND
  * Testpoint CH0/trigger <=> Board TODO
  * Testpoint CH1/extmod_a <=> Board TODO
""",
    tentacle_type=EnumTentacleType.TENTACLE_MCU,
    tentacle_tag="ARDUINO_NANO_33",
    futs=[
        EnumFut.FUT_MCU_ONLY,
        EnumFut.FUT_EXTMOD_HARDWARE,
    ],
    mcu_usb_id=util_mcu_nrf.ARDUINO_NANO_33_USB_ID,
    tags="board=ARDUINO_NANO_33_BLE_SENSE,mcu=nrf,programmer=bossac",
    programmer_args=["--offset=0x16000"],
    mcu_config=McuConfig(),
)


ESP32_DEVKIT = TentacleSpecMicropython(
    doc="""
See: ESP32-DevKitC V4
See: https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32/esp32-devkitc/user_guide.html

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
    tentacle_tag="ESP32_DEVKIT",
    futs=[
        EnumFut.FUT_MCU_ONLY,
        EnumFut.FUT_EXTMOD_HARDWARE,
        EnumFut.FUT_WLAN,
        EnumFut.FUT_BLE,
    ],
    tags="board=ESP32_GENERIC,mcu=esp32,programmer=esptool",
    programmer_args=[
        "--chip=esp32",
        "--baud=460800",
        "--before=default_reset",
        "--after=hard_reset",
        "write_flash",
        "0x1000",
    ],
    power_on_delay_s=1.0,
    mcu_config=McuConfig(),
)

ESP32_C3_DEVKIT = TentacleSpecMicropython(
    doc="""
TODO: Remove: ESP32_GENERIC_C3 firmware on Lolin C3 Mini
TODO: Remove: See: https://www.wemos.cc/en/latest/c3/c3_mini.html
See: ESP32-C3-DevKitC-02
See: https://docs.espressif.com/projects/esp-idf/en/v5.2/esp32c3/hw-reference/esp32c3/user-guide-devkitc-02.html
See: http://adafru.it/5337

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
    tentacle_tag="ESP32_C3_DEVKIT",
    futs=[
        EnumFut.FUT_MCU_ONLY,
        EnumFut.FUT_EXTMOD_HARDWARE,
        EnumFut.FUT_WLAN,
        EnumFut.FUT_BLE,
    ],
    tags="board=ESP32_GENERIC_C3,mcu=esp32,programmer=esptool",
    programmer_args=[
        "--chip=esp32c3",
        "--baud=921600",
        "--before=default_reset",
        "--after=hard_reset",
        "write_flash",
        "-z",
        "0x0",
    ],
    power_on_delay_s=1.0,
    mcu_config=McuConfig(),
)


ESP32_S3_DEVKIT = TentacleSpecMicropython(
    doc="""
See: Espressif ESP32-S3-DevKitC-1-N8R8
See: https://www.adafruit.com/product/5336
See: https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32s3/esp32-s3-devkitc-1/index.html

Connections

* GND
  * Board GND <=> Tentacle GND

* FUT_EXTMOD_HARDWARE
  * Board GPIO4 <=> Board GPIO5

* Testpoints
  * Testpoint "GND" <=> Tentacle GND
  * Testpoint CH0/trigger <=> Board GPIO6
  * Testpoint CH1/extmod_a <=> Board GPIO4

  v1.0: USB DUT is connected to 'UART'
  v1.1: USB DUT is connected to 'USB'
""",
    tentacle_type=EnumTentacleType.TENTACLE_MCU,
    tentacle_tag="ESP32_S3_DEVKIT",
    futs=[
        EnumFut.FUT_MCU_ONLY,
        EnumFut.FUT_EXTMOD_HARDWARE,
        EnumFut.FUT_WLAN,
        EnumFut.FUT_BLE,
    ],
    # TODO: board=ESP32_GENERIC_S3:UM_FEATHERS3
    tags="board=ESP32_GENERIC_S3,mcu=esp32,programmer=esptool",
    programmer_args=[
        "--baud=921600",
        "--chip=esp32s3",
        "write_flash",
        "-z",
        "0x0",
    ],
    mcu_config=McuConfig(),
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
  * Testpoint CH0/trigger <=> Board 1
  * Testpoint CH1/extmod_a <=> Board 5/U0RXD/RX
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
    power_on_delay_s=1.0,
    mcu_config=McuConfig(
        micropython_perftest_args=["50", "36"],
    ),
)


NUCLEO_WB55 = TentacleSpecMicropython(
    doc="""
See: https://micropython.org/download/NUCLEO_WB55/
See: https://www.st.com/en/evaluation-tools/p-nucleo-wb55.html
See: https://www.st.com/en/evaluation-tools/nucleo-wb55rg.html
See headers: https://os.mbed.com/platforms/ST-Nucleo-WB55RG/
See - old doc, but detailed: https://fcc.report/FCC-ID/YCP-MB1355002/5777411.pdf

Connections

* Bootmode
  * Board CN7-pin7(BOOT0) <=> Tentacle Relay 1b
  * Tentacle Relay 1a <=> Board CN7-pin5(3V3)

* GND
  * Board CN7-pin8(GND) <=> Tentacle GND

* FUT_EXTMOD_HARDWARE
  * Board CN7-pin28(X1/A0) <=> Board CN7-pin30(X2/A1)

* Testpoints
  * Testpoint "GND" <=> Tentacle GND
  * Testpoint CH0/trigger <=> Board TODO
  * Testpoint CH1/extmod_a <=> Board CN7-pin28(X1/A0)

Board setup:
* CN1: USB cable
* JP1: all open. But "USB MCU" closed.
* JP2: closed
* JP3: closed
* JP4: closed
* JP5: all closend. But "GND" open.
* JP6: closed
""",
    tentacle_type=EnumTentacleType.TENTACLE_MCU,
    tentacle_tag="NUCLEO_WB55",
    futs=[
        EnumFut.FUT_MCU_ONLY,
        EnumFut.FUT_EXTMOD_HARDWARE,
    ],
    mcu_usb_id=util_mcu_pyboard.NUCLEO_WB55_USB_ID,
    # TODO: Enable all board variants when issue fixed: https://github.com/micropython/micropython/issues/16498
    # tags="build_variants=:DP:THREAD:DP_THREAD,mcu=stm32,programmer=dfu-util",
    tags="build_variants=,mcu=stm32,programmer=dfu-util",
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
  * Testpoint CH0/trigger <=> Board TODO
  * Testpoint CH1/extmod_a <=> Board X1
""",
    tentacle_type=EnumTentacleType.TENTACLE_MCU,
    tentacle_tag="PYBV11",
    futs=[
        EnumFut.FUT_MCU_ONLY,
        EnumFut.FUT_EXTMOD_HARDWARE,
    ],
    mcu_usb_id=util_mcu_pyboard.PYBOARD_USB_ID,
    # TODO: Enable all board variants when issue fixed: https://github.com/micropython/micropython/issues/16498
    tags="build_variants=:DP:THREAD:DP_THREAD,mcu=stm32,programmer=dfu-util",
    # tags="build_variants=,mcu=stm32,programmer=dfu-util",
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

RPI_PICO = TentacleSpecMicropython(
    doc="""
See: https://micropython.org/download/RPI_PICO

Connections: The same as EnumTentacleTag.MCU_RPI_PICO2_W
""",
    tentacle_type=EnumTentacleType.TENTACLE_MCU,
    tentacle_tag="RPI_PICO",
    futs=[
        EnumFut.FUT_MCU_ONLY,
        EnumFut.FUT_EXTMOD_HARDWARE,
    ],
    mcu_usb_id=util_mcu_pico.RPI_PICO_USB_ID,
    tags="mcu=rp2,programmer=picotool",
    mcu_config=McuConfig(),
)

RPI_PICO_W = TentacleSpecMicropython(
    doc="""
See: https://micropython.org/download/RPI_PICO

Connections: The same as EnumTentacleTag.MCU_RPI_PICO2_W
""",
    tentacle_type=EnumTentacleType.TENTACLE_MCU,
    tentacle_tag="RPI_PICO_W",
    futs=[
        EnumFut.FUT_MCU_ONLY,
        EnumFut.FUT_EXTMOD_HARDWARE,
        EnumFut.FUT_WLAN,
        EnumFut.FUT_BLE,
    ],
    mcu_usb_id=util_mcu_pico.RPI_PICO_USB_ID,
    tags="mcu=rp2,programmer=picotool",
    mcu_config=McuConfig(),
)

RPI_PICO2 = TentacleSpecMicropython(
    doc="""
See: https://www.raspberrypi.com/documentation/microcontrollers/pico-series.html#raspberry-pi-pico-2-w24

Connections: The same as EnumTentacleTag.MCU_RPI_PICO2_W
""",
    tentacle_type=EnumTentacleType.TENTACLE_MCU,
    tentacle_tag="RPI_PICO2",
    futs=[
        EnumFut.FUT_MCU_ONLY,
        EnumFut.FUT_EXTMOD_HARDWARE,
    ],
    mcu_usb_id=util_mcu_pico.RPI_PICO2_USB_ID,
    tags="build_variants=:RISCV,mcu=rp2,programmer=picotool",
    mcu_config=McuConfig(),
)


RPI_PICO2_W = TentacleSpecMicropython(
    doc="""
See: https://www.raspberrypi.com/documentation/microcontrollers/pico-series.html#raspberry-pi-pico-2-w24

Connections

* Bootmode
  * Board TP6 (Bootsel) <=> Tentacle Relay 1b
  * Tentacle Relay 1a <=> Tentacle GND

* GND
  * Board GND <=> Tentacle GND

* FUT_EXTMOD_HARDWARE
  * Board GP0 <=> Board GP1

* Testpoints
  * Testpoint GND <=> Tentacle GND
  * Testpoint CH0/trigger <=> Board GP2
  * Testpoint CH1/extmod_a <=> Board GP0
""",
    tentacle_type=EnumTentacleType.TENTACLE_MCU,
    tentacle_tag="RPI_PICO2_W",
    futs=[
        EnumFut.FUT_MCU_ONLY,
        EnumFut.FUT_EXTMOD_HARDWARE,
        EnumFut.FUT_WLAN,
        EnumFut.FUT_BLE,
    ],
    mcu_usb_id=util_mcu_pico.RPI_PICO2_USB_ID,
    # TODO: No RISCV variant. Why?
    # tags="build_variants=:RISCV,mcu=rp2,programmer=picotool",
    tags="build_variants=,mcu=rp2,programmer=picotool",
    mcu_config=McuConfig(),
)


TEENSY40 = TentacleSpecMicropython(
    doc="""
See: https://www.pjrc.com/store/teensy40.html
See: https://micropython.org/download/TEENSY40
See: https://www.pjrc.com/store/teensy40_card10a_rev2.png

Connections

* GND
  * Board GND <=> Tentacle GND

* Bootmode
  * Board PROGRAM <=> Tentacle Relay 1b
  * Tentacle Relay 1a <=> Tentacle GND

* FUT_EXTMOD_HARDWARE
  * Board D0 <=> Board D1
  * Board D2 <=> Board D3
  * Board D11 <=> Board D12

* Testpoints
  * Testpoint "GND" <=> Tentacle GND
  * Testpoint CH0/trigger <=> Board TODO
  * Testpoint CH1/extmod_a <=> Board D0
  * Testpoint CH1/extmod_b <=> Board D2
  * Testpoint CH1/extmod_c <=> Board D11
""",
    tentacle_type=EnumTentacleType.TENTACLE_MCU,
    tentacle_tag="TEENSY40",
    futs=[
        EnumFut.FUT_MCU_ONLY,
        EnumFut.FUT_EXTMOD_HARDWARE,
    ],
    mcu_usb_id=util_mcu_mimxrt.TEENSY40_USB_ID,
    tags="mcu=mimxrt,programmer=teensy_loader_cli",
    programmer_args=[
        "--mcu=imxrt1062",
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


########### Testbed Showcase


DOC_TENTACLE_PYBV11 = """
See: https://github.com/octoprobe/testbed_showcase/tree/main/docs/tentacle_MCU_PYBV11
"""
MCU_PYBV11 = TentacleSpecMicropython(
    tentacle_type=EnumTentacleType.TENTACLE_MCU,
    tentacle_tag="MCU_PYBV11",
    futs=[],
    doc=DOC_TENTACLE_PYBV11,
    mcu_usb_id=util_mcu_pyboard.PYBOARD_USB_ID,
    tags="boards=PYBV11:PYBV11-DP:PYBV11-THREAD:PYBV11-DP_THREAD,mcu=stm32,programmer=dfu-util",
    relays_closed={},
    mcu_config=McuConfig(),
)


DOC_TENTACLE_RPI_PICO = """
See: https://github.com/octoprobe/testbed_showcase/tree/main/docs/tentacle_MCU_RPI_PICO
"""
MCU_RPI_PICO = TentacleSpecMicropython(
    tentacle_type=EnumTentacleType.TENTACLE_MCU,
    tentacle_tag="MCU_RPI_PICO",
    futs=[],
    doc=DOC_TENTACLE_RPI_PICO,
    mcu_usb_id=util_mcu_pico.RPI_PICO_USB_ID,
    tags="boards=RPI_PICO,mcu=rp2,programmer=picotool",
    relays_closed={},
    mcu_config=McuConfig(),
)


# DOC_TENTACLE_RPI_PICO2 = """
# See: https://github.com/octoprobe/testbed_showcase/tree/main/docs/tentacle_MCU_RPI_PICO
# """
# MCU_RPI_PICO2 = TentacleSpecMicropython(
#     tentacle_type=EnumTentacleType.TENTACLE_MCU,
#     tentacle_tag="MCU_RPI_PICO2",
#     futs=[],
#     doc=DOC_TENTACLE_RPI_PICO2,
#     mcu_usb_id=util_mcu_pico.RPI_PICO2_USB_ID,
#     tags="boards=RPI_PICO2:RPI_PICO2-RISCV,mcu=rp2,programmer=picotool",
#     relays_closed={},
#     mcu_config=McuConfig(),
# )


# DOC_TENTACLE_DEVICE_POTPOURRY = """
# FT232RL
#   https://www.aliexpress.com/item/1005006445462581.html
# I2C EEPROM AT24C08
#   https://www.aliexpress.com/item/1005005344566156.html
# 1Wire Temperature Sensor DS18B20 TO-92
#   https://www.aliexpress.com/item/1005004987470850.html
# """
# DEVICE_POTPOURRY = TentacleSpecMicropython(
#     tentacle_type=EnumTentacleType.TENTACLE_DEVICE_POTPOURRY,
#     tentacle_tag="DEVICE_POTPOURRY",
#     futs=[],
#     doc=DOC_TENTACLE_DEVICE_POTPOURRY,
#     tags="",
#     relays_closed={},
# )  # type: ignore[var-annotated]

# DOC_TENTACLE_DAQ_SALEAE = """
# USB Logic Analyzer 24MHz 8 Channel
# https://www.aliexpress.com/item/4000146595503.html
# https://sigrok.org/wiki/Noname_Saleae_Logic_clone
# """
# DAQ_SALEAE = TentacleSpecMicropython(
#     tentacle_type=EnumTentacleType.TENTACLE_DAQ_SALEAE,
#     tentacle_tag="DAQ_SALEAE",
#     futs=[],
#     doc=DOC_TENTACLE_DAQ_SALEAE,
#     tags="daq=saleae_clone",
#     relays_closed={},
# )  # type: ignore[var-annotated]
