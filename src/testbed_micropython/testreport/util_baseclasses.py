from __future__ import annotations

import dataclasses
import enum
import pathlib

from octoprobe.util_cached_git_repo import GitMetadata, GitSpec
from octoprobe.util_constants import DirectoryTag

from ..testcollection.testrun_specs import MICROPYTHON_DIRECTORY_TESTS
from .util_markdown2 import md_escape, md_link


class Outcome(enum.StrEnum):
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"

    @property
    def short(self) -> str:
        return {
            Outcome.PASSED: "pass",
            Outcome.FAILED: "FAIL",
            Outcome.SKIPPED: "skip",
        }[self]


@dataclasses.dataclass(slots=True)
class ResultTestOutcome:
    name: str
    """
    extmod_hardware/machine_pwm.py
    """
    outcome: str = ""
    text: str = ""

    def name_markdown(self, tests: ResultContext) -> str:
        """
        Example return: [RUN-TESTS_EXTMOD_HARDWARE](https://github.com/micropython/micropython/tree/master/tests/extmod_hardware/machine_pwm.py	)
        """
        assert isinstance(tests, ResultContext)

        python_test = MICROPYTHON_DIRECTORY_TESTS + "/" + self.name

        # Find the git_ref for the micropython tests repository
        ref_tests = tests.git_ref.get(DirectoryTag.T, None)
        if ref_tests is None:
            return self.name
        ref = GitRef.factory(ref=ref_tests)

        # Build the link
        return md_link(label=self.name, link=ref.link(file=python_test))


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
        return f"{self.url_link}/{file}".replace("//", "/")


@dataclasses.dataclass(slots=True)
class ResultContext:
    """
    Represents 'context.json'
    The Metadata for the testresults:
    * git refs
    * 'mptest' command line parameters
    """

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
    ref_firmware_metadata: GitMetadata | None = None
    # "git describe --dirty"
    ref_tests: str = ""
    # "https://github.com/dpgeorge/micropython@master",
    ref_tests_metadata: GitMetadata | None = None
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

    @classmethod
    def from_dict(cls, json_dict: dict) -> ResultContext:
        for key in ("ref_firmware_metadata", "ref_tests_metadata"):
            if json_dict[key] is None:
                continue
            json_dict[key] = GitMetadata(**json_dict[key])

        result_context = ResultContext(**json_dict)
        return result_context

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


@dataclasses.dataclass(slots=True)
class ResultTestGroup:
    """
    This corresponds to 'context_testgroup.json'.
    It consists of:
    * The metadata of a test results directory.
    * The outcome of all tests
    """

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
    outcomes: list[ResultTestOutcome] = dataclasses.field(default_factory=list)
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
    def results_failed(self) -> list[ResultTestOutcome]:
        return self._result_count(Outcome.FAILED)

    @property
    def results_skipped(self) -> list[ResultTestOutcome]:
        return self._result_count(Outcome.SKIPPED)

    @property
    def results_success(self) -> list[ResultTestOutcome]:
        return self._result_count(Outcome.PASSED)

    def _result_count(self, outcome: Outcome) -> list[ResultTestOutcome]:
        test_results = [r for r in self.outcomes if r.outcome == outcome]
        return sorted(test_results, key=lambda r: r.name)

    def testgroup_markdown(
        self,
        result_context: ResultContext,
        testid: bool = False,
    ) -> str:
        """
        Example return:
          testid=False:
            [RUN-TESTS_EXTMOD_HARDWARE](https://github.com/micropython/micropython/tree/master/tests/run-tests.py)
          testid=True:
            [RUN-TESTS_EXTMOD_HARDWARE@5f2a-ADAITSYBITSYM0](https://github.com/micropython/micropython/tree/master/tests/run-tests.py)
        """
        assert isinstance(result_context, ResultContext)
        from ..mptest.util_testrunner import get_testrun_spec

        # Find the testgroup 'RUN-TESTS_EXTMOD_HARDWARE'
        testspec = get_testrun_spec(self.testgroup)
        if testspec is None:
            return self.testgroup
        python_test = MICROPYTHON_DIRECTORY_TESTS + "/" + testspec.command_executable

        md = self.testgroup_markdown2(
            result_context=result_context,
            python_test=python_test,
            testid=testid,
        )
        # TODO: Is this still required?
        if testid:
            md = md.replace("@", "<br>@")
        return md

    def testgroup_markdown2(
        self,
        result_context: ResultContext,
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
        assert isinstance(result_context, ResultContext)

        # Find the git_ref for the micropython tests repository
        ref_tests = result_context.git_ref.get(DirectoryTag.T, None)
        if ref_tests is None:
            return f"{self.testgroup} ({python_test})"
        ref = GitRef.factory(ref=ref_tests)

        # Build the link
        label = self.testid if testid else self.testgroup

        return md_link(label=label, link=ref.link(file=python_test))

    def test_filename_link(
        self,
        result_context: ResultContext,
        python_test: str,
    ) -> str:
        """
        Example return:
          [basics/builtin_pow3_intbig.py](https://github.com/micropython/micropython/tree/master/tests/basics/builtin_pow3_intbig.py)
        """
        assert isinstance(result_context, ResultContext)

        # Find the git_ref for the micropython tests repository
        ref_tests = result_context.git_ref.get(DirectoryTag.T, None)
        if ref_tests is None:
            return md_escape(python_test)
        ref = GitRef.factory(ref=ref_tests)

        return md_link(
            label=python_test,
            link=ref.link(file=f"/{MICROPYTHON_DIRECTORY_TESTS}/{python_test}"),
        )
