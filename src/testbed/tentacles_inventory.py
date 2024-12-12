from . import tentacles_spec

TENTACLES_INVENTORY: dict[str, tuple[str, tentacles_spec.TentacleSpec]] = {
    # testbed_micropython_ch_wetzikon_1
    "e46340474b174429": ("v1.0", tentacles_spec.PYBV11),
    "e46340474b4e1831": ("v1.1", tentacles_spec.RPI_PICO2),
    "e46340474b592d2d": ("v0.1", tentacles_spec.ESP8266_GENERIC),
    "e46340474b192629": ("v0.1", tentacles_spec.LOLIN_C3_MINI),
    # testbed_micropython_au_damien_1
    "e46340474b141c29": ("v1.1", tentacles_spec.RPI_PICO2),
    "e46340474b60452b": ("v0.1", tentacles_spec.ESP8266_GENERIC),
    "e46340474b583521": ("v0.1", tentacles_spec.LOLIN_C3_MINI),
}
