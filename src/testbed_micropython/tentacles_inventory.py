from octoprobe.util_baseclasses import TentaclesCollector

from . import tentacle_specs
from .constants import TESTBED_NAME

TENTACLES_INVENTORY = (
    TentaclesCollector(testbed_name=TESTBED_NAME)
    .add_testbed_instance(
        testbed_instance="ch_hans_1",
        tentacles=[
            # testbed showcase
            ("e46340474b4c2731", "v1.1", tentacle_specs.RPI_PICO2),
            ("e46340474b4e1831", "v1.1", tentacle_specs.RPI_PICO2),
            ("e46340474b174429", "v1.0", tentacle_specs.PYBV11),
            # testbed micropython
            ("e46340474b592d2d", "v0.1", tentacle_specs.LOLIN_D1_MINI),
            ("e4641448132c5f2c", "v1.0", tentacle_specs.RPI_PICO_W),
            ("e46414481355552b", "v1.0", tentacle_specs.RPI_PICO2_W),
            ("e464144813421830", "v1.0", tentacle_specs.LOLIN_C3_MINI),
            ("e464144813460c30", "v0.0", tentacle_specs.ESP32_C3_DEVKIT),
            ("e46414481354472b", "v1.0", tentacle_specs.ESP32_S3_DEVKIT),
            ("e464144813113c2a", "v0.0", tentacle_specs.ARDUINO_NANO_33),
            ("e4641448132a5f2a", "v1.0", tentacle_specs.ADA_ITSYBITSY_M0),
            ("e464144813541133", "v1.0", tentacle_specs.TEENSY40),
            ("e4641448130f2f2c", "v1.0", tentacle_specs.NUCLEO_WB55),
        ],
    )
    .add_testbed_instance(
        testbed_instance="au_damien_1",
        tentacles=[
            ("e46340474b60452b", "v0.1", tentacle_specs.LOLIN_D1_MINI),
            ("e46340474b192629", "v0.1", tentacle_specs.LOLIN_C3_MINI),
            ("e46340474b583521", "v0.1", tentacle_specs.LOLIN_C3_MINI),
            ("e4641448133e3a21", "v1.0", tentacle_specs.RPI_PICO_W),
            ("e464144813183d2c", "v1.0", tentacle_specs.RPI_PICO2_W),
            ("e46414481355442b", "v0.0", tentacle_specs.ESP32_C3_DEVKIT),
            ("e464144813481930", "v1.0", tentacle_specs.ESP32_S3_DEVKIT),
            ("e464144813371c2a", "v0.0", tentacle_specs.ARDUINO_NANO_33),
            ("e46414481312292a", "v1.0", tentacle_specs.ADA_ITSYBITSY_M0),
            ("e464144813363e2a", "v1.0", tentacle_specs.TEENSY40),
            ("e4641448130f272c", "v1.0", tentacle_specs.NUCLEO_WB55),
            ("e464144813491521", "v0.0", tentacle_specs.AA_UNASSEMBLED),
            ("e4641448132c612a", "v0.0", tentacle_specs.AA_UNASSEMBLED),
            ("e464144813175325", "v0.0", tentacle_specs.AA_UNASSEMBLED),
            ("e464144813394321", "v0.0", tentacle_specs.AA_UNASSEMBLED),
        ],
    )
    # .set_testbed_name(testbed_name="testbed_showcase")
    # .add_testbed_instance(
    #     testbed_instance="au_damien_1",
    #     tentacles=[
    #         ("e46340474b141c29", "v1.1", tentacle_specs.MCU_RPI_PICO2),
    #         ("e46340474b121931", "v1.0", tentacle_specs.DAQ_SALEAE),
    #         ("e46340474b563b21", "v1.0", tentacle_specs.DEVICE_POTPOURRY),
    #         ("1521", "v0.0", tentacle_specs.AA_UNASSEMBLED),
    #         ("4222", "v0.0", tentacle_specs.AA_UNASSEMBLED),
    #         ("492f", "v0.0", tentacle_specs.AA_UNASSEMBLED),
    #     ],
    # )
    # .add_testbed_instance(
    #     testbed_instance="ch_greenliff_1",
    #     tentacles=[
    #         # ("e46340474b551722", "v1.0", tentacle_specs.RPI_PICO),
    #     ],
    # )
).inventory
