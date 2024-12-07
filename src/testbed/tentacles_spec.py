from __future__ import annotations

import dataclasses
import enum

from octoprobe import util_mcu_esp32C3, util_mcu_esp8266, util_mcu_pyboard, util_mcu_rp2
from octoprobe.util_baseclasses import TentacleSpec

from testbed.constants import EnumFut, TentacleType


class EnumTentacleTag(enum.StrEnum):
    DAQ_SALEAE = "DAQ_SALEAE"
    DEVICE_POTPOURRY = "DEVICE_POTPOURRY"
    MCU_PYBV11 = "MCU_PYBV11"
    MCU_RPI_PICO = "MCU_RPI_PICO"
    MCU_RPI_PICO2 = "MCU_RPI_PICO2"
    MCU_LOLIN_D1_MINI = "MCU_LOLIN_D1_MINI"
    MCU_LOLIN_C3_MINI = "MCU_LOLIN_C3_MINI"


@dataclasses.dataclass
class McuConfig:
    """
    These variables will be replaced in micropython code
    """

    trig1: str
    trig2: str
    data1: str
    data2: str
    i2c: str
    onewire: str


DOC_TENTACLE_PYBV11 = """
See: https://github.com/octoprobe/testbed_showcase/tree/main/docs/tentacle_MCU_PYBV11
"""
tentacle_spec_mcu_pybv11 = TentacleSpec(
    tentacle_type=TentacleType.TENTACLE_MCU,
    tentacle_tag=EnumTentacleTag.MCU_PYBV11,
    futs=[
        EnumFut.FUT_MCU_ONLY,
        EnumFut.FUT_I2C,
        EnumFut.FUT_UART,
        EnumFut.FUT_ONEWIRE,
        EnumFut.FUT_TIMER,
    ],
    category="MicroPython Board",
    label="pyboard",
    doc=DOC_TENTACLE_PYBV11,
    mcu_usb_id=util_mcu_pyboard.PYBOARD_USB_ID,
    tags="boards=PYBV11:PYBV11-DP:PYBV11-THREAD:PYBV11-DP_THREAD,mcu=stm32,programmer=dfu-util",
    relays_closed={
        EnumFut.FUT_MCU_ONLY: [],
        EnumFut.FUT_I2C: [2, 3, 4, 5],
        EnumFut.FUT_ONEWIRE: [2, 3, 4],
    },
    mcu_config=McuConfig(
        trig1="Y2",
        trig2="Y3",
        data1="Y9",
        data2="Y10",
        i2c="i2c = I2C(scl='Y9', sda='Y10', freq=100000)",
        onewire="Y9",
    ),
)


DOC_TENTACLE_RPI_PICO = """
See: https://github.com/octoprobe/testbed_showcase/tree/main/docs/tentacle_MCU_RPI_PICO
"""
tentacle_spec_mcu_rpi_pico = TentacleSpec(
    tentacle_type=TentacleType.TENTACLE_MCU,
    tentacle_tag=EnumTentacleTag.MCU_RPI_PICO,
    futs=[
        EnumFut.FUT_MCU_ONLY,
        EnumFut.FUT_I2C,
        EnumFut.FUT_UART,
        EnumFut.FUT_ONEWIRE,
        EnumFut.FUT_TIMER,
        EnumFut.FUT_EXTMOD_HARDWARE,
    ],
    category="MicroPython Board",
    label="pico",
    doc=DOC_TENTACLE_RPI_PICO,
    mcu_usb_id=util_mcu_rp2.RPI_PICO_USB_ID,
    tags="boards=RPI_PICO,mcu=rp2,programmer=picotool",
    relays_closed={
        EnumFut.FUT_MCU_ONLY: [],
        EnumFut.FUT_I2C: [2, 3, 4, 5],
        EnumFut.FUT_ONEWIRE: [2, 3, 4],
        EnumFut.FUT_EXTMOD_HARDWARE: [2, 4],
    },
    mcu_config=McuConfig(
        trig1="GP20",
        trig2="GP21",
        data1="GP19",
        data2="GP18",
        i2c="i2c = I2C(1, scl=Pin('GP19'), sda=Pin('GP18'), freq=100_000)",
        onewire="GP14",
    ),
)


DOC_TENTACLE_RPI_PICO2 = """
See: https://github.com/octoprobe/testbed_showcase/tree/main/docs/tentacle_MCU_RPI_PICO
"""
tentacle_spec_mcu_rpi_pico2 = TentacleSpec(
    tentacle_type=TentacleType.TENTACLE_MCU,
    tentacle_tag=EnumTentacleTag.MCU_RPI_PICO2,
    futs=[
        EnumFut.FUT_MCU_ONLY,
        EnumFut.FUT_I2C,
        EnumFut.FUT_UART,
        EnumFut.FUT_ONEWIRE,
        EnumFut.FUT_TIMER,
        EnumFut.FUT_EXTMOD_HARDWARE,
    ],
    category="MicroPython Board",
    label="pico2",
    doc=DOC_TENTACLE_RPI_PICO2,
    mcu_usb_id=util_mcu_rp2.RPI_PICO2_USB_ID,
    tags="boards=RPI_PICO2:RPI_PICO2-RISCV,mcu=rp2,programmer=picotool",
    relays_closed={
        EnumFut.FUT_MCU_ONLY: [],
        EnumFut.FUT_I2C: [2, 3, 4, 5],
        EnumFut.FUT_ONEWIRE: [2, 3, 4],
        EnumFut.FUT_EXTMOD_HARDWARE: [2, 4],
    },
    mcu_config=McuConfig(
        trig1="GP20",
        trig2="GP21",
        data1="GP19",
        data2="GP18",
        i2c="i2c = I2C(1, scl=Pin('GP19'), sda=Pin('GP18'), freq=100_000)",
        onewire="GP14",
    ),
)

