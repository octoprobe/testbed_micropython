from __future__ import annotations

import dataclasses
import logging
import pathlib
import shutil
import time
import typing

from octoprobe.octoprobe import NTestRun
from octoprobe.util_baseclasses import OctoprobeTestException
from octoprobe.util_constants import relative_cwd
from octoprobe.util_firmware_spec import FirmwareBuildSpec
from octoprobe.util_journalctl import JournalctlObserver
from octoprobe.util_micropython_boards import BoardVariant
from octoprobe.util_pytest import util_logging
from octoprobe.util_pytest.util_resultdir import ResultsDir
from octoprobe.util_pyudev import UDEV_POLLER_LAZY, UdevFailException, UdevPoller
from octoprobe.util_subprocess import SubprocessExitCodeException
from octoprobe.util_testbed_lock import TestbedLock
from octoprobe.util_usb_serial import QueryResultTentacle, QueryResultTentacles

from testbed.reports import util_report_renderer, util_report_tasks

from .. import constants
from ..mptest.util_common import ArgsMpTest
from ..multiprocessing import firmware_bartender, util_multiprocessing
from ..multiprocessing.firmware_bartender import (
    FirmwareBartender,
    FirmwareBartenderBase,
    FirmwareBartenderSkipFlash,
    OctoprobeAppExitException,
)
from ..multiprocessing.test_bartender import (
    AsyncTargetTest,
    CurrentlyNoTestsException,
    TestBartender,
)
from ..tentacle_spec import TentacleMicropython, TentacleSpecMicropython
from ..tentacles_inventory import TENTACLES_INVENTORY
from ..testcollection.baseclasses_run import TestRunSpecs
from ..testcollection.baseclasses_spec import ConnectedTentacles
from ..testcollection.testrun_specs import TestArgs, TestRun
from ..testrunspecs import multinet, perftest, runtests, runtests_net_inet
from ..util_firmware_mpbuild_interface import ArgsFirmware

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent


_TESTBED_LOCK = TestbedLock()

logger = logging.getLogger(__file__)


@dataclasses.dataclass(repr=True)
class EventExitRunOneTest(util_multiprocessing.EventExit):
    testid: str


def get_testrun_specs(only_test: str | None = None) -> TestRunSpecs:
    specs = [
        multinet.TESTRUNSPEC_RUNTESTS_MULTBLUETOOTH,
        multinet.TESTRUNSPEC_RUNTESTS_MULTINET,
        perftest.TESTRUNSPEC_PERFTEST,
        runtests_net_inet.TESTRUNSPEC_RUNTESTS_NET_HOSTED,
        runtests_net_inet.TESTRUNSPEC_RUNTESTS_NET_INET,
        runtests.TESTRUNSPEC_RUNTESTS_BASICS,
        runtests.TESTRUNSPEC_RUNTESTS_EXTMOD_HARDWARE,
    ]

    if only_test is not None:
        err_msg = f"Test '{only_test}' not found. Valid tests are {','.join([s.label for s in specs])}"
        for spec in specs:
            if spec.label == only_test:
                return TestRunSpecs([spec])

        raise ValueError(err_msg)

    return TestRunSpecs(specs)


@dataclasses.dataclass
class Args:
    mp_test: ArgsMpTest | None
    firmware: ArgsFirmware
    only_boards: list[str] | None
    only_test: str | None
    force_multiprocessing: bool

    def __post_init__(self) -> None:
        assert isinstance(self.mp_test, ArgsMpTest | None)
        assert isinstance(self.firmware, ArgsFirmware)
        assert isinstance(self.only_boards, list | None)
        assert isinstance(self.only_test, str | None)
        assert isinstance(self.force_multiprocessing, bool)

    @staticmethod
    def get_default_args() -> Args:
        return Args(
            mp_test=ArgsMpTest(
                micropython_tests=constants.URL_FILENAME_DEFAULT,
            ),
            firmware=ArgsFirmware(
                firmware_build=constants.URL_FILENAME_DEFAULT,
                flash_skip=True,
                flash_force=False,
                git_clean=False,
            ),
            only_boards=None,
            only_test=None,
            force_multiprocessing=False,
        )


