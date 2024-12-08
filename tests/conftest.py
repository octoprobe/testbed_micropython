import copy
import logging
import pathlib
import shutil
import time
from collections.abc import Iterator

import pytest
from octoprobe.lib_tentacle import Tentacle
from octoprobe.lib_testbed import Testbed
from octoprobe.octoprobe import NTestRun
from octoprobe.util_dut_programmers import FirmwareSpecBase
from octoprobe.util_pytest import util_logging
from octoprobe.util_pytest.util_resultdir import ResultsDir
from octoprobe.util_pytest.util_vscode import break_into_debugger_on_exception
from octoprobe.util_testbed_lock import TestbedLock
from pytest import fixture

import testbed.util_testbed
from testbed.constants import (
    DIRECTORY_TESTRESULTS,
    EnumFut,
    EnumTentacleType,
    FILENAME_TESTBED_LOCK,
)
from testbed.tentacles_inventory import TENTACLES_INVENTORY
from testbed.tentacles_spec import McuConfig, TENTACLES_SPECS
from testbed.util_firmware_specs import (
    PYTEST_OPT_BUILD_FIRMWARE,
    PYTEST_OPT_DOWNLOAD_FIRMWARE,
    get_firmware_specs,
)
from testbed.util_github_micropython_org import (
    DEFAULT_GIT_MICROPYTHON_TESTS,
    PYTEST_OPT_DIR_MICROPYTHON_TESTS,
    PYTEST_OPT_GIT_MICROPYTHON_TESTS,
)

logger = logging.getLogger(__file__)

# TESTBED = testbed.util_testbed.get_testbed()
TESTBED: Testbed | None = None
DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent

DEFAULT_FIRMWARE_SPEC = (
    testbed.constants.DIRECTORY_REPO / "pytest_args_firmware_RPI_PICO2_v1.24.0.json"
)


_TESTBED_LOCK = TestbedLock()

# Uncomment to following line
# to stop tests on exceptions
break_into_debugger_on_exception(globals())


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    """
    This is a pytest hook https://docs.pytest.org/en/7.1.x/reference/reference.html?highlight=pytest_generate_tests#std-hook-pytest_generate_tests

    Give a test function like 'test_i2c()' in 'metafunc', this function will create test calls for possible combinations of tentacles and firmware versions.

    Calls `metafunc.parametrize` which defines the tests that have been be collected.

    :param metafunc: See https://docs.pytest.org/en/7.1.x/reference/reference.html#metafunc
    :type metafunc: pytest.Metafunc
    """
    # print(metafunc.definition.nodeid)
    # for marker in metafunc.definition.own_markers:
    #     print(f" {marker!r}")

    assert TESTBED is not None

    def get_marker(name: str) -> pytest.Mark:
        for marker in metafunc.definition.own_markers:
            if marker.name == name:
                return marker
        raise KeyError(f"Marker '{name}' not found!")

    def get_required_futs() -> list[EnumFut]:
        try:
            marker_required_futs = get_marker(name="required_futs")
        except KeyError:
            return []
        assert isinstance(marker_required_futs, pytest.Mark)
        return list(marker_required_futs.args)

    _required_futs = get_required_futs()
    for fut in _required_futs:
        assert EnumFut(fut), fut

    if "mcu" in metafunc.fixturenames:
        list_tentacles: list[Tentacle] = []
        for firmware_spec in get_firmware_specs(
            config=metafunc.config,
            tentacles=TESTBED.tentacles,
        ):
            assert isinstance(firmware_spec, FirmwareSpecBase)
            tentacles = EnumTentacleType.TENTACLE_MCU.get_tentacles_for_type(
                tentacles=TESTBED.tentacles,
                required_futs=_required_futs,
            )
            tentacles = list(filter(firmware_spec.match_board, tentacles))
            if len(tentacles) == 0:
                futs_text = ", ".join(f.name for f in _required_futs)
                msg = f"No tentacle where selected for testing firmware '{firmware_spec.board_variant}'. Required futs: {futs_text}"
                logger.warning(msg)
            for tentacle in tentacles:
                # Need to create a copy to the tentacle as we
                # modify it for the test.
                _tentacle = copy.copy(tentacle)
                _tentacle.firmware_spec = firmware_spec
                list_tentacles.append(_tentacle)

        if len(list_tentacles) == 0:
            assert isinstance(firmware_spec, FirmwareSpecBase)
            msg = f"No tentacle where selected for testing firmware '{firmware_spec.board_variant}'."
            # raise ValueError(msg)
            logger.warning(msg)
            return
        # print(f"LEN={len(list_tentacles)}")
        metafunc.parametrize("mcu", list_tentacles, ids=lambda t: t.pytest_id)

    if "device_potpourry" in metafunc.fixturenames:
        tentacles = EnumTentacleType.TENTACLE_DEVICE_POTPOURRY.get_tentacles_for_type(
            TESTBED.tentacles,
            required_futs=_required_futs,
        )
        if len(tentacles) == 0:
            return
        assert len(tentacles) > 0
        metafunc.parametrize(
            "device_potpourry",
            tentacles,
            ids=lambda t: t.pytest_id,
        )

    if "daq_saleae" in metafunc.fixturenames:
        tentacles = EnumTentacleType.TENTACLE_DAQ_SALEAE.get_tentacles_for_type(
            TESTBED.tentacles,
            required_futs=_required_futs,
        )
        # assert len(tentacles) > 0
        if len(tentacles) == 0:
            msg = "No TENTACLE_DAQ_SALEAE tentacle was selected. Might be the required FUTS specified for TENTACLE_DAQ_SALEAE"
            raise ValueError(msg)

        metafunc.parametrize(
            "daq_saleae",
            tentacles,
            ids=lambda t: t.pytest_id,
        )


