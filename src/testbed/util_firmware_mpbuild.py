import logging
import os
import pathlib

from mpbuild.board_database import Database
from mpbuild.build_api import build_by_variant_normalized
from octoprobe.lib_tentacle import Tentacle
from octoprobe.util_cached_git_repo import CachedGitRepo
from octoprobe.util_dut_programmers import FirmwareBuildSpec, FirmwareSpecBase
from octoprobe.util_micropython_boards import BoardVariant

from testbed.constants import DIRECTORY_GIT_CACHE
from testbed.testcollection.baseclasses_spec import tentacle_spec_2_variants

logger = logging.getLogger(__file__)

_ENV_MICROPY_DIR = "MICROPY_DIR"


class FirmwareBuilder:
    """
    It is difficult in pytest to keep track if git has
    already been cloned and if a firmware alread
    has been compiled.
    This class will build every variant only once, even if
    many tests might require it.
    """

    def __init__(self, firmware_git_url: str) -> None:
        self._already_build_firmwares: dict[str, FirmwareBuildSpec] = {}
        self.firmware_git_url = firmware_git_url
        self.git_repo = CachedGitRepo(
            directory_cache=DIRECTORY_GIT_CACHE,
            git_spec=firmware_git_url,
            prefix="micropython_firmware_",
        )
        self.git_repo.clone()

    def build(
        self,
        firmware_spec: FirmwareSpecBase,
        testresults_mpbuild: pathlib.Path,
    ) -> FirmwareBuildSpec:
        assert isinstance(firmware_spec, FirmwareBuildSpec)

        variant = firmware_spec.board_variant

        firmware_build_spec = self._already_build_firmwares.get(
            variant.name_normalized, None
        )
        if firmware_build_spec is None:
            firmware_build_spec = build(
                micropython_directory=self.git_repo.directory,
                variant=variant,
                testresults_mpbuild=testresults_mpbuild,
            )
        self._already_build_firmwares[variant.name_normalized] = firmware_build_spec
        return firmware_build_spec


def build(
    micropython_directory: pathlib.Path,
    variant: BoardVariant,
    testresults_mpbuild: pathlib.Path,
) -> FirmwareBuildSpec:
    """
    This will compile the firmware

    Input: The git repo containing the micropython source
    Output: The filename of the compiled firmware.
    """
    assert isinstance(micropython_directory, pathlib.Path)
    assert isinstance(variant, BoardVariant)
    assert isinstance(testresults_mpbuild, pathlib.Path)

    # Prepare environment
    env_micropy_dir = os.environ.get(_ENV_MICROPY_DIR, None)
    if env_micropy_dir is not None:
        logger.error(
            f"The environment variable '{_ENV_MICROPY_DIR}' is defined: {env_micropy_dir}"
        )
        logger.error(
            "This variable is used by mpbuild. However octoprobe will DISABLE it."
        )
        del os.environ[_ENV_MICROPY_DIR]

    # Build results
    testresults_build = testresults_mpbuild / variant.name_normalized
    testresults_build.mkdir(parents=True, exist_ok=True)
    prefix = f"Firmware '{variant.name_normalized}'"
    logger.info(f"{prefix}: build in  {micropython_directory}")
    logger.info(f"{prefix}: output in {testresults_build}")

    # Call mpbuild
    db = Database(micropython_directory)
    firmware = build_by_variant_normalized(
        logfile=testresults_build / "docker_stdout.txt",
        db=db,
        variant_normalized=variant.name_normalized,
        do_clean=False,
    )

    # Store build results
    (testresults_build / firmware.filename.name).write_bytes(
        firmware.filename.read_bytes()
    )

    return FirmwareBuildSpec(
        board_variant=BoardVariant(
            board=firmware.board.name,
            variant="" if firmware.variant is None else firmware.variant,
        ),
        _filename=firmware.filename,
        micropython_version_text=firmware.micropython_version_text,
    )


def collect_firmware_specs(tentacles: list[Tentacle]) -> list[FirmwareSpecBase]:
    """
    Loops over all tentacles and finds
    the board variants that have to be
    build/downloaded.
    """
    set_variants: set[BoardVariant] = set()
    for tentacle in tentacles:
        if not tentacle.is_mcu:
            continue
        for variant in tentacle_spec_2_variants(tentacle.tentacle_spec):
            set_variants.add(
                BoardVariant(
                    board=tentacle.tentacle_spec.tentacle_tag.name,
                    variant=variant,
                )
            )
        # boards = tentacle.get_tag_mandatory(TAG_BOARDS)
        # for variant in board_variants(boards):
        #     set_variants.add(variant)
    list_variants = sorted(set_variants, key=lambda v: v.name_normalized)

    return [
        FirmwareBuildSpec(board_variant=variant, micropython_version_text=None)
        for variant in list_variants
    ]
