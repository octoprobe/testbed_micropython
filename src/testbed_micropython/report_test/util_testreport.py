from __future__ import annotations

import dataclasses
import json
import os
import pathlib
import platform
import sys
import time
import typing

from octoprobe.util_constants import DirectoryTag, TAG_MCU
from octoprobe.util_pytest.util_resultdir import ResultsDir

from testbed_micropython.testcollection.testrun_specs import TestRun

from .util_baseclasses import (
    Outcome,
    ResultContext,
    ResultTestGroup,
    ResultTestOutcome,
)
from .util_constants import (
    FILENAME_CONTEXT_JSON,
    FILENAME_CONTEXT_TESTGROUP_JSON,
    TIME_FORMAT,
)
from .util_testreport_summary import DataSummaryLine

if typing.TYPE_CHECKING:
    from .util_testreport_by_test import SummaryByTest


@dataclasses.dataclass(slots=True)
class Data:
    """
    All result data collected:
    * Top 'context.json'
    * All sub 'context_testgroup.json'
    """

    result_context: ResultContext
    """
    The Metadata for the testresults:
    * git refs
    * 'mptest' command line parameters
    """

    testgroups: list[ResultTestGroup] = dataclasses.field(default_factory=list)

    @property
    def testgroups_ordered(self) -> list[ResultTestGroup]:
        return sorted(self.testgroups, key=lambda testgroup: testgroup.testid)

    @property
    def summary(self) -> list[DataSummaryLine]:
        return DataSummaryLine.factory_summary_lines(
            self.result_context, self.testgroups
        )

    @property
    def summary_by_test(self) -> SummaryByTest:
        from .util_testreport_by_test import SummaryByTest

        return SummaryByTest.factory(self.testgroups)

    @staticmethod
    def gather_json_files(directory_results: pathlib.Path) -> Data:
        """
        Loop over all testresults and collect and read json files.
        Return the collected data.
        """

        def collect_top() -> Data:
            filename = directory_results / FILENAME_CONTEXT_JSON
            json_text = filename.read_text()
            json_dict = json.loads(json_text)
            result_context = ResultContext.from_dict(json_dict=json_dict)
            return Data(result_context=result_context)

        data = collect_top()

        def collect() -> None:
            for filename in directory_results.glob(
                f"*/{FILENAME_CONTEXT_TESTGROUP_JSON}"
            ):
                json_text = filename.read_text()
                json_dict = json.loads(json_text)
                testgroup = ResultTestGroup(**json_dict)

                testgroup.outcomes = [
                    ResultTestOutcome(**r)  # type: ignore[arg-type, call-arg]
                    for r in testgroup.outcomes
                ]
                data.testgroups.append(testgroup)

        collect()
        assert isinstance(data, Data)
        return data


def now_formatted() -> str:
    now = time.localtime()
    return time.strftime(TIME_FORMAT, now)


def parse_formatted(time_str: str) -> time.struct_time:
    return time.strptime(time_str, TIME_FORMAT)


class ReportTests:
    def __init__(
        self,
        testresults_directory: pathlib.Path,
        log_output: pathlib.Path,
        ref_firmware: str,
        ref_tests: str,
    ) -> None:
        self.testresults_directory = testresults_directory
        self.result_context = ResultContext()
        self.result_context.time_start = now_formatted()
        self.result_context.commandline = " ".join(sys.argv)
        self.result_context.ref_firmware = ref_firmware
        self.result_context.ref_tests = ref_tests
        self.result_context.log_output = DirectoryTag.R.render_relative_to(
            top=testresults_directory, filename=log_output
        )
        self.result_context.log_directory = (
            DirectoryTag.R.render_relative_to(
                top=testresults_directory, filename=log_output.parent
            )
            + "/"
        )  # Hack: "/" is required for later path replacement!

        def get_trigger() -> str:
            if os.environ.get("CI", False):
                # See: https://docs.github.com/en/actions/writing-workflows/choosing-what-your-workflow-does/store-information-in-variables#default-environment-variables
                return "github ci pipeline"
            return f"manually started from {platform.node()}"

        self.result_context.trigger = get_trigger()
        self._write()

    def set_testbed(self, testbed_name: str, testbed_instance: str) -> None:
        self.result_context.testbed_name = testbed_name
        self.result_context.testbed_instance = testbed_instance

    def write_ok(self) -> None:
        self.result_context.error = ""
        self._write()

    def write_context_json(self) -> None:
        filename = self.testresults_directory / FILENAME_CONTEXT_JSON
        json_text = json.dumps(dataclasses.asdict(self.result_context), indent=4)
        filename.write_text(json_text)

    def _write(self) -> None:
        self.result_context.time_end = now_formatted()
        self.write_context_json()

        from ..report_test.renderer import ReportRenderer

        renderer = ReportRenderer(
            directory_results=self.testresults_directory,
            label=self.testresults_directory.name,
        )
        renderer.render()


