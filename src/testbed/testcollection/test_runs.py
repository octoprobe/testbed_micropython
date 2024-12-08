"""
"""

from __future__ import annotations

import dataclasses

from octoprobe.lib_tentacle import Tentacle

from .baseclasses_spec import TentacleVariant
from .testrun_specs import TestRunBase


@dataclasses.dataclass
class TestRunSingle(TestRunBase):
    tentacle_variant: TentacleVariant

    @property
    def tentacles(self) -> list[Tentacle]:
        return [self.tentacle_variant.tentacle]


@dataclasses.dataclass(repr=True)
class TestRunWlanAPWlanSTA(TestRunBase):
    tentacle_variant_wlanAP: TentacleVariant
    tentacle_variant_wlanSTA: TentacleVariant

    @property
    def tentacles(self) -> list[Tentacle]:
        return [
            self.tentacle_variant_wlanAP.tentacle,
            self.tentacle_variant_wlanSTA.tentacle,
        ]