DOC_TENTACLE_LOLIN_D1_MINI = """
See: https://www.wemos.cc/en/latest/d1/d1_mini.html

See: https://www.wemos.cc/en/latest/tutorials/d1/get_started_with_micropython_d1.html
esptool.py --port PORT_NAME --baud 1000000 write_flash --flash_size=4MB -fm dio 0 FIRMWARE.bin
"""
tentacle_spec_mcu_lolin_d1_mini = TentacleSpec(
    tentacle_type=TentacleType.TENTACLE_MCU,
    tentacle_tag=EnumTentacleTag.MCU_LOLIN_D1_MINI,
    futs=[
        EnumFut.FUT_MCU_ONLY,
        EnumFut.FUT_EXTMOD_HARDWARE,
    ],
    category="MicroPython Board",
    label="LolinD1",
    doc=DOC_TENTACLE_LOLIN_D1_MINI,
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
    relays_closed={
        EnumFut.FUT_MCU_ONLY: [],
        EnumFut.FUT_EXTMOD_HARDWARE: [2, 4],
    },
    mcu_config=McuConfig(
        trig1="-",
        trig2="-",
        data1="-",
        data2="-",
        i2c="-",
        onewire="-",
    ),
)


DOC_TENTACLE_LOLIN_C3_MINI = """
See: https://www.wemos.cc/en/latest/c3/c3_mini.html
"""
tentacle_spec_mcu_lolin_c3_mini = TentacleSpec(
    tentacle_type=TentacleType.TENTACLE_MCU,
    tentacle_tag=EnumTentacleTag.MCU_LOLIN_C3_MINI,
    futs=[
        EnumFut.FUT_MCU_ONLY,
        EnumFut.FUT_EXTMOD_HARDWARE,
    ],
    category="MicroPython Board",
    label="LolinC3",
    doc=DOC_TENTACLE_LOLIN_C3_MINI,
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
    relays_closed={
        EnumFut.FUT_MCU_ONLY: [],
        EnumFut.FUT_EXTMOD_HARDWARE: [2, 4],
    },
    mcu_config=McuConfig(
        trig1="-",
        trig2="-",
        data1="-",
        data2="-",
        i2c="-",
        onewire="-",
    ),
)

DOC_TENTACLE_DEVICE_POTPOURRY = """
FT232RL
  https://www.aliexpress.com/item/1005006445462581.html
I2C EEPROM AT24C08
  https://www.aliexpress.com/item/1005005344566156.html
1Wire Temperature Sensor DS18B20 TO-92
  https://www.aliexpress.com/item/1005004987470850.html
"""
tentacle_spec_device_potpourry = TentacleSpec(
    tentacle_type=TentacleType.TENTACLE_DEVICE_POTPOURRY,
    tentacle_tag=EnumTentacleTag.DEVICE_POTPOURRY,
    futs=[EnumFut.FUT_I2C, EnumFut.FUT_UART, EnumFut.FUT_ONEWIRE, EnumFut.FUT_TIMER],
    category="MicroPython Board",
    label="potpourry",
    doc=DOC_TENTACLE_DEVICE_POTPOURRY,
    tags="",
    relays_closed={
        EnumFut.FUT_I2C: [1, 2],
        EnumFut.FUT_ONEWIRE: [5],
    },
)  # type: ignore[var-annotated]

DOC_TENTACLE_DAQ_SALEAE = """
USB Logic Analyzer 24MHz 8 Channel
https://www.aliexpress.com/item/4000146595503.html
https://sigrok.org/wiki/Noname_Saleae_Logic_clone
"""
tentacle_spec_daq_saleae = TentacleSpec(
    tentacle_type=TentacleType.TENTACLE_DAQ_SALEAE,
    tentacle_tag=EnumTentacleTag.DAQ_SALEAE,
    futs=[
        EnumFut.FUT_I2C,
        EnumFut.FUT_UART,
        EnumFut.FUT_ONEWIRE,
        EnumFut.FUT_TIMER,
        EnumFut.FUT_EXTMOD_HARDWARE,
    ],
    category="MicroPython Board",
    label="daq",
    doc=DOC_TENTACLE_DAQ_SALEAE,
    tags="daq=saleae_clone",
    relays_closed={
        EnumFut.FUT_I2C: [1, 2, 3, 4],
        EnumFut.FUT_ONEWIRE: [1, 2, 3, 4],
        EnumFut.FUT_EXTMOD_HARDWARE: [1, 2, 3, 4],
    },
)  # type: ignore[var-annotated]


TENTACLES_SPECS: dict[str, TentacleSpec] = {
    tentacle_spec.tentacle_tag: tentacle_spec
    for tentacle_spec in (
        tentacle_spec_daq_saleae,
        tentacle_spec_device_potpourry,
        tentacle_spec_mcu_pybv11,
        tentacle_spec_mcu_rpi_pico,
        tentacle_spec_mcu_rpi_pico2,
        tentacle_spec_mcu_lolin_d1_mini,
        tentacle_spec_mcu_lolin_c3_mini,
    )
}
