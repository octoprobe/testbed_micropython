import pathlib

from testbed_micropython.report_test import util_xfail

FILENAME_XFAIL = pathlib.Path(__file__).with_name("test_xfail_input.json")


def test_xfail() -> None:
    xfail_file = util_xfail.XFailFile.factory(filename=FILENAME_XFAIL)

    assert xfail_file.xfail_list.match(
        testgroup="RUN-TESTS_STANDARD",
        test_name="extmod/socket_udp_nonblock.py",
        board_variant="PYBV11",
    )
    assert not xfail_file.xfail_list.match(
        testgroup="RUN-TESTS_STANDARD_NATIVE",
        test_name="extmod/socket_udp_nonblock.py",
        board_variant="DUMMY",
    )
