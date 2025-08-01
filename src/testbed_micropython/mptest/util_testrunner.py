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
from octoprobe.util_baseclasses import (
    OctoprobeAppExitException,
    OctoprobeTestException,
    OctoprobeTestSkipException,
)
from octoprobe.util_cached_git_repo import CachedGitRepo, GitMetadata
from octoprobe.util_constants import DirectoryTag
from octoprobe.util_firmware_spec import FirmwareBuildSpec
from octoprobe.util_journalctl import JournalctlObserver
from octoprobe.util_micropython_boards import BoardVariant
from octoprobe.util_pytest import util_logging
from octoprobe.util_pytest.util_resultdir import ResultsDir
from octoprobe.util_pyudev import UDEV_POLLER_LAZY, UdevFailException, UdevPoller
from octoprobe.util_subprocess import SubprocessExitCodeException
from octoprobe.util_testbed_lock import TestbedLock

from .. import constants, util_multiprocessing
from ..mptest.util_common import ArgsMpTest
from ..report_task import util_report_renderer, util_report_tasks
from ..report_test.util_testreport import (
    ReportTestgroup,
    ReportTests,
)
from ..tentacle_spec import TentacleMicropython, TentacleSpecMicropython
from ..tentacles_inventory import TENTACLES_INVENTORY
from ..testcollection.baseclasses_run import TestRunSpecs
from ..testcollection.baseclasses_spec import ConnectedTentacles
from ..testcollection.testrun_specs import TestArgs, TestRun, TestRunSpec
from ..testrunspecs import (
    run_multinet,
    run_natmodtests,
    run_perftest,
    runtests,
    runtests_net_inet,
)
from ..testrunspecs.run_natmodtests import NATMOD_EXAMPLES
from ..testrunspecs.util_testarg import TestArg
from ..util_firmware_mpbuild_interface import ArgsFirmware
from .util_baseclasses import ArgsQuery

if typing.TYPE_CHECKING:
    from ..bartenders.test_bartender import (
        AsyncTargetTest,
        TestBartender,
    )

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent


_TESTBED_LOCK = TestbedLock()

logger = logging.getLogger(__file__)


@dataclasses.dataclass(repr=True)
class EventExitRunOneTest(util_multiprocessing.EventExit):
    testid: str


_TESTRUN_SPECS = [
    run_multinet.TESTRUNSPEC_RUNTESTS_MULTBLUETOOTH,
    run_multinet.TESTRUNSPEC_RUNTESTS_MULTINET,
    run_perftest.TESTRUNSPEC_PERFTEST,
    runtests_net_inet.TESTRUNSPEC_RUNTESTS_NET_HOSTED,
    runtests_net_inet.TESTRUNSPEC_RUNTESTS_NET_INET,
    runtests.TESTRUNSPEC_RUNTESTS_STANDARD,
    runtests.TESTRUNSPEC_RUNTESTS_STANDARD_VIA_MPY,
    runtests.TESTRUNSPEC_RUNTESTS_STANDARD_NATIVE,
    runtests.TESTRUNSPEC_RUNTESTS_EXTMOD_HARDWARE,
    runtests.TESTRUNSPEC_RUNTESTS_EXTMOD_HARDWARE_NATIVE,
    run_natmodtests.TESTRUNSPEC_RUN_NATMODTESTS,
]
DICT_TESTRUN_SPECS = {s.label: s for s in _TESTRUN_SPECS}


def get_testrun_spec(label: str) -> TestRunSpec | None:
    for spec in _TESTRUN_SPECS:
        if spec.label == label:
            return spec
    return None


def get_testrun_specs(query: ArgsQuery | None = None) -> TestRunSpecs:
    if query is None:
        query = ArgsQuery()
    assert isinstance(query, ArgsQuery)

    assert (len(query.only) == 0) or (len(query.skip) == 0)

    query_only = [TestArg.parse(t) for t in query.only]
    query_skip = [TestArg.parse(t) for t in query.skip]

    def assert_valid_tests(testargs: list[TestArg]) -> None:
        for testarg in testargs:
            if testarg.testname not in DICT_TESTRUN_SPECS:
                raise ValueError(
                    f"Test '{testarg.testname}' not found. Valid tests are {','.join(sorted(DICT_TESTRUN_SPECS.keys()))}"
                )

    assert_valid_tests(testargs=query_only)
    assert_valid_tests(testargs=query_skip)

    def factory(testargs: list[TestArg]) -> TestRunSpecs:
        assert isinstance(testargs, list)
        for testarg in testargs:
            assert isinstance(testarg, TestArg)

        def factory_inner(testspec: TestArg) -> TestRunSpec:
            assert isinstance(testspec, TestArg)
            s = DICT_TESTRUN_SPECS[testspec.testname]
            if testspec.has_args:
                command = testspec.command.split(" ")
                return dataclasses.replace(
                    s,
                    command=command,  # type: ignore[arg-type]
                )

            return s

        return TestRunSpecs([factory_inner(testarg) for testarg in testargs])

    if len(query_skip) > 0:
        selected_tests = set(DICT_TESTRUN_SPECS.keys()) - query.skip
        return factory([TestArg.parse(t) for t in selected_tests])

    if len(query_only) == 0:
        # Run all tests
        return factory([TestArg.parse(t) for t in DICT_TESTRUN_SPECS.keys()])

    if len(query_only) > 1:
        if len([q for q in query_only if q.has_args]) >= 1:
            raise ValueError(
                f"'--test-only' with arguments may not be used once: {' '.join(query.only)}:"
            )

    return factory(query_only)


