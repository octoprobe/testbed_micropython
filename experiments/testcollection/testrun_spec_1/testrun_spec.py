from __future__ import annotations

import dataclasses
from abc import abstractmethod
from typing import Iterator


@dataclasses.dataclass
class TestRun:
    test_run_specs: list[RunSpecBase]


@dataclasses.dataclass
class RunSpecBase:
    pass

    @abstractmethod
    def generate(self, available_tentacles:list) -> Iterator[TestRun]:
       ...

@dataclasses.dataclass
class RunSpecSingle(RunSpecBase):
    """
    Runs tests against a single tentacle.

    Each test has to run on every connected tentacle with FUT_MCU_ONLY.
    """
    filename: str
    """
    perftest.py, hwtest.py
    """

    list_tentacles_not_yet_tested: list

    def generate(self,  available_tentacles:list) -> Iterator[TestRun]:
        yield self.filename

@dataclasses.dataclass
class RunSpecWlanAP_vs_STA(RunSpecBase):
    """
    Tentacle_WLA_STA connects to Tentacle_WLAN_AP.
    """

@dataclasses.dataclass
class RunSpecWlanSTA_vs_STA(RunSpecBase):
    """
    Two tentacles connect to an AP and communicate together.
    """


def testspec_generator() -> Iterator[RunSpecBase]:
    yield RunSpecSingle("perftest.py")
