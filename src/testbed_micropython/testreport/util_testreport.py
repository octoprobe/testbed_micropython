import dataclasses
import json
import os
import pathlib
import platform
import sys
import time

from octoprobe.util_pytest.util_logging import LOGFILENAME_HACK
from octoprobe.util_pytest.util_resultdir import ResultsDir

from ..testcollection.testrun_specs import TestRun


@dataclasses.dataclass
class ResultTestResult:
    name: str
    result: str = ""
    text: str = ""


@dataclasses.dataclass
class ResultTestGroup:
    directory_relative: str = ""
    testgroup: str = ""
    testid: str = ""
    commandline: str = ""
    # RUN-TESTS_BASICS
    tentacles: list[str] = dataclasses.field(default_factory=list)
    # b0c30
    # port_variant: str = ""
    # ESP32_C3_DEVKIT
    time_start: str = ""
    # 2025-04-18 23:22:12
    time_end: str = ""
    # 2025-04-18 23:43:14
    log_output: str = ""
    # logger_20_info.log
    results: list[ResultTestResult] = dataclasses.field(default_factory=list)
    error: str = "Test never finished..."


@dataclasses.dataclass
class ResultTests:
    testbed_name: str = ""
    # testbed_micropython
    testbed_instance: str = ""
    # ch_hans_1
    time_start: str = ""
    # 2025-04-18 23:22:12
    time_end: str = ""
    # 2025-04-18 23:43:14
    ref_firmware: str = ""
    # "https://github.com/micropython/micropython.git@master",
    ref_tests: str = ""
    # "https://github.com/dpgeorge/micropython@master",
    trigger: str = ""
    # "https://github.com/micropython/micropython/pull/17091"
    commandline: str = ""
    # mptest.cli test --only-test=RUN-TESTS_EXTMOD_HARDWARE --no-multiprocessing --flash-skip
    log_output: str = ""
    # logger_20_info.log
    error: str = "Test never finished..."


def now_formatted() -> str:
    now = time.localtime()
    return time.strftime("%Y-%m-%d %H:%M:%S", now)


class ReportTests:
    def __init__(
        self,
        testresults_directory: pathlib.Path,
        log_output: pathlib.Path,
        ref_firmware: str,
        ref_tests: str,
    ) -> None:
        self.testresults_directory = testresults_directory
        self.report = ResultTests()
        self.report.time_start = now_formatted()
        self.report.commandline = " ".join(sys.argv)
        self.report.ref_firmware = ref_firmware
        self.report.ref_tests = ref_tests
        self.report.log_output = str(log_output.relative_to(testresults_directory))

        def get_trigger() -> str:
            if os.environ.get("CI", False):
                # See: https://docs.github.com/en/actions/writing-workflows/choosing-what-your-workflow-does/store-information-in-variables#default-environment-variables
                return "github ci pipeline"
            return platform.node()

        self.report.trigger = get_trigger()
        self._write()

    def set_testbed(self, testbed_name: str, testbed_instance: str) -> None:
        self.report.testbed_name = testbed_name
        self.report.testbed_instance = testbed_instance

    def write_ok(self) -> None:
        self.report.error = ""
        self._write()

    def _write(self) -> None:
        self.report.time_end = now_formatted()
        filename = self.testresults_directory / "context.json"
        json_text = json.dumps(dataclasses.asdict(self.report), indent=4)
        filename.write_text(json_text)


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
        self.report.commandline = " ".join(testrun.testrun_spec.command)
        self.report.log_output = str(
            logfile.relative_to(self.testresults_directory.directory_top)
        )
        self.report.tentacles = sorted([t.label_short for t in testrun.tentacles])

        # Write the file for the case that it will never finish (timeout/crash).
        self._write()

    def write_ok(self) -> None:
        self._report_written = True
        self.report.error = ""
        self._append_testresults_from_json()
        self._write()

    def write_error(self, error: str) -> None:
        if self._report_written:
            # This file has already been written
            return

        # TODO: Remove this 'if' as soon as 'run-tests.py' returns better error codes.
        # See: https://github.com/octoprobe/testbed_micropython/issues/8
        if self._append_testresults_from_json():
            # The file could be read: We leave the error empty
            self.report.error = ""
            self._write()
            return

        self.report.error = error
        self._write()

    def _write(self) -> None:
        self.report.time_end = now_formatted()
        filename = self.testresults_directory.directory_test / "context_testgroup.json"
        json_text = json.dumps(dataclasses.asdict(self.report), indent=4)
        filename.write_text(json_text)

    def _append_testresults_from_json(self) -> bool:
        filename = self.testresults_directory.directory_test / "_results.json"
        if not filename.exists():
            return False
        json_text = filename.read_text()
        json_dict = json.loads(json_text)
        self.report.results = []
        for failed_test in json_dict["failed_tests"]:
            self.report.results.append(
                ResultTestResult(name=failed_test, result="failed")
            )
        return True
