from __future__ import annotations

import dataclasses
import logging
import pathlib
import shutil
import subprocess
import sys
import time
import typing

from octoprobe.octoprobe import CtxTestRun
from octoprobe.usb_tentacle.usb_tentacle import (
    UsbTentacles,
    assert_serialdelimtied_valid,
)
from octoprobe.util_baseclasses import OctoprobeAppExitException, OctoprobeTestException
from octoprobe.util_constants import DirectoryTag
from octoprobe.util_firmware_spec import FirmwareBuildSpec
from octoprobe.util_journalctl import JournalctlObserver
from octoprobe.util_micropython_boards import BoardVariant
from octoprobe.util_pytest import util_logging
from octoprobe.util_pytest.util_resultdir import ResultsDir
from octoprobe.util_pyudev import UDEV_POLLER_LAZY, UdevFailException, UdevPoller
from octoprobe.util_subprocess import SubprocessExitCodeException
from octoprobe.util_testbed_lock import TestbedLock

from testbed_micropython.mptest.util_baseclasses import ArgsQuery
from testbed_micropython.testreport.util_testreport import (
    ReportTestgroup,
    ReportTests,
)

from .. import constants
from ..mptest.util_common import ArgsMpTest
from ..multiprocessing import firmware_bartender, util_multiprocessing
from ..multiprocessing.firmware_bartender import (
    FirmwareBartender,
    FirmwareBartenderBase,
    FirmwareBartenderSkipFlash,
)
from ..multiprocessing.test_bartender import (
    AsyncTargetTest,
    CurrentlyNoTestsException,
    TestBartender,
)
from ..reports import util_report_renderer, util_report_tasks
from ..tentacle_spec import TentacleMicropython, TentacleSpecMicropython
from ..tentacles_inventory import TENTACLES_INVENTORY
from ..testcollection.baseclasses_run import TestRunSpecs
from ..testcollection.baseclasses_spec import ConnectedTentacles
from ..testcollection.testrun_specs import TestArgs, TestRun, TestRunSpec
from ..testrunspecs import multinet, perftest, runtests, runtests_net_inet
from ..util_firmware_mpbuild_interface import ArgsFirmware

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent


_TESTBED_LOCK = TestbedLock()

logger = logging.getLogger(__file__)


@dataclasses.dataclass(repr=True)
class EventExitRunOneTest(util_multiprocessing.EventExit):
    testid: str


_TESTRUN_SPECS = [
    multinet.TESTRUNSPEC_RUNTESTS_MULTBLUETOOTH,
    multinet.TESTRUNSPEC_RUNTESTS_MULTINET,
    perftest.TESTRUNSPEC_PERFTEST,
    runtests_net_inet.TESTRUNSPEC_RUNTESTS_NET_HOSTED,
    runtests_net_inet.TESTRUNSPEC_RUNTESTS_NET_INET,
    runtests.TESTRUNSPEC_RUNTESTS_STANDARD,
    runtests.TESTRUNSPEC_RUNTESTS_EXTMOD_HARDWARE,
]


def get_testrun_spec(label: str) -> TestRunSpec|None:
    for spec in _TESTRUN_SPECS:
        if spec.label == label:
            return spec
    return None


def get_testrun_specs(query: ArgsQuery | None = None) -> TestRunSpecs:
    if query is None:
        query = ArgsQuery()
    assert isinstance(query, ArgsQuery)

    valid_tests = {s.label for s in _TESTRUN_SPECS}

    def assert_valid_tests(tests: set[str]) -> None:
        for test in tests:
            if test not in valid_tests:
                raise ValueError(
                    f"Test '{test}' not found. Valid tests are {','.join(sorted(valid_tests))}"
                )

    assert_valid_tests(tests=query.only)
    assert_valid_tests(tests=query.skip)

    selected_tests = valid_tests
    if len(query.only) > 0:
        selected_tests.intersection_update(query.only)
    if len(query.skip) > 0:
        selected_tests.difference_update(query.skip)

    return TestRunSpecs(
        [spec for spec in _TESTRUN_SPECS if spec.label in sorted(selected_tests)]
    )