class ReportTestgroup:
    def __init__(
        self,
        testresults_directory: ResultsDir,
        testrun: TestRun,
        logfile: pathlib.Path,
    ) -> None:
        self._report_written = False
        self.testresults_directory = testresults_directory
        self.report = ResultTestGroup()
        self.report.time_start = now_formatted()
        self.report.testgroup = testrun.testrun_spec.label
        self.report.directory_relative = (
            self.testresults_directory.directory_test_relative
        )
        self.report.testid = testrun.testid
        self.report.tentacle_variant = testrun.tentacle_variant_text
        self.report.tentacle_variant_role = testrun.tentacle_variant_role_text
        self.report.commandline = " ".join(testrun.testrun_spec.command)
        self.report.log_output = DirectoryTag.R.render_relative_to(
            top=self.testresults_directory.directory_top,
            filename=logfile,
        )
        self.report.tentacle_mcu = (
            testrun.tentacle_variant.tentacle.tentacle_spec.get_tag_mandatory(TAG_MCU)
        )
        if testrun.tentacle_reference is not None:
            self.report.tentacle_reference = testrun.tentacle_reference.label_short

        # Write the file for the case that it will never finish (timeout/crash).
        self._write()

    def write_ok(self) -> None:
        self._report_written = True
        self.report.msg_error = ""
        self._append_testresults_from_json()
        self._write()

    def write_error(self, msg: str, skipped: bool = False) -> None:
        """
        if skipped is True:
           * The test terminated as it was skipped
        if skipped is False:
           * The test terminated due to an error
        """
        if self._report_written:
            # This file has already been written
            return

        # TODO: Remove this 'if' as soon as 'run-tests.py' returns better error codes.
        # See: https://github.com/octoprobe/testbed_micropython/issues/8
        if self._append_testresults_from_json():
            # The file could be read: We leave the error empty
            self.report.msg_error = ""
            self._write()
            return

        if skipped:
            self.report.msg_error = ""
            self.report.msg_skipped = msg
        else:
            self.report.msg_error = msg
        self._write()

    def _write(self) -> None:
        self.report.time_end = now_formatted()
        filename = (
            self.testresults_directory.directory_test / FILENAME_CONTEXT_TESTGROUP_JSON
        )
        json_text = json.dumps(dataclasses.asdict(self.report), indent=4)
        filename.write_text(json_text)

    def _append_testresults_from_json(self) -> bool:
        filename = self.testresults_directory.directory_test / "_results.json"
        if not filename.exists():
            return False

        json_text = filename.read_text()
        json_dict = json.loads(json_text)

        self.report.outcomes = []
        list_results = json_dict.get("results", None)
        if list_results is None:
            # structure of _results.json before https://github.com/micropython/micropython/pull/17373
            for outcome in Outcome:
                for test_name in json_dict.get(f"{outcome}_tests", []):
                    self.report.outcomes.append(
                        ResultTestOutcome(name=test_name, outcome=outcome)
                    )
            return True

        fix_outcomes = {"pass": "passed", "skip": "skipped", "fail": "failed"}
        for test_name, _outcome, reason in list_results:
            _outcome = fix_outcomes[_outcome]
            outcome = Outcome(_outcome)
            self.report.outcomes.append(
                ResultTestOutcome(name=test_name, outcome=outcome, text=reason)
            )

        return True
