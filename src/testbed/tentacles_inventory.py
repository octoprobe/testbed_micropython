from .tentacles_spec import EnumTentacleTag

TENTACLES_INVENTORY: dict[str, tuple[str, str]] = {
    # testbed_micropython_ch_wetzikon_1
    "e46340474b174429": ("v1.0", EnumTentacleTag.MCU_PYBV11),
    "e46340474b4e1831": ("v1.1", EnumTentacleTag.MCU_RPI_PICO2),
    "e46340474b592d2d": ("v0.1", EnumTentacleTag.MCU_LOLIN_D1_MINI),
    "e46340474b192629": ("v0.1", EnumTentacleTag.MCU_LOLIN_C3_MINI),
    # testbed_micropython_au_damien_1
    "e46340474b141c29": ("v1.1", EnumTentacleTag.MCU_RPI_PICO2),
    "e46340474b60452b": ("v0.1", EnumTentacleTag.MCU_LOLIN_D1_MINI),
    "e46340474b583521": ("v0.1", EnumTentacleTag.MCU_LOLIN_C3_MINI),
}