@dataclasses.dataclass
class Args:
    mp_test: ArgsMpTest | None
    firmware: ArgsFirmware
    directory_results: pathlib.Path
    force_multiprocessing: bool
    query_test: ArgsQuery
    query_board: ArgsQuery
    reference_board: str = constants.DEFAULT_REFERENCE_BOARD
    """
    The board to be used a reference for WLAN/Bluetooth tests.
    Example: RPI_PICO_W
    """

    def __post_init__(self) -> None:
        assert isinstance(self.mp_test, ArgsMpTest | None)
        assert isinstance(self.firmware, ArgsFirmware)
        assert isinstance(self.directory_results, pathlib.Path)
        assert isinstance(self.force_multiprocessing, bool)
        assert isinstance(self.query_test, ArgsQuery)
        assert isinstance(self.query_board, ArgsQuery)
        assert isinstance(self.reference_board, str)

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
        from ..bartenders import firmware_bartender

        self.ctxtestrun: CtxTestRun
        self.test_bartender: TestBartender
        self.tentacle_reference: TentacleMicropython | None
        self.firmware_bartender: firmware_bartender.FirmwareBartenderBase
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
        self.report_testgroup.result_context.set_directory(tag=tag, directory=directory)

        def git_metadata() -> GitMetadata | None:
            from testbed_micropython.util_firmware_mpbuild import PLACEHOLDER_PATH

            if str(directory) == PLACEHOLDER_PATH:
                return None
            return CachedGitRepo.git_metadata(pathlib.Path(directory))

        if tag is DirectoryTag.T:
            self.report_testgroup.result_context.ref_tests_metadata = git_metadata()
        if tag is DirectoryTag.F:
            self.report_testgroup.result_context.ref_firmware_metadata = git_metadata()

    def set_git_ref(self, tag: DirectoryTag, git_ref: str) -> None:
        self.report_testgroup.result_context.set_git_ref(tag=tag, git_ref=git_ref)

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

        connected_tentacles = connected_tentacles.query_boards(
            query=ArgsQuery(),
            testrun_specs=TestRunSpecs(),
        )

        self.ctxtestrun = CtxTestRun(connected_tentacles=connected_tentacles)
        CachedGitRepo.clean_directory_work_repo(
            directory_cache=constants.DIRECTORY_GIT_CACHE
        )
        self.args.firmware.setup()
        self.set_directory(DirectoryTag.F, self.args.firmware.repo_micropython_firmware)

        # _testrun.session_powercycle_tentacles()

        testrun_specs = get_testrun_specs(query=self.args.query_test)
        self.tentacle_reference = connected_tentacles.find_first_tentacle(
            board=self.args.reference_board
        )
        selected_tentacles = connected_tentacles.query_boards(
            query=self.args.query_board,
            tentacle_reference=self.tentacle_reference,
            testrun_specs=testrun_specs,
        )
        testrun_specs.assign_tentacles(
            tentacles=selected_tentacles,
            count=self.args.query_test.count,
            flash_skip=self.args.firmware.flash_skip,
        )

        from ..bartenders.test_bartender import TestBartender

        self.test_bartender = TestBartender(
            connected_tentacles=selected_tentacles,
            tentacle_reference=self.tentacle_reference,
            testrun_specs=testrun_specs,
            priority_sorter=TestRun.priority_sorter,
            directory_results=self.args.directory_results,
        )

        from ..bartenders import firmware_bartender

        if self.args.firmware.flash_skip:
            self.firmware_bartender = firmware_bartender.FirmwareBartenderSkipFlash()
        else:
            self.firmware_bartender = firmware_bartender.FirmwareBartender(
                self.test_bartender.testrun_specs
            )
        if self.args.firmware.flash_force:
            for tentacle in selected_tentacles:
                tentacle.tentacle_state.flash_force = True

        def update_testbed_instance() -> None:
            for tentacle in selected_tentacles:
                self.report_testgroup.set_testbed(
                    testbed_name=tentacle.tentacle_instance.testbed_name,
                    testbed_instance=tentacle.tentacle_instance.testbed_instance,
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
        self.set_directory(DirectoryTag.T, repo_micropython_tests)
        directory_mpbuild_artifacts = (
            self.args.directory_results / constants.SUBDIR_MPBUILD
        )
        if self.test_bartender.contains_test_with_label(
            label=run_natmodtests.TESTRUNSPEC_RUN_NATMODTESTS.label
        ):
            NATMOD_EXAMPLES.compile_all(
                repo_micropython_tests=repo_micropython_tests,
                directory_mpbuild_artifacts=directory_mpbuild_artifacts,
            )
        async_target = self.firmware_bartender.build_firmwares(
            directory_mpbuild_artifacts=directory_mpbuild_artifacts,
            repo_micropython_firmware=self.args.firmware.repo_micropython_firmware,
            reference_board=self.args.reference_board,
        )
        if async_target is not None:
            target_ctx.start(async_target=async_target)

        # Write 'context_json' in case the tests will timeout!
        self.report_testgroup.write_context_json()

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
            from ..bartenders.test_bartender import CurrentlyNoTestsException

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
                        f"[COLOR_INFO]{async_target.target_unique_name}: Started test {self.test_bartender.testrun_specs.tests_progress}"
                    )
                    self.run_one_test(
                        async_target=async_target,
                        target_ctx=target_ctx,
                    )
                except CurrentlyNoTestsException:
                    logger.debug(
                        "CurrentlyNoTestsException: Wait for firmware to be built or tentacles to be freed!"
                    )
                    if target_ctx.done(self.test_bartender.async_targets):
                        if target_ctx.done(self.firmware_bartender.async_targets):
                            logger.info(f"Done in {target_ctx.duration_text}")
                            return

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

                    from ..bartenders import firmware_bartender

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
        from ..bartenders.test_bartender import AsyncTargetTest

        assert isinstance(async_target, AsyncTargetTest)
        assert isinstance(target_ctx, util_multiprocessing.TargetCtx)

        logger.debug(async_target.testrun.testid)

        self._assign_firmware_specs(testrun=async_target.testrun)

        target_ctx.start(async_target=async_target)

    def _assign_firmware_specs(self, testrun: TestRun) -> None:
        """
        Assign firmware_spec to each tentacle
        """

        def assign(tentacle: TentacleMicropython, variant: str) -> None:
            assert isinstance(tentacle, TentacleMicropython)
            tentacle.tentacle_state.firmware_spec = (
                self.firmware_bartender.get_firmware_spec(
                    board=tentacle.tentacle_spec.board,
                    variant=variant,
                )
            )

        assign(
            tentacle=testrun.tentacle_variant.tentacle,
            variant=testrun.tentacle_variant.variant,
        )
        if testrun.tentacle_reference is not None:
            assign(tentacle=testrun.tentacle_reference, variant="")


