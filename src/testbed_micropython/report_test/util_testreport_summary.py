from __future__ import annotations

import dataclasses

from testbed_micropython.report_test.util_baseclasses import (
    Outcome,
    ResultContext,
    ResultTestGroup,
)


@dataclasses.dataclass(slots=True)
class DataSummaryLine:
    label: str
    group_run: int = 0
    group_skipped: int = 0
    group_error: int = 0
    tests_skipped: int = 0
    tests_passed: int = 0
    tests_failed: int = 0

    @staticmethod
    def factory_summary_lines(
        result_context: ResultContext,
        testgroups: list[ResultTestGroup],
    ) -> list[DataSummaryLine]:
        dict_summary: dict[str, DataSummaryLine] = {}
        for testgroup in testgroups:
            line = dict_summary.get(testgroup.testgroup, None)
            if line is None:
                # Example label: [RUN-TESTS_EXTMOD_HARDWARE](https://github.com/micropython/micropython/tree/master/tests/run-tests.py)
                label = testgroup.testgroup_markdown(result_context=result_context)
                line = DataSummaryLine(label=label)
                dict_summary[testgroup.testgroup] = line
            assert isinstance(line, DataSummaryLine)

            if testgroup.msg_skipped != "":
                line.group_skipped += 1
            elif testgroup.msg_error != "":
                line.group_error += 1
            else:
                line.group_run += 1

            for result in testgroup.outcomes:
                if result.outcome == Outcome.FAILED:
                    line.tests_failed += 1
                    continue
                if result.outcome == Outcome.SKIPPED:
                    line.tests_skipped += 1
                    continue
                assert result.outcome == Outcome.PASSED
                line.tests_passed += 1

        lines = sorted(dict_summary.values(), key=lambda line: line.label)

        total_line = DataSummaryLine(label="Total")
        for line in lines:
            total_line.group_error += line.group_error
            total_line.group_skipped += line.group_skipped
            total_line.group_run += line.group_run
            total_line.tests_failed += line.tests_failed
            total_line.tests_skipped += line.tests_skipped
            total_line.tests_passed += line.tests_passed
        lines.append(total_line)
        return lines
