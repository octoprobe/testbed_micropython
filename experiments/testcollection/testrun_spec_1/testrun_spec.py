"""
tsv: TentacleSpecVariant
tsvs: TentacleSpecVariants
tbt: ToBeTested
"""

from __future__ import annotations

import abc
import dataclasses
import enum
import itertools
from typing import Iterator


class EnumFut(enum.StrEnum):
    FUT_MCU_ONLY = enum.auto()
    """
    Do not provide a empty list, use FUT_MCU_ONLY instead!
    """
    FUT_EXTMOD_HARDWARE = enum.auto()
    """
    rx-tx loopback connection
    """
    FUT_WLAN = enum.auto()
    FUT_BLE = enum.auto()


@dataclasses.dataclass(frozen=True, unsafe_hash=True)
class TentacleSpecVariant:
    tentacle_spec: TentacleSpec
    variant: str

    def __repr__(self) -> str:
        return f"{self.tentacle_spec.board}-{self.variant}"


@dataclasses.dataclass(frozen=True, unsafe_hash=True)
class TentacleVariant:
    tentacle: Tentacle
    variant: str

    def __repr__(self) -> str:
        return f"{self.tentacle.tentacle_spec.board}-{self.variant}"


class TentacleSpec:
    def __init__(self, board: str, variants: list[str], list_futs: list[str]) -> None:
        self.board = board
        self.variants = variants
        self.list_futs = list_futs

    @property
    def tsvs(self) -> list[TentacleSpecVariant]:
        """
        ["RP_PICO2W-default", "RP_PICO2W-RISCV"]
        """
        # return [f"{self.board}-{v}" for v in self.variants]
        return [
            TentacleSpecVariant(tentacle_spec=self, variant=v) for v in self.variants
        ]

    # @property
    # def board_variants(self) -> list[BoardVariant]:
    #     """
    #     ["RP_PICO2W-default", "RP_PICO2W-RISCV"]
    #     """
    #     # return [f"{self.board}-{v}" for v in self.variants]
    #     return [BoardVariant(tentacle_spec=self, variant=v) for v in self.variants]


@dataclasses.dataclass
class Tentacle:
    tentacle_spec: TentacleSpec
    serial: str

    # def __repr__(self)->str:
    #     return f"{self.__class__.__name__}({self.serial}, {self.tentacle_spec.__repr__()})"


@dataclasses.dataclass
class TestRunBase:
    testrun_spec: TestRunSpecBase

    @property
    @abc.abstractmethod
    def tentacles(self) -> list[Tentacle]: ...

    def done(self) -> None:
        self.testrun_spec.done(test_run=self)


@dataclasses.dataclass
class TestRunSingle(TestRunBase):
    tentacle_variant: TentacleVariant

    @property
    def tentacles(self) -> list[Tentacle]:
        return [self.tentacle_variant.tentacle]


@dataclasses.dataclass
class TestRunFirstSecond(TestRunBase):
    tentacle_variant_first: TentacleVariant
    tentacle_variant_second: TentacleVariant

    @property
    def tentacles(self) -> list[Tentacle]:
        return [
            self.tentacle_variant_first.tentacle,
            self.tentacle_variant_second.tentacle,
        ]


class TestRunSpecBase(abc.ABC):
    @abc.abstractmethod
    def generate(self, available_tentacles: list) -> Iterator[TestRunBase]: ...

    @abc.abstractmethod
    def done(self, test_run: TestRunBase) -> None: ...

    @property
    @abc.abstractmethod
    def tests_tbd(self) -> int: ...


class TestRunSpecSingle(TestRunSpecBase):
    """
    Runs tests against a single tentacle.

    Each test has to run on every connected tentacle with FUT_MCU_ONLY.
    """

    def __init__(
        self,
        subprocess_args: list[str],
        tsvs_tbt: TentacleSpecVariants,
    ) -> None:
        assert isinstance(subprocess_args, list)
        assert isinstance(tsvs_tbt, TentacleSpecVariants)

        self.tsvs_tbt = TentacleSpecVariants(tsvs_tbt)
        self.subprocess_args = subprocess_args
        """
        perftest.py, hwtest.py
        """

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(tests_tbd={self.tests_tbd} {self.subprocess_args})"

    def done(self, test_run: TestRunBase) -> None:
        assert isinstance(test_run, TestRunSingle)

        self.tsvs_tbt.remove_tentacle_variant(test_run.tentacle_variant)

    @property
    def tests_tbd(self) -> int:
        return len(self.tsvs_tbt)

    def generate(self, available_tentacles: list[Tentacle]) -> Iterator[TestRunBase]:
        for tsv_to_be_tested in self.tsvs_tbt:
            for available_tentacle in available_tentacles:
                if (
                    available_tentacle.tentacle_spec
                    is not tsv_to_be_tested.tentacle_spec
                ):
                    continue
                yield TestRunSingle(
                    testrun_spec=self,
                    tentacle_variant=TentacleVariant(
                        tentacle=available_tentacle,
                        variant=tsv_to_be_tested.variant,
                    ),
                )
                break