def _target_run_one_test_async_b(
    ctxtestrun: CtxTestRun,
    testrun: TestRun,
    repo_micropython_tests: pathlib.Path,
    testresults_directory: ResultsDir,
    testid: str,
    duration_text: typing.Callable,
) -> None:
    """
    This is a 'global' method and as such may be used within process or
    be called by the multiprocessing module.
    """
    logger.info(f"TEST SETUP {duration_text(0.0)} {testid}")

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
        tentacles=list(testrun.tentacles),
    )
    logger.info(f"TEST BEGIN {duration_text()} {testid}")

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
    testid: str,
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
            testid=testid,
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
        msg = f"{testid}: Terminating test due to: {e!r}"
        logger.warning(msg)
        skipped = isinstance(e, OctoprobeTestSkipException)
        report_test.write_error(msg=msg, skipped=skipped)
        return False
    except Exception as e:
        msg = f"{testid}: Terminating test due to: {e!r}"
        logger.error(msg, exc_info=e)
        report_test.write_error(msg=msg)
        return False
    finally:
        logger.info(f"TEST TEARDOWN {duration_text()} {testid}")
        try:
            ctxtestrun.function_teardown(active_tentacles=testrun.tentacles)
        except Exception as e:
            logger.exception(e)
        logger.info(f"TEST END {duration_text()} {testid}")


def target_run_one_test_async(
    arg1: util_multiprocessing.TargetArg1,
    args: Args,
    ctxtestrun: CtxTestRun,
    testrun: TestRun,
    repo_micropython_tests: pathlib.Path,
) -> None:
    logfile = pathlib.Path("/here_is_the_logfile")
    success = False
    testid = testrun.testid
    try:
        arg1.initfunc(arg1=arg1)

        testresults_directory = ResultsDir(
            directory_top=args.directory_results,
            test_name=testid,
            test_nodeid=testid,
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
                testid=testid,
            )
    finally:
        # We have to send a exit event before returing!
        arg1.queue_put(
            EventExitRunOneTest(
                arg1.target_unique_name,
                success=success,
                logfile=logfile,
                testid=testid,
            )
        )
