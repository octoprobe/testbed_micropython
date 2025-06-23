import dataclasses

import pytest

from testbed_micropython.testrunspecs import util_testarg


@dataclasses.dataclass
class Ttestparam:
    testspec_with_args: str
    expected_testspec: str
    expected_command: str

    @property
    def pytest_id(self) -> str:
        return self.testspec_with_args.replace(" ", "-")


_TESTPARAMS = [
    Ttestparam(
        testspec_with_args="RUN-TESTS_STANDARD",
        expected_testspec="RUN-TESTS_STANDARD",
        expected_command="",
    ),
    Ttestparam(
        testspec_with_args="RUN-TESTS_STANDARD:",
        expected_testspec="RUN-TESTS_STANDARD",
        expected_command="",
    ),
    Ttestparam(
        testspec_with_args="RUN-TESTS_STANDARD:run-tests.py --via-mpy",
        expected_testspec="RUN-TESTS_STANDARD",
        expected_command="run-tests.py --via-mpy",
    ),
    Ttestparam(
        testspec_with_args="RUN-TESTS_STANDARD:run-tests.py --via-mpy --test-dirs=micropython",
        expected_testspec="RUN-TESTS_STANDARD",
        expected_command="run-tests.py --via-mpy --test-dirs=micropython",
    ),
]


def _test_testspec(testparam: Ttestparam) -> None:
    testspec = util_testarg.TestArg.parse(testparam.testspec_with_args)
    assert testspec.testname == testparam.expected_testspec
    assert testspec.command == testparam.expected_command


@pytest.mark.parametrize(
    "testparam", _TESTPARAMS, ids=lambda testparam: testparam.pytest_id
)
def test_testspec(testparam: Ttestparam) -> None:
    _test_testspec(testparam)


if __name__ == "__main__":
    _test_testspec(testparam=_TESTPARAMS[0])
