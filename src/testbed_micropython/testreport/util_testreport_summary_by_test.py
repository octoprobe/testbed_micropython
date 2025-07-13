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
from octoprobe.util_constants import DELIMITER_SERIAL_BOARD

from testbed_micropython.testcollection.testrun_specs import (
    DELIMITER_TENTACLES,
)

from .util_baseclasses import Outcome, ResultContext
from .util_markdown2 import md_escape
from .util_testreport import (
    ResultTestGroup,
    ResultTestOutcome,
)

logger = logging.getLogger(__file__)


@dataclasses.dataclass(repr=True, slots=True)
class TestOutcome:
    testid_tentacles: str
    test_outcome: ResultTestOutcome
    testgroup: ResultTestGroup

    @property
    def logfile_markdown(self) -> str:
        return f"{self.test_outcome.outcome}({self.testgroup.log_output})"


@dataclasses.dataclass(repr=True, slots=True)
class OutcomesForOneTest(list[TestOutcome]):
    testgroup: ResultTestGroup
    test_name: str
    """
    Example: basics/0prelim.py
    """

    def test_name_link_markup(
        self,
        result_context: ResultContext,
    ) -> Markup:
        test_filename_link = self.testgroup.test_filename_link(
            result_context=result_context,
            python_test=self.test_name,
        )
        return Markup(test_filename_link)

    def outcome_link(
        self,
        testid_tentacles: str,
        fix_links: typing.Callable[[str], str],
    ) -> str:
        outcomes = [
            outcome for outcome in self if outcome.testid_tentacles == testid_tentacles
        ]
        if len(outcomes) == 0:
            return ""
        outcomes.sort(key=lambda outcome: outcome.testgroup.testid)

        def get_decoration(outcomes: list[TestOutcome]) -> tuple[str, str]:
            has_failed = False
            has_passed = False
            for outcome in outcomes:
                if outcome.test_outcome.outcome == Outcome.FAILED.value:
                    has_failed = True
                if outcome.test_outcome.outcome == Outcome.PASSED.value:
                    has_passed = True

            if not has_failed:
                # All success: subscript italic
                return ("<sub>*", "*</sub>")

            if has_passed and has_failed:
                # Flaky: italic
                return ("*", "*")

            # all failed: bold
            return ("**", "**")

        decoration_begin, decoration_end = get_decoration(outcomes)

        def render_outcome(outcome: TestOutcome) -> str:
            outcome_short = Outcome(outcome.test_outcome.outcome).short
            return f"{decoration_begin}[{md_escape(outcome_short)}]({md_escape(fix_links(outcome.testgroup.log_output))}){decoration_end}"

        return " ".join([render_outcome(outcome) for outcome in outcomes])

    @property
    def interesting(self) -> bool:
        """
        A boring tentacle_combination is, when there is at least on failed outcome.
        """
        for outcome in self:
            if outcome.test_outcome.outcome == Outcome.FAILED:
                return True
        return False


@dataclasses.dataclass(slots=True)
class Group(list[OutcomesForOneTest]):
    testgroup: ResultTestGroup
    """
    Example: RUN-TESTS_STANDARD_NATIVE
    The group is related to many 'ResultTestGroup's.
    'testgroup' just references just one.
    """
    testids_tentacles: set[str] = dataclasses.field(default_factory=set)

    @property
    def testids_tentacles_sorted(self) -> list[str]:
        return sorted(self.testids_tentacles)

    def find_or_new(
        self,
        testgroup: ResultTestGroup,
        test_name: str,
    ) -> OutcomesForOneTest:
        for outcomes_for_one_test in self:
            if outcomes_for_one_test.test_name == test_name:
                return outcomes_for_one_test

        outcomes_for_one_test = OutcomesForOneTest(
            testgroup=testgroup,
            test_name=test_name,
        )
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

        def format_tentacle_combination(testid_tentacles: str) -> str:
            testid_tentacles = md_escape(testid_tentacles)
            return testid_tentacles.replace(
                DELIMITER_TENTACLES,
                DELIMITER_TENTACLES + "<br>",
            ).replace(DELIMITER_SERIAL_BOARD, DELIMITER_SERIAL_BOARD + "<br>", 1)

        elems_header = [
            format_tentacle_combination(testid_tentacles)
            for testid_tentacles in self.testids_tentacles_sorted
        ]
        return Markup(f"| Test | {' | '.join(elems_header)} |")

    @property
    def table_delimiter_markup(self) -> Markup:
        """
        | Test | RPI_PICO_W | ESP32_DEVKIT |
        | :-: | - | - |
        """
        elems_header = [":-:" for x in self.testids_tentacles_sorted]
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
                outcomes_for_one_test = group.find_or_new(
                    testgroup=testgroup,
                    test_name=test_outcome.name,
                )
                group.testids_tentacles.add(testgroup.testid_tentacles)
                outcomes_for_one_test.append(
                    TestOutcome(
                        testid_tentacles=testgroup.testid_tentacles,
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

        groups.sort(key=lambda g: g.group_name)
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