@dataclasses.dataclass
class TestRunSpecWlan(TestRunSpecBase):
    """
    Tentacle_WLA_STA connects to Tentacle_WLAN_AP.
    Two tentacles connect to an AP and communicate together.

    Every tentacle has to be tested against two other tentacles. Once as first, and once as second.
    """

    def __init__(
        self,
        subprocess_args: list[str],
        tsvs_tbt: TentacleSpecVariants,
    ) -> None:
        assert isinstance(subprocess_args, list)
        assert isinstance(tsvs_tbt, TentacleSpecVariants)

        self.tsvs_tbt_first = TentacleSpecVariants(tsvs_tbt)
        self.tsvs_tbt_second = TentacleSpecVariants(tsvs_tbt)
        self.subprocess_args = subprocess_args
        """
        wlantest.py
        """

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(tests_tbd={self.tests_tbd} {self.subprocess_args})"

    def done(self, test_run: TestRunBase) -> None:
        assert isinstance(test_run, TestRunFirstSecond)

        self.tsvs_tbt_first.remove_tentacle_variant(test_run.tentacle_variant_first)
        self.tsvs_tbt_second.remove_tentacle_variant(test_run.tentacle_variant_second)

    @property
    def tests_tbd(self) -> int:
        return len(self.tsvs_tbt_first) + len(self.tsvs_tbt_second)

    def generate(self, available_tentacles: list[Tentacle]) -> Iterator[TestRunBase]:
        tsvs_combinations: list[tuple[TentacleSpecVariant, TentacleSpecVariant]] = []
        for first in self.tsvs_tbt_first:
            for second in self.tsvs_tbt_second:
                tsvs_combinations.append((first, second))

        if False:
            for s in tsvs_combinations:
                print(s)

        for first, second in tsvs_combinations:
            for tentacle_first, tentacle_second in itertools.combinations(
                available_tentacles, 2
            ):
                if tentacle_first.tentacle_spec is not first.tentacle_spec:
                    continue
                if tentacle_second.tentacle_spec is not second.tentacle_spec:
                    continue
                yield TestRunFirstSecond(
                    testrun_spec=self,
                    tentacle_variant_first=TentacleVariant(
                        tentacle=tentacle_first,
                        variant=first.variant,
                    ),
                    tentacle_variant_second=TentacleVariant(
                        tentacle=tentacle_second,
                        variant=first.variant,
                    ),
                )
                break


class RunSpecContainer(list[TestRunSpecBase]):
    def generate(self, available_tentacles: list[Tentacle]) -> Iterator[TestRunBase]:
        for testrun_spec in self:
            yield from testrun_spec.generate(available_tentacles=available_tentacles)

    @property
    def tests_tbd(self) -> int:
        return sum(testrun_spec.tests_tbd for testrun_spec in self)


class TentacleSpecVariants(set[TentacleSpecVariant]):
    def remove_tentacle_variant(self, tentacle_variant: TentacleVariant) -> None:
        for tsv in self:
            if tsv.tentacle_spec == tentacle_variant.tentacle.tentacle_spec:
                if tsv.variant == tentacle_variant.variant:
                    assert tsv in self
                    self.remove(tsv)
                    return


class WaitForTestsToTerminateException(Exception):
    pass


class AllTestsDoneException(Exception):
    pass


class TestBartender:
    def __init__(
        self,
        connected_tentacles: ConnectedTentacles,
        testrun_spec_container: RunSpecContainer,
    ) -> None:
        assert isinstance(connected_tentacles, ConnectedTentacles)
        assert isinstance(testrun_spec_container, RunSpecContainer)
        self.connected_tentacles = connected_tentacles
        self.testrun_spec_container = testrun_spec_container
        self.actual_runs: list[TestRunBase] = []
        self.available_tentacles = connected_tentacles.copy()

    def test_run_next(self) -> TestRunBase:
        possible_test_runs = list(
            self.testrun_spec_container.generate(
                available_tentacles=self.available_tentacles
            )
        )
        if len(possible_test_runs) == 0:
            if self.tests_tbd == 0:
                raise AllTestsDoneException
            raise WaitForTestsToTerminateException()
        # Calculate priorities
        # Return max

        selected_test_run = possible_test_runs[-1]
        # selected_test_run.decrement()available_tentacles: list[
        self._reserve(test_run=selected_test_run)
        return selected_test_run

    @property
    def tests_tbd(self) -> int:
        return self.testrun_spec_container.tests_tbd

    def _reserve(self, test_run: TestRunBase) -> None:
        self.actual_runs.append(test_run)

        for tentacle in test_run.tentacles:
            assert tentacle in self.available_tentacles
            self.available_tentacles.remove(tentacle)

    def _release(self, test_run: TestRunBase) -> None:
        assert test_run in self.actual_runs
        self.actual_runs.remove(test_run)

        test_run.done()

        for tentacle in test_run.tentacles:
            assert tentacle not in self.available_tentacles
            self.available_tentacles.append(tentacle)

    def test_run_done(self, test_run: TestRunBase) -> None:
        self._release(test_run=test_run)


