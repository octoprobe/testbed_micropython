from __future__ import annotations

from testbed_micropython.constants import EnumFut
from testbed_micropython.mptest import util_testrunner
from testbed_micropython.mptest.util_baseclasses import ArgsQuery
from testbed_micropython.testrunspecs import run_mpremote_tests

LABEL = "RUN-MPREMOTE_TESTS"


def test_mpremote_registered() -> None:
    """The mpremote test group is part of the static inventory."""
    assert LABEL in util_testrunner.DICT_TESTRUN_SPECS
    spec = util_testrunner.DICT_TESTRUN_SPECS[LABEL]
    assert spec is run_mpremote_tests.TESTRUNSPEC_RUN_MPREMOTE_TESTS
    assert spec.required_fut is EnumFut.FUT_MCU_ONLY
    assert spec.requires_reference_tentacle is False
    assert spec.command_executable == "run-mpremote-tests.sh"
    assert spec.command_subdir == "tools/mpremote/tests"


def test_mpremote_in_get_testrun_specs() -> None:
    """Without a query, the group is enumerated (used for shell completion)."""
    labels = [spec.label for spec in util_testrunner.get_testrun_specs()]
    assert LABEL in labels


def test_mpremote_only_test_selection() -> None:
    """'--only-test=RUN-MPREMOTE_TESTS' selects exactly this group."""
    query = ArgsQuery(only_test={LABEL})
    specs = util_testrunner.get_testrun_specs(query=query)
    assert [spec.label for spec in specs] == [LABEL]


def test_mpremote_skip_test_selection() -> None:
    """'--skip-test=RUN-MPREMOTE_TESTS' removes this group."""
    query = ArgsQuery(skip_test={LABEL})
    labels = [spec.label for spec in util_testrunner.get_testrun_specs(query=query)]
    assert LABEL not in labels
