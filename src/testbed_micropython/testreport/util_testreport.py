from __future__ import annotations

import dataclasses
import json
import os
import pathlib
import platform
import sys
import time

from octoprobe.util_constants import DirectoryTag
from octoprobe.util_pytest.util_resultdir import ResultsDir

from ..testcollection.testrun_specs import MICROPYTHON_DIRECTORY_TESTS, TestRun

TIME_FORMAT = "%Y-%m-%d_%H-%M-%S-%Z"

FILENAME_CONTEXT_JSON = "context.json"


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
        return f"[{self.name}]({ref.link(file=python_test)})"


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
    error: str = "Test never finished..."
    """
    Error message.
    "": No error
    """

    @property
    def results_failed(self) -> list[ResultTestResult]:
        failed = [r for r in self.results if r.result == "failed"]
        return sorted(failed, key=lambda r: r.name)

    def testgroup_markdown(self, tests: ResultTests) -> str:
        """
        Example return: [RUN-TESTS_EXTMOD_HARDWARE](https://github.com/micropython/micropython/tree/master/tests/run-tests.py)
        """
        from ..mptest.util_testrunner import get_testrun_spec

        # Find the testgroup 'RUN-TESTS_EXTMOD_HARDWARE'
        testspec = get_testrun_spec(self.testgroup)
        if testspec is None:
            return self.testgroup
        python_test = MICROPYTHON_DIRECTORY_TESTS + "/" + testspec.command_executable

        return self.testgroup_markdown2(tests=tests, python_test=python_test)

    def testgroup_markdown2(self, tests: ResultTests, python_test: str) -> str:
        """
        Example return: [RUN-TESTS_EXTMOD_HARDWARE](https://github.com/micropython/micropython/tree/master/tests/run-tests.py)
        """
        assert isinstance(tests, ResultTests)

        # Find the git_ref for the micropython tests repository
        ref_tests = tests.git_ref.get(DirectoryTag.T, None)
        if ref_tests is None:
            return f"{self.testgroup} ({python_test})"
        ref = GitRef.factory(ref=ref_tests)

        # Build the link
        return f"[{self.testgroup}]({ref.link(file=python_test)})"


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


@dataclasses.dataclass
class DataSummaryLine:
    testgroup: ResultTestGroup
    group_run: int = 0
    group_error: int = 0
    tests_skipped: int = 0
    tests_passed: int = 0
    tests_failed: int = 0

    def testgroup_markdown(self, tests: ResultTests) -> str:
        """
        Example return: [RUN-TESTS_EXTMOD_HARDWARE](https://github.com/micropython/micropython/tree/master/tests/run-tests.py)
        """
        return self.testgroup.testgroup_markdown(tests=tests)


@dataclasses.dataclass
class Data:
    tests: ResultTests
    testgroups: list[ResultTestGroup] = dataclasses.field(default_factory=list)

    @property
    def summary(self) -> list[DataSummaryLine]:
        dict_summary: dict[str, DataSummaryLine] = {}
        for testgroup in self.testgroups:
            line = dict_summary.get(testgroup.testgroup, None)
            if line is None:
                line = DataSummaryLine(testgroup)
                dict_summary[testgroup.testgroup] = line
            assert isinstance(line, DataSummaryLine)
            line.group_run += 1
            if testgroup.error != "":
                line.group_error += 1
            for result in testgroup.results:
                if result.result == "failed":
                    line.tests_failed += 1
        return sorted(dict_summary.values(), key=lambda line: line.testgroup.testgroup)

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
            for filename in directory_results.glob("*/context_testgroup.json"):
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

    def _write(self) -> None:
        self.report.time_end = now_formatted()
        filename = self.testresults_directory / FILENAME_CONTEXT_JSON
        json_text = json.dumps(dataclasses.asdict(self.report), indent=4)
        filename.write_text(json_text)

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


@dataclasses.dataclass
class GitRef:
    ref: str
    url: str | None
    """
    None if undefined
    """
    branch: str

    @staticmethod
    def factory(ref: str) -> GitRef:
        """
        Examples:
        https://github.com/micropython/micropython.git@master
        https://github.com/micropython/micropython.git@dc46cf15c17ab5bd8371c00e11ee9743229b7868
        https://github.com/micropython/micropython.git@v1.25.0
        """
        tag_at = "@"
        pos = ref.find(tag_at)
        if pos == -1:
            return GitRef(ref=ref, url=None, branch="")

        url = ref[:pos]
        tag_git = ".git"
        if url.endswith(tag_git):
            url = url[: -len(tag_git)]
        branch = ref[pos + len(tag_at) :]
        return GitRef(ref=ref, url=url, branch=branch)

    @property
    def url_link(self) -> str:
        """
        Example:
        https://github.com/micropython/micropython/tree/master
        """
        return f"{self.url}/tree/{self.branch}"

    @property
    def markdown(self) -> str:
        if self.url is None:
            return self.ref
        return f"[{self.ref}]({self.url_link})"

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
        if self.url is None:
            return None
        return f"{self.url_link}/{file}"