@dataclasses.dataclass
class Args:
    mp_test: ArgsMpTest | None
    firmware: ArgsFirmware
    directory_results: pathlib.Path
    force_multiprocessing: bool
    query_test: ArgsQuery
    query_board: ArgsQuery

    def __post_init__(self) -> None:
        assert isinstance(self.mp_test, ArgsMpTest | None)
        assert isinstance(self.firmware, ArgsFirmware)
        assert isinstance(self.directory_results, pathlib.Path)
        assert isinstance(self.force_multiprocessing, bool)
        assert isinstance(self.query_test, ArgsQuery)
        assert isinstance(self.query_board, ArgsQuery)

    @staticmethod
    def get_default_args(
        directory_git_cache: pathlib.Path,
        directory_results: pathlib.Path,
    ) -> Args:
        return Args(
            mp_test=ArgsMpTest(
                micropython_tests=constants.URL_FILENAME_DEFAULT,
            ),
            firmware=ArgsFirmware(
                firmware_build=constants.URL_FILENAME_DEFAULT,
                flash_skip=True,
                flash_force=False,
                git_clean=False,
                directory_git_cache=directory_git_cache,
            ),
            directory_results=directory_results,
            query_board=ArgsQuery(),
            query_test=ArgsQuery(),
            force_multiprocessing=False,
        )


def query_connected_tentacles_fast() -> ConnectedTentacles:
    usb_tentacles = UsbTentacles.query(poweron=False)

    return instantiate_tentacles(usb_tentacles)


def instantiate_tentacles(usb_tentacles: UsbTentacles) -> ConnectedTentacles:
    assert isinstance(usb_tentacles, UsbTentacles)

    if len(usb_tentacles) == 0:
        raise OctoprobeAppExitException("No tentacles are connected!")

    tentacles = ConnectedTentacles()
    for usb_tentacle in usb_tentacles:
        pico_infra = usb_tentacle.pico_infra
        if pico_infra is None:
            continue
        serial_delimited = pico_infra.serial_delimited
        if serial_delimited is None:
            continue
        assert_serialdelimtied_valid(serial_delimited=serial_delimited)
        try:
            tentacle_instance = TENTACLES_INVENTORY[serial_delimited]

        except KeyError:
            logger.warning(
                f"Tentacle with serial {serial_delimited} is not specified in TENTACLES_INVENTORY."
            )
            continue

        tentacle = TentacleMicropython(
            tentacle_instance=tentacle_instance,
            tentacle_serial_number=serial_delimited,
            usb_tentacle=usb_tentacle,
        )

        tentacles.append(tentacle)

    return tentacles


