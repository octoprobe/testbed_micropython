from octoprobe.util_baseclasses import TentaclesCollector

from testbed.constants import TESTBED_NAME

from . import tentacles_spec

TENTACLES_INVENTORY = (
    TentaclesCollector(testbed_name=TESTBED_NAME)
    .add_testbed_instance(
        testbed_instance="ch_wetzikon_1",
        tentacles=[
            ("e46340474b174429", "v1.0", tentacles_spec.PYBV11),
            ("e46340474b4e1831", "v1.1", tentacles_spec.RPI_PICO2),
            ("e46340474b592d2d", "v0.1", tentacles_spec.ESP8266_GENERIC),
            ("e46340474b192629", "v0.1", tentacles_spec.LOLIN_C3_MINI),
        ],
    )
    .add_testbed_instance(
        testbed_instance="au_damien_1",
        tentacles=[
            ("e46340474b141c29", "v1.1", tentacles_spec.RPI_PICO2),
            ("e46340474b60452b", "v0.1", tentacles_spec.ESP8266_GENERIC),
            ("e46340474b583521", "v0.1", tentacles_spec.LOLIN_C3_MINI),
        ],
    )
).inventory