def query_connected_tentacles_fast() -> ConnectedTentacles:
    query_result_tentacles = QueryResultTentacle.query_fast()

    return instantiate_tentacles(query_result_tentacles)


def instantiate_tentacles(
    query_result_tentacles: QueryResultTentacles,
) -> ConnectedTentacles:
    assert isinstance(query_result_tentacles, QueryResultTentacles)

    if len(query_result_tentacles) == 0:
        raise OctoprobeAppExitException("No tentacles are connected!")

    tentacles = ConnectedTentacles()
    for query_result_tentacle in query_result_tentacles:
        serial = query_result_tentacle.rp2_serial_number
        assert serial is not None
        try:
            tentacle_instance = TENTACLES_INVENTORY[serial]
        except KeyError:
            logger.warning(
                f"Tentacle with serial {serial} is not specified in TENTACLES_INVENTORY."
            )
            continue

        tentacle = TentacleMicropython(
            tentacle_serial_number=serial,
            tentacle_spec_base=tentacle_instance.tentacle_spec,
            hw_version=tentacle_instance.hw_version,
            hub=query_result_tentacle,
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
        self.ntestrun: NTestRun
        self.test_bartender: TestBartender
        self.firmware_bartender: FirmwareBartenderBase

        self.args = args
        _TESTBED_LOCK.acquire(constants.FILENAME_TESTBED_LOCK)

        if constants.DIRECTORY_TESTRESULTS.exists():
            shutil.rmtree(constants.DIRECTORY_TESTRESULTS, ignore_errors=False)
        constants.DIRECTORY_TESTRESULTS.mkdir(parents=True, exist_ok=True)

        util_logging.init_logging()
        util_logging.Logs(constants.DIRECTORY_TESTRESULTS)

    def init(self) -> None:
        journalctl = JournalctlObserver(
            logfile=constants.DIRECTORY_TESTRESULTS / "journalctl.txt"
        )
        journalctl.start_observer_thread()
        query_result_tentacles = NTestRun.session_powercycle_tentacles()

        connected_tentacles = instantiate_tentacles(
            query_result_tentacles=query_result_tentacles
        )
        if len(connected_tentacles) == 0:
            logger.warning("No tentacles discovered!")
            raise SystemExit(0)

        connected_tentacles = connected_tentacles.get_boards_only(
            boards=self.args.only_boards
        )

        self.ntestrun = NTestRun(connected_tentacles=connected_tentacles)
        self.args.firmware.setup()

        # _testrun.session_powercycle_tentacles()

        testrun_specs = get_testrun_specs(only_test=self.args.only_test)
        testrun_specs.assign_tentacles(
            tentacles=connected_tentacles.get_boards_only(boards=self.args.only_boards)
        )
        self.test_bartender = TestBartender(
            connected_tentacles=connected_tentacles,
            testrun_specs=testrun_specs,
            priority_sorter=TestRun.priority_sorter,
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
                mpbuild_artifacts=constants.DIRECTORY_MPBUILD_ARTIFACTS,
            )

            self.ntestrun.function_setup_infa_and_dut(
                udev_poller=udev_poller,
                tentacle=tentacle,
                directory_logs=constants.DIRECTORY_MPBUILD_ARTIFACTS
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

        async_target = self.firmware_bartender.build_firmwares(
            repo_micropython_firmware=self.args.firmware.repo_micropython_firmware
        )
        if async_target is not None:
            target_ctx.start2(async_target=async_target)

        report_tasks = util_report_tasks.Tasks()

        def generate_task_report(align_time: bool = False) -> None:
            report = util_report_tasks.TaskReport(tasks=report_tasks)
            for suffix, cls_renderer in (
                (".txt", util_report_renderer.RendererAscii),
                (".md", util_report_renderer.RendererMarkdown),
                (".html", util_report_renderer.RendererHtml),
            ):
                filename_report = (
                    constants.DIRECTORY_TESTRESULTS / "task_report"
                ).with_suffix(suffix)
                with filename_report.open("w", encoding="ascii") as f:
                    report.report(renderer=cls_renderer(f))

        def run_all():
            while True:
                try:
                    async_target = self.test_bartender.testrun_next(
                        firmwares_built=self.firmware_bartender.firmwares_built,
                        args=self.args,
                        ntestrun=self.ntestrun,
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
                        logger.info(
                            f"[COLOR_SUCCESS]{event.target_unique_name}: Firmware build took {event.duration_text}. Logfile: {relative_cwd(event.logfile)}"
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
                        logger.debug(f"{event.target_unique_name}: Terminated")
                        target_ctx.close_and_join(self.firmware_bartender.async_targets)
                        if not event.success:
                            msg = f"Firmware build failed: {event.logfile_relative}"
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

        self.ntestrun.session_teardown()
        UDEV_POLLER_LAZY.close()

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
        :type testrun: NTestRun
        """
        assert isinstance(async_target, AsyncTargetTest)
        assert isinstance(target_ctx, util_multiprocessing.TargetCtx)
        assert len(async_target.testrun.list_tentacle_variant) > 0

        logger.debug(
            async_target.testrun.testid_patch(flash_skip=self.args.firmware.flash_skip)
        )

        self._assign_firmware_specs(testrun=async_target.testrun)

        target_ctx.start2(async_target=async_target)

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
    ntestrun: NTestRun,
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
        ntestrun.function_prepare_dut(tentacle=tentacle)
        ntestrun.function_setup_infra(
            udev_poller=UDEV_POLLER_LAZY.udev_poller, tentacle=tentacle
        )
        ntestrun.function_setup_dut_flash(
            udev_poller=UDEV_POLLER_LAZY.udev_poller,
            tentacle=tentacle,
            directory_logs=testresults_directory.directory_test,
        )

    ntestrun.setup_relays(
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
    ntestrun: NTestRun,
    testrun: TestRun,
    repo_micropython_tests: pathlib.Path,
    testresults_directory: ResultsDir,
    testid_patch: str,
) -> bool:
    """
    return True on success
    """
    begin_s = time.monotonic()

    def duration_text(duration_s: float | None = None) -> str:
        if duration_s is None:
            duration_s = time.monotonic() - begin_s
        return f"{duration_s:2.0f}s"

    try:
        _target_run_one_test_async_b(
            ntestrun=ntestrun,
            testrun=testrun,
            repo_micropython_tests=repo_micropython_tests,
            testresults_directory=testresults_directory,
            testid_patch=testid_patch,
            duration_text=duration_text,
        )
        return True
    except (OctoprobeTestException, UdevFailException) as e:
        logger.warning(f"{testid_patch}: Terminating test due to: {e!r}")
        return False
    except SubprocessExitCodeException as e:
        logger.warning(f"{testid_patch}: Terminating test due to: {e!r}")
        return False
    except Exception as e:
        msg = f"{testid_patch}: Terminating test due to: {e!r}"
        logger.error(msg, exc_info=e)
        return False
    finally:
        logger.info(f"TEST TEARDOWN {duration_text()} {testid_patch}")
        try:
            ntestrun.function_teardown(active_tentacles=testrun.tentacles)
        except Exception as e:
            logger.exception(e)
        logger.info(f"TEST END {duration_text()} {testid_patch}")


def target_run_one_test_async(
    arg1: util_multiprocessing.TargetArg1,
    args: Args,
    ntestrun: NTestRun,
    testrun: TestRun,
    repo_micropython_tests: pathlib.Path,
) -> None:
    logfile = pathlib.Path("/here_is_the_logfile")
    success = False
    testid_patch = testrun.testid_patch(flash_skip=args.firmware.flash_skip)
    try:
        arg1.initfunc(arg1=arg1)

        testresults_directory = ResultsDir(
            directory_top=constants.DIRECTORY_TESTRESULTS,
            test_name=testid_patch,
            test_nodeid=testid_patch,
        )

        with util_logging.Logs(testresults_directory.directory_test) as logs:
            logfile = logs.filename

            success = _target_run_one_test_async_a(
                args=args,
                ntestrun=ntestrun,
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
