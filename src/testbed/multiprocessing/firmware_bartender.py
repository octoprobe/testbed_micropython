from __future__ import annotations

import dataclasses
import logging
import pathlib
import typing
from collections import defaultdict

from octoprobe.util_firmware_spec import FirmwareBuildSpec, FirmwaresBuilt
from octoprobe.util_pytest import util_logging

from testbed import constants, util_firmware_mpbuild
from testbed.multiprocessing import util_multiprocessing
from testbed.testcollection.baseclasses_run import TestRunSpecs
from testbed.util_firmware_mpbuild_interface import BoardVariant

logger = logging.getLogger(__file__)


def build_firmware_async(
    firmware: FirmwareTobeBuilt, repo_micropython_firmware: pathlib.Path
) -> util_firmware_mpbuild.FirmwareBuildSpec:
    assert isinstance(firmware, FirmwareTobeBuilt)
    assert isinstance(repo_micropython_firmware, pathlib.Path)

    builder = util_firmware_mpbuild.Builder(
        variant=firmware.firmware_build_spec.board_variant,
        mpbuild_artifacts=constants.DIRECTORY_MPBUILD_ARTIFACTS,
    )
    with util_logging.Logs(builder.mpbuild_artifacts):
        logger.info(
            f"Build {firmware.firmware_build_spec.board_variant.name_normalized}"
        )
        return builder.build(repo_micropython_firmware=repo_micropython_firmware)


@dataclasses.dataclass
class FirmwareTobeBuilt:
    board: str
    variant: str
    firmware_build_spec: util_firmware_mpbuild.FirmwareBuildSpec
    """
    Default variant: ""
    """
    priority: tuple[typing.Any, ...]


class FirmwaresToBeBuilt(list[FirmwareTobeBuilt]):
    @staticmethod
    def factory(testrun_specs: TestRunSpecs) -> FirmwaresToBeBuilt:
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
            for tsvs in testrun_spec.list_tsvs_todo:
                for tsv in tsvs:
                    variants = board_variants[tsv.board]
                    variants.add(tsv.variant)

        firmwares = FirmwaresToBeBuilt()
        for board, variants in board_variants.items():
            for idx, variant in enumerate(sorted(variants)):
                firmwares.append(
                    FirmwareTobeBuilt(
                        board=board,  # TODO: Remove
                        variant=variant,  # TODO: Remove
                        firmware_build_spec=util_firmware_mpbuild.FirmwareBuildSpec(
                            board_variant=BoardVariant(board=board, variant=variant),
                        ),
                        priority=(idx, -len(variants), board, variant),
                    )
                )
        firmwares.sort(key=lambda y: y.priority)
        return firmwares


class FirmwareBartender:
    def __init__(self, testrun_specs: TestRunSpecs) -> None:
        self.firmwares_tobe_built = FirmwaresToBeBuilt.factory(testrun_specs)
        self.firmwares_built = FirmwaresBuilt()
        self.build_in_progress: AsyncResultFirmware | None = None

    def testrun_next(
        self, repo_micropython_firmware: pathlib.Path
    ) -> AsyncResultFirmware | None:
        if self.build_in_progress is not None:
            return None
        if len(self.firmwares_tobe_built) == 0:
            return None
        firmware_build = self.firmwares_tobe_built.pop(0)
        assert isinstance(firmware_build, FirmwareTobeBuilt)
        async_result = AsyncResultFirmware(
            firmware_build=firmware_build,
            repo_micropython_firmware=repo_micropython_firmware,
        )
        self.build_in_progress = async_result
        return async_result

    def testrun_done(self, result: AsyncResultFirmware) -> None:
        assert isinstance(result, AsyncResultFirmware)
        assert self.build_in_progress is result
        self.firmwares_built[
            result.result_firmware_build_spec.board_variant.name_normalized
        ] = result.result_firmware_build_spec
        self.build_in_progress = None


class AsyncResultFirmware(util_multiprocessing.AsyncResult):
    def __init__(
        self,
        firmware_build: FirmwareTobeBuilt,
        repo_micropython_firmware: pathlib.Path,
    ) -> None:
        super().__init__(
            label=firmware_build.firmware_build_spec.board_variant.name_normalized,
            tentacles=[],
            func=build_firmware_async,
            func_args=[firmware_build, repo_micropython_firmware],
        )

        assert isinstance(firmware_build, FirmwareTobeBuilt)
        assert isinstance(repo_micropython_firmware, pathlib.Path)

        self.firmware_build = firmware_build
        self.repo_micropython_firmware = repo_micropython_firmware

    @property
    def result_firmware_build_spec(self) -> FirmwareBuildSpec:
        assert isinstance(self._result_value, FirmwareBuildSpec)
        return self._result_value

    def done(self, bartender: FirmwareBartender) -> None:
        assert isinstance(bartender, FirmwareBartender)
        bartender.testrun_done(result=self)