class ConnectedTentacles(list[Tentacle]):
    @property
    def tentacle_specs(self) -> set[TentacleSpec]:
        specs: set[TentacleSpec] = set()
        for t in self:
            specs.add(t.tentacle_spec)
        return specs

    @property
    def tsvs(self) -> TentacleSpecVariants:
        s = TentacleSpecVariants()
        for tentacle_spec in self.tentacle_specs:
            for tsv in tentacle_spec.tsvs:
                s.add(tsv)
        return s


def main() -> None:
    spec_pico2w = TentacleSpec(
        board="RPI_PICO2W",
        variants=["default", "RISCV"],
        list_futs=[EnumFut.FUT_MCU_ONLY, EnumFut.FUT_EXTMOD_HARDWARE, EnumFut.FUT_WLAN],
    )
    spec_d1 = TentacleSpec(
        board="LolinD1",
        variants=["default", "Flash512k"],
        list_futs=[EnumFut.FUT_MCU_ONLY, EnumFut.FUT_EXTMOD_HARDWARE, EnumFut.FUT_WLAN],
    )
    spec_c3 = TentacleSpec(
        board="LolinC3",
        variants=["default"],
        list_futs=[EnumFut.FUT_MCU_ONLY, EnumFut.FUT_EXTMOD_HARDWARE, EnumFut.FUT_WLAN],
    )

    connected_tentacles = ConnectedTentacles(
        [
            Tentacle(tentacle_spec=spec_pico2w, serial="AA"),
            Tentacle(tentacle_spec=spec_pico2w, serial="AB"),
            Tentacle(tentacle_spec=spec_d1, serial="AC"),
            Tentacle(tentacle_spec=spec_c3, serial="AD"),
        ]
    )
    testrun_spec_container = RunSpecContainer(
        [
            TestRunSpecSingle(
                subprocess_args=["perftest.py"],
                tsvs_tbt=connected_tentacles.tsvs,
            ),
            TestRunSpecWlan(
                subprocess_args=["wlantest.py"],
                tsvs_tbt=connected_tentacles.tsvs,
            ),
        ]
    )
    if False:
        test_runs = list(
            testrun_spec_container.generate(available_tentacles=connected_tentacles)
        )
        for test_run in test_runs:
            print(test_run)
    else:
        test_bartender = TestBartender(
            connected_tentacles=connected_tentacles,
            testrun_spec_container=testrun_spec_container,
        )
        for i in itertools.count():
            # if i == 10:
            #     break
            print(f"START: test_dbd:{test_bartender.tests_tbd}")
            for testrun_spec in test_bartender.testrun_spec_container:
                print(f"  {testrun_spec!r}")
            try:
                test_run_next = test_bartender.test_run_next()
                print(
                    f"{i} test_dbd:{test_bartender.tests_tbd} test_run_next:{test_run_next}"
                )
                for test_run in test_bartender.actual_runs:
                    print("   ", test_run)
                if len(test_bartender.actual_runs) >= 3:
                    test_run_done = test_bartender.actual_runs[-1]
                    print("  test_run_done:", test_run_done)
                    test_bartender.test_run_done(test_run_done)
                if test_run_next is None:
                    return
            except WaitForTestsToTerminateException:
                print(i, "WaitForTestsToTerminateException")
                if len(test_bartender.actual_runs) == 0:
                    print("DONE")
                    break
                test_run_done = test_bartender.actual_runs[-1]
                test_bartender.test_run_done(test_run_done)
                print("  test_run_done:", test_run_done)

            except AllTestsDoneException:
                print("Done")
                for test_run in test_bartender.actual_runs:
                    print("   ", test_run)
                break

    # list_test_run = TestRuns([TestRun()])
    # connected_tentacles.used("MCU_LOLIN_D1_MINI")
    # test_run = get_next_test(connected_tentacles, list_test_run)


main()
