from octoprobe.util_baseclasses import TentaclesCollector

from testbed.constants import TESTBED_NAME

from . import tentacle_specs

TENTACLES_INVENTORY = (
    TentaclesCollector(testbed_name=TESTBED_NAME)
    .add_testbed_instance(
        testbed_instance="ch_hans_1",
        tentacles=[
            ("e46340474b174429", "v1.0", tentacle_specs.PYBV11),
            ("e46340474b4e1831", "v1.1", tentacle_specs.RPI_PICO2),
            ("e46340474b592d2d", "v0.1", tentacle_specs.LOLIN_D1_MINI),
            ("e46340474b192629", "v0.1", tentacle_specs.LOLIN_C3_MINI),
        ],
    )
    .add_testbed_instance(
        testbed_instance="au_damien_1",
        tentacles=[
            ("e46340474b141c29", "v1.1", tentacle_specs.RPI_PICO2),
            ("e46340474b60452b", "v0.1", tentacle_specs.LOLIN_D1_MINI),
            ("e46340474b583521", "v0.1", tentacle_specs.LOLIN_C3_MINI),
        ],
    )
    .add_testbed_instance(
        testbed_instance="ch_greenliff_1",
        tentacles=[
            ("e46340474b551722", "v1.0", tentacle_specs.RPI_PICO),
        ],
    )
).inventory
