from __future__ import annotations

import dataclasses
import enum
import json
import os
import pathlib
import platform
import sys
import time

from octoprobe.util_cached_git_repo import GitSpec
from octoprobe.util_constants import DirectoryTag
from octoprobe.util_pytest.util_resultdir import ResultsDir

from ..testcollection.testrun_specs import MICROPYTHON_DIRECTORY_TESTS, TestRun
from .util_markdown2 import md_link

TIME_FORMAT = "%Y-%m-%d_%H-%M-%S-%Z"

FILENAME_CONTEXT_JSON = "context.json"

FILENAME_CONTEXT_TESTGROUP_JSON = "context_testgroup.json"


class Outcome(enum.StrEnum):
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclasses.dataclass
class ResultTestResult:
    name: str
    """
    extmod_hardware/machine_pwm.py
    """
    result: str = ""
    text: str = ""

    def name_markdown(self, tests: ResultTests) -> str:
        """
        Example return: [RUN-TESTS_EXTMOD_HARDWARE](https://github.com/micropython/micropython/tree/master/tests/extmod_hardware/machine_pwm.py	)
        """
        assert isinstance(tests, ResultTests)

        python_test = MICROPYTHON_DIRECTORY_TESTS + "/" + self.name

        # Find the git_ref for the micropython tests repository
        ref_tests = tests.git_ref.get(DirectoryTag.T, None)
        if ref_tests is None:
            return self.name
        ref = GitRef.factory(ref=ref_tests)

        # Build the link
        return md_link(label=self.name, link=ref.link(file=python_test))


@dataclasses.dataclass
class ResultTestGroup:
    directory_relative: str = ""
    testgroup: str = ""
    testid: str = ""
    commandline: str = ""
    # RUN-TESTS_STANDARD
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
    msg_error: str = "Test never finished..."
    """
    Error message.
    "": No error
    """
    msg_skipped: str = ""
    """
    Example:
    It looks like the firmware has not been compiled, but the test requires '--via-mpy'!
    """

    @property
    def results_failed(self) -> list[ResultTestResult]:
        return self._result_count(Outcome.FAILED)

    @property
    def results_skipped(self) -> list[ResultTestResult]:
        return self._result_count(Outcome.SKIPPED)

    @property
    def results_success(self) -> list[ResultTestResult]:
        return self._result_count(Outcome.PASSED)

    def _result_count(self, outcome: Outcome) -> list[ResultTestResult]:
        test_results = [r for r in self.results if r.result == outcome]
        return sorted(test_results, key=lambda r: r.name)

    def testgroup_markdown(self, tests: ResultTests, testid: bool = False) -> str:
        """
        Example return:
          testid=False:
            [RUN-TESTS_EXTMOD_HARDWARE](https://github.com/micropython/micropython/tree/master/tests/run-tests.py)
          testid=True:
            [RUN-TESTS_EXTMOD_HARDWARE@5f2a-ADAITSYBITSYM0](https://github.com/micropython/micropython/tree/master/tests/run-tests.py)
        """
        assert isinstance(tests, ResultTests)
        from ..mptest.util_testrunner import get_testrun_spec

        # Find the testgroup 'RUN-TESTS_EXTMOD_HARDWARE'
        testspec = get_testrun_spec(self.testgroup)
        if testspec is None:
            return self.testgroup
        python_test = MICROPYTHON_DIRECTORY_TESTS + "/" + testspec.command_executable

        md = self.testgroup_markdown2(
            tests=tests, python_test=python_test, testid=testid
        )
        # TODO: Is this still required?
        if testid:
            md = md.replace("@", "<br>@")
        return md

    def testgroup_markdown2(
        self,
        tests: ResultTests,
        python_test: str,
        testid: bool,
    ) -> str:
        """
        Example return:
          testid=False:
            [RUN-TESTS_EXTMOD_HARDWARE](https://github.com/micropython/micropython/tree/master/tests/run-tests.py)
          testid=True:
            [RUN-TESTS_EXTMOD_HARDWARE@5f2a-ADAITSYBITSYM0](https://github.com/micropython/micropython/tree/master/tests/run-tests.py)
        """
        assert isinstance(tests, ResultTests)

        # Find the git_ref for the micropython tests repository
        ref_tests = tests.git_ref.get(DirectoryTag.T, None)
        if ref_tests is None:
            return f"{self.testgroup} ({python_test})"
        ref = GitRef.factory(ref=ref_tests)

        # Build the link
        label = self.testid if testid else self.testgroup

        return md_link(label=label, link=ref.link(file=python_test))


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
    ref_firmware_describe: str = ""
    # "git describe --dirty"
    ref_tests: str = ""
    # "https://github.com/dpgeorge/micropython@master",
    ref_tests_describe: str = ""
    # "git describe --dirty"
    trigger: str = ""
    # "https://github.com/micropython/micropython/pull/17091"
    commandline: str = ""
    # mptest.cli test --only-test=RUN-TESTS_EXTMOD_HARDWARE --no-multiprocessing --flash-skip
    log_output: str = ""
    # logger_20_info.log
    log_directory: str = ""
    error: str = "Test never finished..."
    directories: dict[str, str] = dataclasses.field(default_factory=dict)
    # {"F": "/home/xy/firmware/microython", "R", "/home/xy/results"}
    git_ref: dict[str, str] = dataclasses.field(default_factory=dict)
    # {"F": "https://github.com/micropython/micropython.git@master"}

    def set_directory(self, tag: DirectoryTag, directory: str | pathlib.Path) -> None:
        if isinstance(directory, pathlib.Path):
            directory = str(directory)
        assert isinstance(tag, DirectoryTag)
        assert isinstance(directory, str)
        self.directories[tag.name] = directory

    def set_git_ref(self, tag: DirectoryTag, git_ref: str) -> None:
        assert isinstance(tag, DirectoryTag)
        assert isinstance(git_ref, str)
        self.git_ref[tag.name] = git_ref

    @property
    def ref_firmware2(self) -> GitRef:
        return GitRef.factory(self.ref_firmware)

    @property
    def ref_tests2(self) -> GitRef:
        return GitRef.factory(self.ref_tests)

    @property
    def commandline_markdown(self) -> str:
        markdown = "<br>".join([f"```{arg}```" for arg in self.commandline.split(" ")])

        # Avoid github to make a link out of
        # https://github.com/micropython/micropython.git@master
        # markdown = markdown.replace("https://", "https:// ")
        # markdown = markdown.replace("@", " @ ")

        # for ref in (self.ref_firmware, self.ref_tests):
        #     ref_markdown = GitRef.factory(self.ref_firmware).markdown
        #     markdown_try = markdown.replace(ref, ref_markdown)
        #     if markdown_try.find("[[") == -1:
        #         # Avoid double replacement which results in
        #         # [[https://github.com/micropython/micropython.git@master](https://github.com/micropython/micropython/tree/master)](https://github.com/micropython/micropython/tree/master)
        #         markdown = markdown_try

        return markdown