@pytest.fixture
def required_futs(request: pytest.FixtureRequest) -> list[EnumFut]:
    """
    Returns all FUTS (Feature Under Test) which are required
    by the test function referencing this fixture.
    """
    for m in request.node.own_markers:
        assert isinstance(m, pytest.Mark)
        if m.name == "required_futs":
            return list(m.args)
    return []


@pytest.fixture
def active_tentacles(request: pytest.FixtureRequest) -> list[Tentacle]:
    """
    Returns all active tentacles which are required
    by the test function referencing this fixture.
    """

    def inner() -> Iterator[Tentacle]:
        if not hasattr(request.node, "callspec"):
            return
        for _param_name, param_value in request.node.callspec.params.items():
            if isinstance(param_value, Tentacle):
                yield param_value

    return list(inner())


@fixture(scope="session", autouse=True)
def session_setup(request: pytest.FixtureRequest) -> Iterator[NTestRun]:
    """
    Setup and teardown octoprobe and all connected tentacles.

    Now we loop over all tests an return for every test a `NTestRun` structure.
    Using this structure, the test find there tentacles, git-repos etc.
    """
    assert TESTBED is not None

    firmware_git_url = request.config.getoption(PYTEST_OPT_BUILD_FIRMWARE)
    _testrun = NTestRun(testbed=TESTBED, firmware_git_url=firmware_git_url)

    # _testrun.session_powercycle_tentacles()

    yield _testrun

    _testrun.session_teardown()


@fixture(scope="function", autouse=True)
def setup_tentacles(
    session_setup: NTestRun,  # pylint: disable=W0621:redefined-outer-name
    required_futs: tuple[EnumFut],  # pylint: disable=W0621:redefined-outer-name
    active_tentacles: list[Tentacle],  # pylint: disable=W0621:redefined-outer-name
    testresults_directory: ResultsDir,  # pylint: disable=W0621:redefined-outer-name
) -> Iterator[None]:
    """
    Runs setup and teardown for every single test:

    * Setup

      * powercycle the tentacles
      * Turns on the 'active' LED on the tentacles involved
      * Flash firmware
      * Set the relays according to `@pytest.mark.required_futs(EnumFut.FUT_I2C)`.

    * yields to the test function
    * Teardown

      * Resets the relays.

    :param testrun: The structure created by `testrun()`
    :type testrun: NTestRun
    """
    if len(active_tentacles) == 0:
        # No tentacle has been specified: This is just a normal pytest.
        # Do not call setup/teardown
        yield
        return

    with util_logging.Logs(testresults_directory.directory_test):
        begin_s = time.monotonic()

        def duration_text(duration_s: float | None = None) -> str:
            if duration_s is None:
                duration_s = time.monotonic() - begin_s
            return f"{duration_s:2.0f}s"

        try:
            logger.info(
                f"TEST SETUP {duration_text(0.0)} {testresults_directory.test_nodeid}"
            )
            session_setup.function_build_firmwares(
                active_tentacles=active_tentacles,
                testresults_mpbuild=testresults_directory.directory_top / "mpbuild",
            )
            session_setup.function_prepare_dut()
            session_setup.function_setup_infra()
            session_setup.function_setup_dut(active_tentacles=active_tentacles)

            session_setup.setup_relays(futs=required_futs, tentacles=active_tentacles)
            logger.info(
                f"TEST BEGIN {duration_text()} {testresults_directory.test_nodeid}"
            )
            yield

        except Exception as e:
            logger.warning(f"Exception during test: {e!r}")
            logger.exception(e)
            raise
        finally:
            logger.info(
                f"TEST TEARDOWN {duration_text()} {testresults_directory.test_nodeid}"
            )
            try:
                session_setup.function_teardown(active_tentacles=active_tentacles)
            except Exception as e:
                logger.exception(e)
            logger.info(
                f"TEST END {duration_text()} {testresults_directory.test_nodeid}"
            )


