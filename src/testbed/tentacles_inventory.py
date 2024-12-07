from .tentacles_spec import EnumTentacleTag

TENTACLES_INVENTORY: dict[str, tuple[str, str]] = {
    # testbed_ch_wetzikon_1
    "e46340474b174429": ("v1.0", EnumTentacleTag.MCU_PYBV11),
    "e46340474b4e1831": ("v1.1", EnumTentacleTag.MCU_RPI_PICO2),
    "e46340474b592d2d": ("v0.1", EnumTentacleTag.MCU_LOLIN_D1_MINI),
    "e46340474b192629": ("v0.1", EnumTentacleTag.MCU_LOLIN_C3_MINI),
    "e46340474b4c1331": ("v1.0", EnumTentacleTag.DAQ_SALEAE),
    "e46340474b4c3f31": ("v1.0", EnumTentacleTag.DEVICE_POTPOURRY),
    # testbed_ch_greenliff_1
    "e46340474b551722": ("v1.0", EnumTentacleTag.MCU_RPI_PICO),
    "e46340474b164d29": ("v1.0", EnumTentacleTag.DAQ_SALEAE),
    "e46340474b574722": ("v1.0", EnumTentacleTag.DEVICE_POTPOURRY),
    # testbed_au_melbourne_1 Damien
    "e46340474b141c29": ("v1.1", EnumTentacleTag.MCU_RPI_PICO2),
    "e46340474b60452b": ("v0.1", EnumTentacleTag.MCU_LOLIN_D1_MINI),
    "e46340474b583521": ("v0.1", EnumTentacleTag.MCU_LOLIN_C3_MINI),
    "e46340474b283623": ("v1.0", EnumTentacleTag.DAQ_SALEAE),
    "e46340474b0c3523": ("v1.0", EnumTentacleTag.DEVICE_POTPOURRY),
    # testbed_au_melbourne_2
    "e46340474b4c2731": ("v1.1", EnumTentacleTag.MCU_RPI_PICO2),
    "e46340474b121931": ("v1.0", EnumTentacleTag.DAQ_SALEAE),
    "e46340474b563b21": ("v1.0", EnumTentacleTag.DEVICE_POTPOURRY),
}