class TestRunner:
    def __init__(self, args: Args) -> None:
        """
        Initialize logging
        Query the tentacles.
        Clone github.
        """
        assert isinstance(args, Args)
        self.ctxtestrun: CtxTestRun
        self.test_bartender: TestBartender
        self.firmware_bartender: FirmwareBartenderBase
        self.args = args

        util_logging.init_logging()

        _TESTBED_LOCK.acquire(constants.FILENAME_TESTBED_LOCK)

        if args.directory_results.exists():
            shutil.rmtree(args.directory_results, ignore_errors=False)
        args.directory_results.mkdir(parents=True, exist_ok=True)

        logs = util_logging.Logs(args.directory_results)
        ref_tests = "Not specified (no tests to run)"
        if args.mp_test is not None:
            ref_tests = args.mp_test.micropython_tests
        self.report_testgroup = ReportTests(
            testresults_directory=args.directory_results,
            log_output=logs.filename,
            ref_firmware=args.firmware.ref_firmware,
            ref_tests=ref_tests,
        )
        if args.mp_test is not None:
            self.set_git_ref(DirectoryTag.T, args.mp_test.micropython_tests)
        self.set_git_ref(DirectoryTag.F, args.firmware.ref_firmware)
        self.set_directory(DirectoryTag.R, args.directory_results)
        self.set_directory(DirectoryTag.P, pathlib.Path(sys.executable).parent)
        self.set_directory(DirectoryTag.W, pathlib.Path.cwd())

    def set_directory(self, tag: DirectoryTag, directory: str | pathlib.Path) -> None:
        self.report_testgroup.report.set_directory(tag=tag, directory=directory)

    def set_git_ref(self, tag: DirectoryTag, git_ref: str) -> None:
        self.report_testgroup.report.set_git_ref(tag=tag, git_ref=git_ref)

    def init(self) -> None:
        journalctl = JournalctlObserver(
            logfile=self.args.directory_results / "journalctl.txt"
        )
        journalctl.start_observer_thread()
        # TODO: Is the name 'query_result_tentacles' correct?
        query_result_tentacles = CtxTestRun.session_powercycle_tentacles()

        connected_tentacles = instantiate_tentacles(
            usb_tentacles=query_result_tentacles
        )
        if len(connected_tentacles) == 0:
            logger.warning("No tentacles discovered!")
            raise SystemExit(0)

        connected_tentacles = connected_tentacles.query_boards(query=ArgsQuery())

        self.ctxtestrun = CtxTestRun(connected_tentacles=connected_tentacles)
        self.args.firmware.setup()
        self.set_directory(DirectoryTag.F, self.args.firmware.repo_micropython_firmware)

        # _testrun.session_powercycle_tentacles()

        testrun_specs = get_testrun_specs(query=self.args.query_test)
        testrun_specs.assign_tentacles(
            tentacles=connected_tentacles.query_boards(query=self.args.query_board)
        )
        self.test_bartender = TestBartender(
            connected_tentacles=connected_tentacles,
            testrun_specs=testrun_specs,
            priority_sorter=TestRun.priority_sorter,
            directory_results=self.args.directory_results,
        )
        if self.args.firmware.flash_skip:
            self.firmware_bartender = FirmwareBartenderSkipFlash()
        else:
            self.firmware_bartender = FirmwareBartender(
                self.test_bartender.testrun_specs
            )
        if self.args.firmware.flash_force:
            for tentacle in connected_tentacles:
                tentacle.tentacle_state.flash_force = True

        def update_testbed_instance() -> None:
            for connected_tentacle in connected_tentacles:
                self.report_testgroup.set_testbed(
                    testbed_name=connected_tentacle.tentacle_instance.testbed_name,
                    testbed_instance=connected_tentacle.tentacle_instance.testbed_instance,
                )

        update_testbed_instance()

    def flash(self, udev_poller: UdevPoller, last_variant: bool) -> None:
        assert isinstance(last_variant, bool)

        for tentacle in self.test_bartender.connected_tentacles:
            tentacle_spec = tentacle.tentacle_spec
            assert isinstance(tentacle_spec, TentacleSpecMicropython)
            variant = tentacle_spec.get_first_last_variant(last=last_variant)

            tentacle.tentacle_state.firmware_spec = FirmwareBuildSpec(
                board_variant=BoardVariant(board=tentacle_spec.board, variant=variant)
            )

            self.args.firmware.build_firmware(
                tentacle=tentacle,
                mpbuild_artifacts=self.args.directory_results
                / constants.SUBDIR_MPBUILD,
            )

            self.ctxtestrun.function_setup_infa_and_dut(
                udev_poller=udev_poller,
                tentacle=tentacle,
                directory_logs=self.args.directory_results
                / tentacle.tentacle_state.firmware_spec.board_variant.name_normalized,
            )

    def run_all_in_sequence(
        self,
        target_ctx: util_multiprocessing.TargetCtx,
    ) -> None:
        assert self.args.mp_test is not None
        repo_micropython_tests = self.args.mp_test.clone_git_micropython_tests(
            directory_git_cache=constants.DIRECTORY_GIT_CACHE
        )
        self.set_directory(DirectoryTag.T, str(repo_micropython_tests))
        async_target = self.firmware_bartender.build_firmwares(
            directory_mpbuild_artifacts=self.args.directory_results
            / constants.SUBDIR_MPBUILD,
            repo_micropython_firmware=self.args.firmware.repo_micropython_firmware,
        )
        if async_target is not None:
            target_ctx.start(async_target=async_target)

        report_tasks = util_report_tasks.Tasks()

        def generate_task_report(align_time: bool = False) -> None:
            report = util_report_tasks.TaskReport(tasks=report_tasks)
            for suffix, cls_renderer in (
                (".txt", util_report_renderer.RendererAscii),
                (".md", util_report_renderer.RendererMarkdown),
                (".html", util_report_renderer.RendererHtml),
            ):
                filename_report = (
                    self.args.directory_results / "task_report"
                ).with_suffix(suffix)
                with filename_report.open("w", encoding="ascii") as f:
                    report.report(renderer=cls_renderer(f))

        def run_all():
            while True:
                try:
                    async_target = self.test_bartender.testrun_next(
                        firmwares_built=self.firmware_bartender.firmwares_built,
                        args=self.args,
                        ctxtestrun=self.ctxtestrun,
                        repo_micropython_tests=repo_micropython_tests,
                    )

                    #
                    # Run test
                    #
                    logger.info(
                        f"[COLOR_INFO]{async_target.target_unique_name}: Started"
                    )
                    self.run_one_test(
                        async_target=async_target,
                        target_ctx=target_ctx,
                    )
                except CurrentlyNoTestsException:
                    logger.debug(
                        "CurrentlyNoTestsException: Wait for firmware to be built or tentacles to be freed!"
                    )

                self.firmware_bartender.handle_timeouts()
                self.test_bartender.handle_timeouts(report_tasks)

                for event in target_ctx.iter_queue():

                    def handle_event(event: util_multiprocessing.EventBase):
                        async_target_firmware = self.firmware_bartender.get_by_event(
                            event
                        )
                        if async_target_firmware is not None:
                            async_target_firmware.target.handle_exit_event(event)
                            return
                        async_target_test = self.test_bartender.get_by_event(event)
                        if async_target_test is not None:
                            async_target_test.target.handle_exit_event(event)
                            return
                        # raise ValueError(f"Bartender not found for event: {event}!")

                    handle_event(event)
                    generate_task_report()

                    if isinstance(event, util_multiprocessing.EventLog):
                        logger.info(
                            f"[COLOR_INFO]{event.target_unique_name}: {event.msg}"
                        )
                    elif isinstance(event, EventExitRunOneTest):
                        async_target_test = self.test_bartender.testrun_done(
                            event=event
                        )
                        report_tasks.append(async_target_test.report_task)

                    elif isinstance(event, firmware_bartender.EventFirmwareSpec):
                        logfile = DirectoryTag.R.render_relative_to(
                            top=self.args.directory_results, filename=event.logfile
                        )

                        logger.info(
                            f"[COLOR_SUCCESS]{event.target_unique_name}: Firmware build took {event.duration_text}. Logfile: {logfile}"
                        )
                        self.firmware_bartender.firmware_built(event.firmware_spec)
                        report_tasks.append(
                            util_report_tasks.Task(
                                label=event.target_unique_name,
                                start_s=event.start_s,
                                end_s=event.end_s,
                                tentacles=[],
                            )
                        )
                    elif isinstance(event, firmware_bartender.EventExitFirmware):
                        logger.debug(f"{event.target_unique_name}: Completed")
                        target_ctx.close_and_join(self.firmware_bartender.async_targets)
                        if not event.success:
                            logfile = DirectoryTag.R.render_relative_to(
                                top=self.args.directory_results,
                                filename=event.logfile,
                            )
                            msg = f"Firmware build failed: {logfile}"
                            logger.error(
                                f"[COLOR_ERROR]{event.target_unique_name}: {msg}"
                            )
                            raise OctoprobeAppExitException(msg)
                    else:
                        raise ValueError("Programming error!")

                if self.test_bartender.tests_todo == 0:
                    if target_ctx.done(self.test_bartender.async_targets):
                        if target_ctx.done(self.firmware_bartender.async_targets):
                            logger.info(f"Done in {target_ctx.duration_text}")
                            return

        run_all()

        target_ctx.close_and_join(self.firmware_bartender.async_targets)
        target_ctx.close_and_join(self.test_bartender.async_targets)

        self.ctxtestrun.session_teardown()
        UDEV_POLLER_LAZY.close()

        self.report_testgroup.write_ok()
        generate_task_report(align_time=True)

    def run_one_test(
        self,
        async_target: AsyncTargetTest,
        target_ctx: util_multiprocessing.TargetCtx,
    ) -> None:
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
        :type testrun: CtxTestRun
        """
        assert isinstance(async_target, AsyncTargetTest)
        assert isinstance(target_ctx, util_multiprocessing.TargetCtx)
        assert len(async_target.testrun.list_tentacle_variant) > 0

        logger.debug(
            async_target.testrun.testid_patch(flash_skip=self.args.firmware.flash_skip)
        )

        self._assign_firmware_specs(testrun=async_target.testrun)

        target_ctx.start(async_target=async_target)

    def _assign_firmware_specs(self, testrun: TestRun) -> None:
        """
        Assign firmware_spec to each tentacle
        """
        for tentacle_variant in testrun.list_tentacle_variant:
            tentacle = tentacle_variant.tentacle
            tentacle_spec = tentacle.tentacle_spec
            assert isinstance(tentacle_spec, TentacleSpecMicropython)
            tentacle.tentacle_state.firmware_spec = (
                self.firmware_bartender.get_firmware_spec(
                    board=tentacle_spec.board, variant=tentacle_variant.variant
                )
            )


def _target_run_one_test_async_b(
    ctxtestrun: CtxTestRun,
    testrun: TestRun,
    repo_micropython_tests: pathlib.Path,
    testresults_directory: ResultsDir,
    testid_patch: str,
    duration_text: typing.Callable,
) -> None:
    """
    This is a 'global' method and as such may be used within process or
    be called by the multiprocessing module.
    """
    logger.info(f"TEST SETUP {duration_text(0.0)} {testid_patch}")

    for tentacle in testrun.tentacles:
        ctxtestrun.function_prepare_dut(tentacle=tentacle)
        ctxtestrun.function_setup_infra(
            udev_poller=UDEV_POLLER_LAZY.udev_poller,
            tentacle=tentacle,
        )
        ctxtestrun.function_setup_dut_flash(
            udev_poller=UDEV_POLLER_LAZY.udev_poller,
            tentacle=tentacle,
            directory_logs=testresults_directory.directory_test,
        )

    ctxtestrun.setup_relays(
        futs=(testrun.testrun_spec.required_fut,),
        tentacles=testrun.tentacles,
    )
    logger.info(f"TEST BEGIN {duration_text()} {testid_patch}")

    with testrun.active_led_on:
        testrun.test(
            testargs=TestArgs(
                testresults_directory=testresults_directory,
                repo_micropython_tests=repo_micropython_tests,
            )
        )
        logger.info("Test SUCCESS")


def _target_run_one_test_async_a(
    args: Args,
    ctxtestrun: CtxTestRun,
    logfile: pathlib.Path,
    testrun: TestRun,
    repo_micropython_tests: pathlib.Path,
    testresults_directory: ResultsDir,
    testid_patch: str,
) -> bool:
    """
    return True on success
    """
    begin_s = time.monotonic()
    report_test = ReportTestgroup(
        testresults_directory=testresults_directory,
        testrun=testrun,
        logfile=logfile,
    )

    def duration_text(duration_s: float | None = None) -> str:
        if duration_s is None:
            duration_s = time.monotonic() - begin_s
        return f"{duration_s:2.0f}s"

    try:
        _target_run_one_test_async_b(
            ctxtestrun=ctxtestrun,
            testrun=testrun,
            repo_micropython_tests=repo_micropython_tests,
            testresults_directory=testresults_directory,
            testid_patch=testid_patch,
            duration_text=duration_text,
        )
        report_test.write_ok()
        return True
    except (
        OctoprobeTestException,
        UdevFailException,
        SubprocessExitCodeException,
        subprocess.TimeoutExpired,
    ) as e:
        msg = f"{testid_patch}: Terminating test due to: {e!r}"
        logger.warning(msg)
        report_test.write_error(error=msg)
        return False
    except Exception as e:
        msg = f"{testid_patch}: Terminating test due to: {e!r}"
        logger.error(msg, exc_info=e)
        report_test.write_error(error=msg)
        return False
    finally:
        logger.info(f"TEST TEARDOWN {duration_text()} {testid_patch}")
        try:
            ctxtestrun.function_teardown(active_tentacles=testrun.tentacles)
        except Exception as e:
            logger.exception(e)
        logger.info(f"TEST END {duration_text()} {testid_patch}")


def target_run_one_test_async(
    arg1: util_multiprocessing.TargetArg1,
    args: Args,
    ctxtestrun: CtxTestRun,
    testrun: TestRun,
    repo_micropython_tests: pathlib.Path,
) -> None:
    logfile = pathlib.Path("/here_is_the_logfile")
    success = False
    testid_patch = testrun.testid_patch(flash_skip=args.firmware.flash_skip)
    try:
        arg1.initfunc(arg1=arg1)

        testresults_directory = ResultsDir(
            directory_top=args.directory_results,
            test_name=testid_patch,
            test_nodeid=testid_patch,
        )

        with util_logging.Logs(testresults_directory.directory_test) as logs:
            logfile = logs.filename

            success = _target_run_one_test_async_a(
                args=args,
                ctxtestrun=ctxtestrun,
                logfile=logfile,
                testrun=testrun,
                repo_micropython_tests=repo_micropython_tests,
                testresults_directory=testresults_directory,
                testid_patch=testid_patch,
            )
    finally:
        # We have to send a exit event before returing!
        arg1.queue_put(
            EventExitRunOneTest(
                arg1.target_unique_name,
                success=success,
                logfile=logfile,
                testid=testid_patch,
            )
        )
