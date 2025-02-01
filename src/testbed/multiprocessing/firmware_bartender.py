from __future__ import annotations

import dataclasses
import logging
import pathlib
import time
import typing
from collections import defaultdict

from octoprobe.util_baseclasses import OctoprobeAppExitException
from octoprobe.util_constants import relative_cwd
from octoprobe.util_firmware_spec import FirmwareBuildSpec, FirmwaresBuilt
from octoprobe.util_micropython_boards import BoardVariant
from octoprobe.util_pytest import util_logging

from testbed import util_firmware_mpbuild
from testbed.mpbuild.build_api import MpbuildDockerException
from testbed.multiprocessing import util_multiprocessing
from testbed.testcollection.baseclasses_run import TestRunSpecs
from testbed.util_firmware_mpbuild import FirmwareSpecBase

logger = logging.getLogger(__file__)


@dataclasses.dataclass(repr=True)
class EventFirmwareSpec(util_multiprocessing.EventBase):
    firmware_spec: FirmwareBuildSpec
    start_s: float
    end_s: float
    logfile: pathlib.Path

    @property
    def duration_s(self) -> float:
        return self.end_s - self.start_s

    @property
    def duration_text(self) -> str:
        return f"{self.duration_s:0.1f}s"


@dataclasses.dataclass(repr=True)
class EventExitFirmware(util_multiprocessing.EventExit):
    pass


def target_build_firmware_async(
    arg1: util_multiprocessing.TargetArg1,
    directory_mpbuild_artifacts: pathlib.Path,
    firmwares: FirmwaresTobeBuilt,
    repo_micropython_firmware: pathlib.Path,
) -> None:
    assert isinstance(arg1, util_multiprocessing.TargetArg1)
    assert isinstance(directory_mpbuild_artifacts, pathlib.Path)
    assert isinstance(firmwares, FirmwaresTobeBuilt)
    assert isinstance(repo_micropython_firmware, pathlib.Path)

    success = False
    logfile = pathlib.Path("/dummy_path")
    target_unique_name = arg1.target_unique_name
    try:
        arg1.initfunc(arg1=arg1)
        for firmware in firmwares:
            builder = util_firmware_mpbuild.Builder(
                variant=firmware.firmware_build_spec.board_variant,
                mpbuild_artifacts=directory_mpbuild_artifacts,
            )
            with util_logging.Logs(builder.mpbuild_artifacts) as logs:
                logfile = logs.filename
                target_unique_name = (
                    firmware.firmware_build_spec.board_variant.name_normalized
                )
                util_multiprocessing.EVENTLOGCALLBACK.log(
                    msg=f"Firmware build start. Logfile: {relative_cwd(builder.docker_logfile)}",
                    target_unique_name=target_unique_name,
                )

                start_s = time.monotonic()
                try:
                    spec = builder.build(
                        repo_micropython_firmware=repo_micropython_firmware
                    )
                except MpbuildDockerException as e:
                    # We log the exception in the local logger and do NOT
                    # send the exception to the main process: pickle will fail on some exceptions!
                    logger.error(f"{e!r}: See logfile: {builder.docker_logfile}")
                    raise e
                except Exception as e:
                    logger.exception(
                        f"{e!r}: See logfile: {builder.docker_logfile}", exc_info=e
                    )
                    raise e

                arg1.queue_put(
                    EventFirmwareSpec(
                        target_unique_name=spec.board_variant.name_normalized,
                        firmware_spec=spec,
                        start_s=start_s,
                        end_s=time.monotonic(),
                        logfile=builder.docker_logfile,
                    )
                )
        success = True

    except Exception:
        # We can not write to the logger anymore at this point
        pass

    arg1.queue_put(
        EventExitFirmware(
            target_unique_name=target_unique_name,
            success=success,
            logfile=logfile,
        )
    )


@dataclasses.dataclass
class FirmwareTobeBuilt:
    firmware_build_spec: util_firmware_mpbuild.FirmwareBuildSpec
    """
    Default variant: ""
    """
    priority: tuple[typing.Any, ...]


class FirmwaresTobeBuilt(list[FirmwareTobeBuilt]):
    @staticmethod
    def factory(testrun_specs: TestRunSpecs) -> FirmwaresTobeBuilt:
        """
        Example order:
            # The multivariant boards will require much time.
            # Compile them first!
            (0, -2, 'ESP8266_GENERIC', '')
            (0, -2, 'RPI_PICO2', '')

            # Now the ones with only the default variant
            (0, -1, 'RPI_PICO', '')

            # Finally the not default variants
            (1, -2, 'ESP8266_GENERIC', 'FLASH_512K')
            (1, -2, 'RPI_PICO2', 'RISCV')

        """
        assert isinstance(testrun_specs, TestRunSpecs)
        board_variants: dict[str, set[str]] = defaultdict(set)
        for testrun_spec in testrun_specs:
            for tsvs in testrun_spec.roles_tsvs_todo:
                for tsv in tsvs:
                    variants = board_variants[tsv.board]
                    variants.add(tsv.variant)

        firmwares = FirmwaresTobeBuilt()
        for board, variants in board_variants.items():
            for idx, variant in enumerate(sorted(variants)):
                firmwares.append(
                    FirmwareTobeBuilt(
                        firmware_build_spec=util_firmware_mpbuild.FirmwareBuildSpec(
                            board_variant=BoardVariant(board=board, variant=variant),
                        ),
                        priority=(idx, -len(variants), board, variant),
                    )
                )
        firmwares.sort(key=lambda y: y.priority)
        return firmwares