@dataclasses.dataclass
class DataSummaryLine:
    label: str
    group_run: int = 0
    group_skipped: int = 0
    group_error: int = 0
    tests_skipped: int = 0
    tests_passed: int = 0
    tests_failed: int = 0


@dataclasses.dataclass
class Data:
    tests: ResultTests
    testgroups: list[ResultTestGroup] = dataclasses.field(default_factory=list)

    @property
    def testgroups_ordered(self) -> list[ResultTestGroup]:
        return sorted(self.testgroups, key=lambda testgroup: testgroup.testid)

    @property
    def summary(self) -> list[DataSummaryLine]:
        dict_summary: dict[str, DataSummaryLine] = {}
        for testgroup in self.testgroups:
            line = dict_summary.get(testgroup.testgroup, None)
            if line is None:
                # Example label: [RUN-TESTS_EXTMOD_HARDWARE](https://github.com/micropython/micropython/tree/master/tests/run-tests.py)
                label = testgroup.testgroup_markdown(tests=self.tests)
                line = DataSummaryLine(label=label)
                dict_summary[testgroup.testgroup] = line
            assert isinstance(line, DataSummaryLine)

            if testgroup.msg_skipped != "":
                line.group_skipped += 1
            elif testgroup.msg_error != "":
                line.group_error += 1
            else:
                line.group_run += 1

            for result in testgroup.results:
                if result.result == Outcome.FAILED:
                    line.tests_failed += 1
                    continue
                if result.result == Outcome.SKIPPED:
                    line.tests_skipped += 1
                    continue
                assert result.result == Outcome.PASSED
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
        lines.insert(0, total_line)
        return lines

    @staticmethod
    def gather_json_files(directory_results: pathlib.Path) -> Data:
        """
        Loop over all testresults and collect and read json files.
        Return the collected data.
        """

        def collect_top():
            filename = directory_results / FILENAME_CONTEXT_JSON
            json_text = filename.read_text()
            json_dict = json.loads(json_text)
            tests = ResultTests(**json_dict)
            return Data(tests=tests)

        data = collect_top()

        def collect():
            for filename in directory_results.glob(
                f"*/{FILENAME_CONTEXT_TESTGROUP_JSON}"
            ):
                json_text = filename.read_text()
                json_dict = json.loads(json_text)
                testgroup = ResultTestGroup(**json_dict)
                testgroup.results = [ResultTestResult(**r) for r in testgroup.results]
                data.testgroups.append(testgroup)

        collect()
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
        self.report = ResultTests()
        self.report.time_start = now_formatted()
        self.report.commandline = " ".join(sys.argv)
        self.report.ref_firmware = ref_firmware
        self.report.ref_tests = ref_tests
        self.report.log_output = DirectoryTag.R.render_relative_to(
            top=testresults_directory, filename=log_output
        )
        self.report.log_directory = (
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

        self.report.trigger = get_trigger()
        self._write()

    def set_testbed(self, testbed_name: str, testbed_instance: str) -> None:
        self.report.testbed_name = testbed_name
        self.report.testbed_instance = testbed_instance

    def write_ok(self) -> None:
        self.report.error = ""
        self._write()

    def write_context_json(self) -> None:
        filename = self.testresults_directory / FILENAME_CONTEXT_JSON
        json_text = json.dumps(dataclasses.asdict(self.report), indent=4)
        filename.write_text(json_text)

    def _write(self) -> None:
        self.report.time_end = now_formatted()
        self.write_context_json()

        from .testreport import ReportRenderer

        renderer = ReportRenderer(directory_results=self.testresults_directory)
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
        self.report.commandline = " ".join(testrun.testrun_spec.command)
        self.report.log_output = DirectoryTag.R.render_relative_to(
            top=self.testresults_directory.directory_top,
            filename=logfile,
        )
        self.report.tentacles = sorted([t.label_short for t in testrun.tentacles])

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

        self.report.results = []
        list_results = json_dict.get("results", None)
        if list_results is None:
            # structure of _results.json before https://github.com/micropython/micropython/pull/17373
            for outcome in Outcome:
                for test_name in json_dict.get(f"{outcome}_tests", []):
                    self.report.results.append(
                        ResultTestResult(name=test_name, result=outcome)
                    )
            return True

        fix_outcomes = {"pass": "passed", "skip": "skipped", "fail": "failed"}
        for test_name, _outcome, reason in list_results:
            _outcome = fix_outcomes[_outcome]
            outcome = Outcome(_outcome)
            self.report.results.append(
                ResultTestResult(name=test_name, result=outcome, text=reason)
            )

        return True


@dataclasses.dataclass
class GitRef:
    git_spec: GitSpec

    @staticmethod
    def factory(ref: str) -> GitRef:
        """
        Examples:
        https://github.com/micropython/micropython.git
        https://github.com/micropython/micropython.git~17232
        https://github.com/micropython/micropython.git@1.25.0
        https://github.com/micropython/micropython.git~17232@1.25.0
        """
        assert isinstance(ref, str)
        return GitRef(git_spec=GitSpec.parse(git_ref=ref))

    @property
    def ref(self) -> str:
        return self.git_spec.git_spec

    @property
    def url_without_git(self) -> str:
        """
        The url WITHOUT '.git'
        "https://github.com/micropython/micropython"
        """
        return self.git_spec.url_without_git

    @property
    def branch(self) -> str | None:
        "v1.25.0"
        return self.git_spec.branch

    @property
    def pr(self) -> str | None:
        "17232"
        return self.git_spec.pr

    @property
    def url_link(self) -> str:
        """
        Example:
        https://github.com/micropython/micropython/tree/master
        https://github.com/micropython/micropython/pull/17419
        """
        return self.git_spec.url_link

    @property
    def markdown(self) -> str:
        return md_link(label=self.ref, link=self.url_link)

    # def markdown2(self, label: str, file: str) -> str:
    #     """
    #     Example url: https://github.com/micropython/micropython/
    #     Example branch: master
    #     Example label: RUN-TESTS_STANDARD
    #     Example file: tests/run-tests.py
    #     Return: [RUN-TESTS_STANDARD](https://github.com/micropython/micropython/tree/master/tests/run-tests.py)
    #     """
    #     if self.url is None:
    #         return file
    #     link = f"{self.url_link}/{file}".replace("//", "/")
    #     return f"[{label} ({file})]({link})"

    def link(self, file: str) -> str | None:
        """
        Example url: https://github.com/micropython/micropython/
        Example branch: master
        Example file: tests/run-tests.py
        Return: https://github.com/micropython/micropython/tree/master/tests/run-tests.py
        """
        return f"{self.url_link}/{file}"
