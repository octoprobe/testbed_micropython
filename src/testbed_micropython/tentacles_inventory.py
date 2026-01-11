from octoprobe.usb_tentacle.usb_constants import HwVersion
from octoprobe.util_baseclasses import TentaclesCollector

from . import tentacle_specs
from .constants import TESTBED_NAME

TENTACLES_INVENTORY = (
    TentaclesCollector(testbed_name=TESTBED_NAME)
    .add_testbed_instance(
        testbed_instance="ch_hans_1",
        tentacles=[
            # testbed showcase
            (
                # PICO_INFRA broken. Replaced by e46340474b4b-5a31
                "e46340474b4c-2731",
                HwVersion.V03,
                "v1.1",
                tentacle_specs.RPI_PICO2,
            ),
            (
                # PICO_INFRA broken. Replaced e46340474b4c-2731
                "e46340474b4b-5a31",
                HwVersion.V03,
                "v1.1",
                tentacle_specs.RPI_PICO2,
            ),
            ("e46340474b4e-1831", HwVersion.V03, "v1.1", tentacle_specs.RPI_PICO2),
            (
                "de646cc20b92-5425",
                HwVersion.V03,
                "v1.1",
                tentacle_specs.RPI_PICO_W,
            ),  # v0.4
            # ("e46340474b17-4429",HwVersion.V03, "v1.0", tentacle_specs.PYBV11), This is for testbed_showcase
            ("e46414481338-3a21", HwVersion.V03, "v1.0", tentacle_specs.PYBV11),
            # testbed micropython
            ("e46340474b59-2d2d", HwVersion.V03, "v0.1", tentacle_specs.LOLIN_D1_MINI),
            ("e4641448132c-5f2c", HwVersion.V03, "v1.0", tentacle_specs.RPI_PICO_W),
            ("e46414481355-552b", HwVersion.V03, "v1.0", tentacle_specs.RPI_PICO2_W),
            ("e46414481342-1830", HwVersion.V03, "v1.1", tentacle_specs.LOLIN_C3_MINI),
            ("e4641448133e-5d21", HwVersion.V03, "v1.1", tentacle_specs.ESP32_DEVKIT),
            (
                "e46414481346-0c30",
                HwVersion.V03,
                "v1.1",
                tentacle_specs.ESP32_C3_DEVKIT,
            ),
            (
                "e46414481354-472b",
                HwVersion.V03,
                "v1.1",
                tentacle_specs.ESP32_S3_DEVKIT,
            ),
            (
                "e46414481311-3c2a",
                HwVersion.V03,
                "v0.0",
                tentacle_specs.ARDUINO_NANO_33,
            ),
            (
                "e4641448132a-5f2a",
                HwVersion.V03,
                "v1.0",
                tentacle_specs.ADA_ITSYBITSY_M0,
            ),
            ("e46414481354-1133", HwVersion.V03, "v1.0", tentacle_specs.TEENSY40),
            (
                # PICO_INFRA broken, replaced by de6528b3cb15-4434
                "e4641448130f-2f2c",
                HwVersion.V03,
                "v1.1",
                tentacle_specs.NUCLEO_WB55,
            ),
            (
                # replaces e4641448130f-2f2c
                "de6528b3cb15-4434",
                HwVersion.V06,
                "v1.1",
                tentacle_specs.NUCLEO_WB55,
            ),
            (
                # Replaced R1503 0R with 1K
                "de6528b3cb48-3038",
                HwVersion.V06,
                "v0.1",
                tentacle_specs.NRF52840_USB_DONGLE,
            ),
        ],
    )
    .add_testbed_instance(
        testbed_instance="au_damien_1",
        tentacles=[
            ("e46340474b60-452b", HwVersion.V03, "v0.1", tentacle_specs.LOLIN_D1_MINI),
            ("e46340474b19-2629", HwVersion.V03, "v1.1", tentacle_specs.LOLIN_C3_MINI),
            ("e46340474b58-3521", HwVersion.V03, "v1.1", tentacle_specs.LOLIN_C3_MINI),
            ("e46414481349-1521", HwVersion.V03, "v1.0", tentacle_specs.RPI_PICO),
            ("e4641448133e-3a21", HwVersion.V03, "v1.0", tentacle_specs.RPI_PICO_W),
            ("e46340474b14-1c29", HwVersion.V03, "v1.0", tentacle_specs.RPI_PICO2),
            ("e46414481318-3d2c", HwVersion.V03, "v1.0", tentacle_specs.RPI_PICO2_W),
            ("e46414481310-2d2a", HwVersion.V03, "v1.1", tentacle_specs.ESP32_DEVKIT),
            (
                "e46414481355-442b",
                HwVersion.V03,
                "v1.1",
                tentacle_specs.ESP32_C3_DEVKIT,
            ),
            (
                "e46414481348-1930",
                HwVersion.V03,
                "v1.2",
                tentacle_specs.ESP32_S3_DEVKIT,
            ),
            (
                "e46414481337-1c2a",
                HwVersion.V03,
                "v0.0",
                tentacle_specs.ARDUINO_NANO_33,
            ),
            (
                "e46414481312-292a",
                HwVersion.V03,
                "v1.0",
                tentacle_specs.ADA_ITSYBITSY_M0,
            ),
            ("e46414481336-3e2a", HwVersion.V03, "v1.0", tentacle_specs.TEENSY40),
            ("e4641448130f-272c", HwVersion.V03, "v1.1", tentacle_specs.NUCLEO_WB55),
            ("e4641448132c-612a", HwVersion.V03, "v0.0", tentacle_specs.AA_UNASSEMBLED),
            ("e46414481317-5325", HwVersion.V03, "v0.0", tentacle_specs.AA_UNASSEMBLED),
            ("e46414481339-4321", HwVersion.V03, "v0.0", tentacle_specs.AA_UNASSEMBLED),
        ],
    )
    # .set_testbed_name(testbed_name="testbed_showcase")
    # .add_testbed_instance(
    #     testbed_instance="au_damien_1",
    #     tentacles=[
    #         ("e46340474b14-1c29",HwVersion.V03, "v1.1", tentacle_specs.MCU_RPI_PICO2),
    #         ("e46340474b12-1931",HwVersion.V03, "v1.0", tentacle_specs.DAQ_SALEAE),
    #         ("e46340474b56-3b21",HwVersion.V03, "v1.0", tentacle_specs.DEVICE_POTPOURRY),
    #         ("1521",HwVersion.V03, "v0.0", tentacle_specs.AA_UNASSEMBLED),
    #         ("4222",HwVersion.V03, "v0.0", tentacle_specs.AA_UNASSEMBLED),
    #         ("492f", HwVersion.V03,"v0.0", tentacle_specs.AA_UNASSEMBLED),
    #     ],
    # )
    .add_testbed_instance(
        testbed_instance="it_alessandro_1",
        tentacles=[
            ("e46414481340-1d36", HwVersion.V03, "v1.0", tentacle_specs.RPI_PICO2_W),
            (
                "e4641448132c-352c",
                HwVersion.V03,
                "v1.1",
                tentacle_specs.ESP32_C3_DEVKIT,
            ),
            ("e46414481310-422a", HwVersion.V03, "v1.0", tentacle_specs.AA_UNASSEMBLED),
            ("e46414481310-462c", HwVersion.V03, "v1.0", tentacle_specs.AA_UNASSEMBLED),
        ],
    )
    .add_testbed_instance(
        testbed_instance="nl_jan_1",
        tentacles=[
            ("de6528b3cb15-6c34", HwVersion.V06, "v1.0", tentacle_specs.RPI_PICO_W),
        ],
    )
    .add_testbed_instance(
        testbed_instance="ch_greenliff_1",
        tentacles=[
            ("e46340474b55-1722", HwVersion.V03, "v1.0", tentacle_specs.RPI_PICO),
        ],
    )
    .add_testbed_instance(
        testbed_instance="testbed_showcase",
        tentacles=[
            ("e46340474b17-4429", HwVersion.V03, "v1.0", tentacle_specs.AA_UNASSEMBLED),
            ("e46340474b4c-1331", HwVersion.V03, "v1.0", tentacle_specs.AA_UNASSEMBLED),
            ("e46340474b4c-3f31", HwVersion.V03, "v1.0", tentacle_specs.AA_UNASSEMBLED),
        ],
    )
).inventory