@pytest.fixture(scope="function")
def testresults_directory(request: pytest.FixtureRequest) -> ResultsDir:
    """
    Returns the log directory for the test function referencing this fixture.
    """
    return ResultsDir(
        directory_top=DIRECTORY_TESTRESULTS,
        test_name=request.node.name,
        test_nodeid=request.node.nodeid,
    )


def pytest_sessionstart(session: pytest.Session):
    """
    Called after the Session object has been created and
    before performing collection and entering the run test loop.
    """
    _TESTBED_LOCK.acquire(FILENAME_TESTBED_LOCK)

    if DIRECTORY_TESTRESULTS.exists():
        shutil.rmtree(DIRECTORY_TESTRESULTS, ignore_errors=False)
    DIRECTORY_TESTRESULTS.mkdir(parents=True, exist_ok=True)

    util_logging.init_logging()
    util_logging.Logs(DIRECTORY_TESTRESULTS)

    query_result_tentacles = NTestRun.session_powercycle_tentacles()
    tentacles: list[Tentacle] = []
    for query_result_tentacle in query_result_tentacles:
        serial = query_result_tentacle.rp2_serial_number
        assert serial is not None
        try:
            hw_version, enum_tag = TENTACLES_INVENTORY[serial]
        except KeyError:
            logger.warning(
                f"Tentacle with serial {serial} is not specified in TENTACLES_INVENTORY."
            )
            continue

        tentacle_spec = TENTACLES_SPECS[enum_tag]

        tentacle = Tentacle[McuConfig, EnumTentacleType, EnumFut](
            tentacle_serial_number=serial,
            tentacle_spec=tentacle_spec,
            hw_version=hw_version,
        )
        tentacle.assign_connected_hub(query_result_tentacle=query_result_tentacle)
        tentacles.append(tentacle)

    if len(tentacles) == 0:
        raise ValueError("No tentacles are connected!")

    global TESTBED  # pylint: disable=W0603:global-statement
    assert TESTBED is None
    TESTBED = Testbed(workspace="based-on-connected-boards", tentacles=tentacles)


def pytest_sessionfinish(session: pytest.Session):
    _TESTBED_LOCK.unlink()


def pytest_addoption(parser: pytest.Parser) -> None:
    """
    This function name is reserved by pytest.
    See https://docs.pytest.org/en/7.1.x/reference/reference.html#initialization-hooks.

    It will be called to determine the program arguments.

    When calling :code:`pytest --help`, below arguments will be listed!
    """
    parser.addoption(
        PYTEST_OPT_DOWNLOAD_FIRMWARE,
        action="store",
        default=None,
        help="A json file specifying the firmware",
    )
    parser.addoption(
        PYTEST_OPT_BUILD_FIRMWARE,
        action="store",
        default=None,
        help=f"The url to a git repo to be cloned and compiled. Syntax: {DEFAULT_GIT_MICROPYTHON_TESTS}",
    )
    parser.addoption(
        PYTEST_OPT_GIT_MICROPYTHON_TESTS,
        action="store",
        default=None,
        help=f"The micropython repo to check out. Will be used for the tests. Syntax: {DEFAULT_GIT_MICROPYTHON_TESTS}",
    )
    parser.addoption(
        PYTEST_OPT_DIR_MICROPYTHON_TESTS,
        action="store",
        default=None,
        help="The directory name to a checked out micropython repo. Will be used for the tests. Syntax: ~/micropython tests/micropython_repo",
    )
