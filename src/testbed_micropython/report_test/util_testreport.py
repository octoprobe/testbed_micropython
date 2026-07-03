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

from . import util_xfail
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
    patch_time_format,
)
from .util_testreport_summary import DataSummaryLine
from .util_xfail import XFailList

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

    xfail_files: util_xfail.XFailFiles
    """
    The xfail lists under src/testbed_micropython/report_test/*.json
    """

    xfail_file: util_xfail.XFailFile | None
    """
    The xfail file which was applied to mark FAILED as XFAILED
    """

    testgroups: list[ResultTestGroup] = dataclasses.field(default_factory=list)

    def __post_init__(self) -> None:
        assert isinstance(self.result_context, ResultContext)
        assert isinstance(self.xfail_files, util_xfail.XFailFiles)
        assert isinstance(self.testgroups, list)

    def get_xfail_list(self) -> XFailList:
        r = XFailList()
        for g in self.testgroups:
            for outcome in g.outcomes:
                if outcome.outcome in (Outcome.FAILED, Outcome.XFAILED):
                    tg = r.get_group(testgroup=g.testgroup)
                    tg.add(
                        board_variant=g.board_variant,
                        test_name=outcome.name,
                    )
        return r

    @property
    def ports(self) -> list[str]:
        return sorted({g.tentacle_mcu for g in self.testgroups})

    @property
    def ports_md(self) -> str:
        return " ".join([f"`{p}`" for p in self.ports])

    @property
    def testgroups_success(self) -> list[ResultTestGroup]:
        return [g for g in self.testgroups if not g.is_error]

    @property
    def testgroups_error(self) -> list[ResultTestGroup]:
        return [g for g in self.testgroups if g.is_error]

    @property
    def testgroups_success_ordered(self) -> list[ResultTestGroup]:
        return sorted(self.testgroups_success, key=lambda testgroup: testgroup.testid)

    @property
    def testgroups_error_ordered(self) -> list[ResultTestGroup]:
        return sorted(self.testgroups_error, key=lambda testgroup: testgroup.testid)

    @property
    def summary(self) -> list[DataSummaryLine]:
        return DataSummaryLine.factory_summary_lines(
            self.result_context,
            self.testgroups,
        )

    @property
    def summary_by_test(self) -> SummaryByTest:
        from .util_testreport_by_test import SummaryByTest

        return SummaryByTest.factory(self.testgroups_success)

    @property
    def tests_total(self) -> int:
        return sum(len(tg.outcomes) - 1 for tg in self.testgroups)

    @property
    def duration_per_test_text(self) -> str:
        tests_total = self.tests_total
        if tests_total == 0:
            return "-"
        return (
            f"{1000.0 * self.result_context.time_duration_s / tests_total:0.0f}ms/test"
        )

    @staticmethod
    def gather_json_files(
        directory_results: pathlib.Path,
        xfail_file: str | None,
    ) -> Data:
        """
        Loop over all testresults and collect and read json files.
        Return the collected data.
        """

        def collect_top() -> Data:
            result_context = ResultContext.factory(
                directory_results / FILENAME_CONTEXT_JSON
            )
            return Data(
                result_context=result_context,
                xfail_file=util_xfail.XFailFile.factory_template(filename=xfail_file),
                xfail_files=util_xfail.XFailFiles.factory_from_filesystem(),
            )

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

        def patch_xfailed() -> None:
            """
            Replace FAILED with XFAILED
            """
            if data.xfail_file is None:
                return

            for testgroup in data.testgroups:
                for outcome in testgroup.outcomes:
                    if outcome.outcome == Outcome.FAILED.value:
                        if data.xfail_file.xfail_list.match(
                            testgroup=testgroup.testgroup,
                            test_name=outcome.name,
                            board_variant=testgroup.board_variant,
                        ):
                            outcome.outcome = Outcome.XFAILED.value

        patch_xfailed()

        assert isinstance(data, Data)
        return data


def now_formatted() -> str:
    now = time.localtime()
    return time.strftime(TIME_FORMAT, now)


def parse_formatted(time_str: str) -> time.struct_time:
    time_str = patch_time_format(time_str)
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

    def write_error(self, error: str) -> None:
        self.result_context.error = error
        self._write()

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
            xfail_file=None,
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
            # This is the tentacle which is used as a reference.
            # For example '6038-RPI_PICO_W' in 'RUN-MULTITESTS_MULTIBLUETOOTH' or 'RUN-MULTITESTS_MULTINET'.
            # This pico is used the test bluetooth against.
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
            self.report.msg_skipped = ""
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

        fix_outcomes = {
            "pass": "passed",
            "skip": "skipped",
            "fail": "failed",
            "ignored": "skipped",  # Example: run-tests.py: results[i] = (r[0], "ignored", "{}: {}".format(FLAKY_REASON_PREFIX, reason))
        }
        for test_name, _outcome, reason in list_results:
            _outcome = fix_outcomes[_outcome]
            outcome = Outcome(_outcome)
            self.report.outcomes.append(
                ResultTestOutcome(name=test_name, outcome=outcome, text=reason)
            )

        return True
