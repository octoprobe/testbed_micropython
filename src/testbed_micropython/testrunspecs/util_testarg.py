from __future__ import annotations

import dataclasses
import re

RE_NUMBER = re.compile(r"((?P<number>\d+)|(?P<text>^\d+))")
"""
This is an argument passed to: mptest '--only-test=RUN-TESTS_STANDARD:--via-mpy --test-dirs=micropython',

Examples:
RUN-TESTS_STANDARD
RUN-TESTS_STANDARD:
RUN-TESTS_STANDARD:--via-mpy
RUN-TESTS_STANDARD:--via-mpy --test-dirs=micropython
"""


@dataclasses.dataclass(frozen=True, slots=True, repr=True)
class TestArg:
    testname: str
    """
    Example: TESTS_STANDARD
    """
    command: str
    """
    Example: --via-mpy --test-dirs=micropython
    """

    @property
    def has_args(self) -> bool:
        return self.command != ""

    @staticmethod
    def parse(testspec_with_args: str) -> TestArg:
        testspec, _, arguments = testspec_with_args.partition(":")
        return TestArg(testname=testspec, command=arguments)