class FirmwareBartenderSkipFlash:
    def __init__(self) -> None:
        self.async_targets = util_multiprocessing.AsyncTargets[AsyncTargetFirmware]()
        self.get_by_event = self.async_targets.get_by_event

    @property
    def firmwares_built(self) -> set[str] | None:
        return None

    def firmware_built(self, firmware_build_spec: FirmwareBuildSpec) -> None:
        pass

    def build_firmwares(
        self,
        directory_mpbuild_artifacts: pathlib.Path,
        repo_micropython_firmware: pathlib.Path,
    ) -> AsyncTargetFirmware | None:
        return None

    def get_firmware_spec(self, board: str, variant: str) -> FirmwareSpecBase:
        #
        # Nothing was specified: We do not flash any firmware
        #
        from testbed.util_firmware_specs import FirmwareNoFlashingSpec

        return FirmwareNoFlashingSpec(
            board_variant=BoardVariant(board=board, variant=variant)
        )

        return FirmwareNoFlashingSpec.factory()

    def handle_timeouts(self) -> None:
        """
        There might be processes which reached the timeout.
        Kill them and update 'self.async_targets' and free resources (tentacles).
        """
        for async_target in self.async_targets.timeout_reached():
            raise OctoprobeAppExitException(
                f"{async_target.target_unique_name}: Timeout of {async_target.timeout_s:0.1f}s."
            )


class FirmwareBartender(FirmwareBartenderSkipFlash):
    def __init__(self, testrun_specs: TestRunSpecs) -> None:
        super().__init__()
        self._testrun_specs = testrun_specs
        self._firmwares_built = FirmwaresBuilt()

    @typing.override
    def firmware_built(self, firmware_build_spec: FirmwareBuildSpec) -> None:
        assert isinstance(firmware_build_spec, FirmwareBuildSpec)
        self._firmwares_built[firmware_build_spec.board_variant.name_normalized] = (
            firmware_build_spec
        )

    @typing.override
    def build_firmwares(
        self,
        directory_mpbuild_artifacts: pathlib.Path,
        repo_micropython_firmware: pathlib.Path,
    ) -> AsyncTargetFirmware | None:
        async_target = AsyncTargetFirmware(
            directory_mpbuild_artifacts=directory_mpbuild_artifacts,
            firmwares_build=FirmwaresTobeBuilt.factory(self._testrun_specs),
            repo_micropython_firmware=repo_micropython_firmware,
        )
        self.async_targets.append(async_target)
        return async_target

    @property
    @typing.override
    def firmwares_built(self) -> set[str] | None:
        return set(self._firmwares_built)

    @typing.override
    def get_firmware_spec(self, board: str, variant: str) -> FirmwareSpecBase:
        """
        Given: arguments to pytest, for example PYTEST_OPT_FIRMWARE.
        Now we create firmware specs.
        In case of PYTEST_OPT_FIRMWARE:
        The firmware has to be downloaded.
        In case of PYTEST_OPT_FIRMWARE-TODO:
        The firmware has to be compiled.
        If nothing is specified, we do not flash any firmware: Return None
        """
        assert isinstance(board, str)
        assert isinstance(variant, str)

        #
        # Collect firmware specs by connected tentacles
        #
        board_variant = BoardVariant.build_name_normalized(board=board, variant=variant)
        try:
            return self._firmwares_built[board_variant]
        except KeyError as e:
            raise ValueError(
                f"Programming error: Firmware not been built yet: {board_variant}"
            ) from e


FirmwareBartenderBase = FirmwareBartenderSkipFlash


class AsyncTargetFirmware(util_multiprocessing.AsyncTarget):
    def __init__(
        self,
        directory_mpbuild_artifacts: pathlib.Path,
        firmwares_build: FirmwaresTobeBuilt,
        repo_micropython_firmware: pathlib.Path,
    ) -> None:
        assert isinstance(directory_mpbuild_artifacts, pathlib.Path)
        assert isinstance(firmwares_build, FirmwaresTobeBuilt)
        assert isinstance(repo_micropython_firmware, pathlib.Path)

        super().__init__(
            target_unique_name="Firmware",
            tentacles=[],
            func=target_build_firmware_async,
            func_args=[
                directory_mpbuild_artifacts,
                firmwares_build,
                repo_micropython_firmware,
            ],
            timeout_s=25 * 60.0,
        )

        self.firmwares_build = firmwares_build
        self.repo_micropython_firmware = repo_micropython_firmware
