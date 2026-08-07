import pathlib

import pytest

from testbed_micropython.report_test import util_xfail

FILENAME_XFAIL = pathlib.Path(__file__).with_name("test_xfail_input.json")


@pytest.mark.parametrize(
    "expected,testgroup,test_name,board_variant",
    (
        (
            True,
            "RUN-TESTS_STANDARD",
            "extmod/socket_udp_nonblock.py",
            "PYBV11",
        ),
        (
            False,
            "RUN-TESTS_STANDARD_NATIVE",
            "extmod/socket_udp_nonblock.py",
            "DUMMY",
        ),
        (
            # Test '*' on testgroup
            True,
            "anyvalue",
            "testgroup.py",
            "TESTGROUP",
        ),
        (
            # Test '*' on test_name
            True,
            "RUN-TESTS_STANDARD",
            "anyvalue",
            "PYBV11",
        ),
        (
            # Test "*" on board_variant
            True,
            "RUN-TESTS_STANDARD",
            "test_name.py",
            "ANYVALUE",
        ),
    ),
)
def test_xfail(
    testgroup: str,
    test_name: str,
    board_variant: str,
    expected: bool,
) -> None:
    xfail_file = util_xfail.XFailFile.factory(filename=FILENAME_XFAIL)
    match = xfail_file.xfail_list.match

    assert (
        match(
            testgroup=testgroup,
            test_name=test_name,
            board_variant=board_variant,
        )
        == expected
    )
