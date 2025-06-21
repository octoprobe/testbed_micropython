"""
        for group in self.groups:
            print(group.testgroup_name)
            for outcomes_for_one_test in group:

New:
class TentacleColumn
  name
  list_tentacles


list_columns
outcomes_for_one_test
"""

from __future__ import annotations

import dataclasses
import logging
import typing

from markupsafe import Markup

from .util_baseclasses import Outcome
from .util_markdown2 import md_escape
from .util_testreport import (
    ResultTestGroup,
    ResultTestOutcome,
)

logger = logging.getLogger(__file__)


@dataclasses.dataclass(repr=True, slots=True)
class TestOutcome:
    tentacle_combination: TentacleCombination
    test_outcome: ResultTestOutcome
    testgroup: ResultTestGroup

    @property
    def logfile_markdown(self) -> str:
        return f"{self.test_outcome.outcome}({self.testgroup.log_output})"


@dataclasses.dataclass(repr=True, slots=True)
class OutcomesForOneTest(list[TestOutcome]):
    test_name: str
    """
    Example: basics/0prelim.py
    """

    def outcome_link(
        self,
        tentacle_combination: TentacleCombination,
        fix_links: typing.Callable[[str], str],
    ) -> str:
        outcome = self._get_outcome(tentacle_combination)
        if outcome is None:
            return ""
        decoration_begin, decoration_end = {
            Outcome.FAILED.value: ("**", "**"),
            Outcome.PASSED.value: ("*", "*"),
            Outcome.SKIPPED.value: ("<sub>*", "*</sub>"),
        }.get(outcome.test_outcome.outcome, ("", ""))
        return f"{decoration_begin}[{md_escape(outcome.test_outcome.outcome)}]({md_escape(fix_links(outcome.testgroup.log_output))}){decoration_end}"

    def _get_outcome(
        self,
        tentacle_combination: TentacleCombination,
    ) -> TestOutcome | None:
        for outcome in self:
            assert isinstance(outcome, TestOutcome)
            if outcome.tentacle_combination == tentacle_combination:
                return outcome

        return None

    @property
    def interesting(self) -> bool:
        """
        A boring tentacle_combination is, when there is at least on failed outcome.
        """
        for outcome in self:
            if outcome.test_outcome.outcome == Outcome.FAILED:
                return True
        return False


TentacleCombination = list[str]


class TentacleCombinations(list[TentacleCombination]):
    """
    This represents the columns of the summary table
    """

    def add(self, tentacles: list[str]) -> TentacleCombination:
        """
        Add if not already there.
        """
        for tentacle_combination in self:
            if tentacle_combination == tentacles:
                return tentacle_combination

        tentacle_combination = tentacles
        self.append(tentacle_combination)
        return tentacle_combination

    def sortit(self) -> None:
        self.sort()


@dataclasses.dataclass(slots=True)
class Group(list[OutcomesForOneTest]):
    testgroup: ResultTestGroup
    """
    Example: RUN-TESTS_STANDARD_NATIVE
    The group is related to many 'ResultTestGroup's.
    'testgroup' just references just one.
    """
    tentacle_combinations: TentacleCombinations = dataclasses.field(
        default_factory=TentacleCombinations
    )

    def find_or_new(self, test_name: str) -> OutcomesForOneTest:
        for outcomes_for_one_test in self:
            if outcomes_for_one_test.test_name == test_name:
                return outcomes_for_one_test

        outcomes_for_one_test = OutcomesForOneTest(test_name=test_name)
        self.append(outcomes_for_one_test)
        return outcomes_for_one_test

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.group_name}, len={len(self)})"

    @property
    def group_name(self) -> str:
        return self.testgroup.testgroup

    @property
    def table_header_markup(self) -> Markup:
        """
        | Test | RPI_PICO_W | ESP32_DEVKIT |
        | :- | - | - |
        """

        def format_tentacle_combination(c: TentacleCombination) -> str:
            def f(t: str):
                "Example: 1133-TEENSY40"
                serial, _, board = t.partition("-")
                return "-<br>".join([md_escape(serial), md_escape(board)])

            return "<br>".join([f(t) for t in c])

        elems_header = [
            format_tentacle_combination(c) for c in self.tentacle_combinations
        ]
        return Markup(f"| Test | {' | '.join(elems_header)} |")

    @property
    def table_delimiter_markup(self) -> Markup:
        """
        | Test | RPI_PICO_W | ESP32_DEVKIT |
        | :-: | - | - |
        """
        elems_header = [":-:" for x in self.tentacle_combinations]
        return Markup(f"| :- | {' | '.join(elems_header)} |")


class SummaryByTest(list[Group]):
    def find_or_new(self, testgroup: ResultTestGroup) -> Group:
        for group in self:
            if group.testgroup.testgroup == testgroup.testgroup:
                return group

        group = Group(testgroup=testgroup)
        self.append(group)
        return group

    @staticmethod
    def factory(testgroups: list[ResultTestGroup]) -> SummaryByTest:
        groups = SummaryByTest()
        for testgroup in testgroups:
            group = groups.find_or_new(testgroup=testgroup)
            for test_outcome in testgroup.outcomes:
                outcomes_for_one_test = group.find_or_new(test_name=test_outcome.name)
                tentacle_combination = group.tentacle_combinations.add(
                    tentacles=testgroup.tentacles
                )
                outcomes_for_one_test.append(
                    TestOutcome(
                        tentacle_combination=tentacle_combination,
                        test_outcome=test_outcome,
                        testgroup=testgroup,
                    )
                )

        # Just keep interesting tests. Purge tests with only pass/skip.
        for group in groups:
            tobe_removed: list[OutcomesForOneTest] = []
            for outcomes_for_one_test in group:
                if not outcomes_for_one_test.interesting:
                    tobe_removed.append(outcomes_for_one_test)
            for x in tobe_removed:
                group.remove(x)

        # Just keep the groups which have outcomes.
        groups = SummaryByTest(g for g in groups if len(group) > 0)

        for group in groups:
            group.tentacle_combinations.sortit()

        groups.print()
        return groups

    def print(self) -> None:
        return
        for group in self:
            print(f"{group!r}")

        for group in self:
            print(group.testgroup_name)

            print("Header: ", end="")
            for tentacle_combination in group.tentacle_combinations:
                print(f"{tentacle_combination.tentacles},", end="")
            print("Done")

            for outcomes_for_one_test in group:
                assert isinstance(outcomes_for_one_test, OutcomesForOneTest)
                print(f"   test_name={outcomes_for_one_test.test_name}:", end="")

                for tentacle_combination in group.tentacle_combinations:
                    outcome = outcomes_for_one_test.get_outcome(tentacle_combination)
                    if outcome is None:
                        print("-,", end="")
                    else:
                        print(f"'{outcome.logfile_markdown}',", end="")
                    # outcome_text = ",".join(
                    #     outcome.test_outcome.outcome
                    #     for outcome in outcomes_for_one_test
                    # )
                    # print(f"  {outcomes_for_one_test.test_name}: {outcome_text}")
                print(" DONE")
                # break

        print("DONE")
