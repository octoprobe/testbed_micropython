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
class TestRunFirstSecond(TestRunBase):
    tentacle_variant_first: TentacleVariant
    tentacle_variant_second: TentacleVariant

    @property
    def tentacles(self) -> list[Tentacle]:
        return [
            self.tentacle_variant_first.tentacle,
            self.tentacle_variant_second.tentacle,
        ]
