import logging
import os
import pathlib
import typing

from mpbuild.board_database import Database
from octoprobe.util_cached_git_repo import CachedGitRepo
from octoprobe.util_firmware_spec import (
    FirmwareBuildSpec,
    FirmwareSpecBase,
)
from octoprobe.util_micropython_boards import BoardVariant

from .constants import is_url
from .mpbuild.build_api import build_by_variant_normalized
from .tentacle_spec import (
    TentacleMicropython,
    TentacleSpecMicropython,
)

logger = logging.getLogger(__file__)

_ENV_MICROPY_DIR = "MICROPY_DIR"


class FirmwareBuilderSkipFlash:
    def __init__(self) -> None:
        self.repo_directory = pathlib.Path("/placeholder_path")

    def build(
        self,
        firmware_spec: FirmwareSpecBase,
        mpbuild_artifacts: pathlib.Path,
    ) -> FirmwareBuildSpec:
        raise NotImplementedError()


class FirmwareBuilder(FirmwareBuilderSkipFlash):
    """
    It is difficult in pytest to keep track if git has
    already been cloned and if a firmware alread
    has been compiled.
    This class will build every variant only once, even if
    many tests might require it.
    """

    def __init__(
        self, firmware_git: str, directory_git_cache: pathlib.Path, git_clean: bool
    ) -> None:
        super().__init__()
        assert isinstance(firmware_git, str)
        assert isinstance(directory_git_cache, pathlib.Path)
        assert isinstance(git_clean, bool)

        self._already_build_firmwares: dict[str, FirmwareBuildSpec] = {}
        """
        Key: board_variant.name_normalized
        """

        if is_url(firmware_git):
            self.firmware_git = firmware_git
            self.git_repo = CachedGitRepo(
                directory_cache=directory_git_cache,
                git_spec=firmware_git,
                prefix="firmware-build_",
            )
            self.git_repo.clone(git_clean=git_clean)
            self.repo_directory = self.git_repo.directory_git_worktree

        else:
            self.repo_directory = pathlib.Path(firmware_git).expanduser().resolve()

        Database.assert_mpy_root_direcory(self.repo_directory)

    @typing.override
    def build(
        self,
        firmware_spec: FirmwareSpecBase,
        mpbuild_artifacts: pathlib.Path,
    ) -> FirmwareBuildSpec:
        assert isinstance(firmware_spec, FirmwareBuildSpec)

        variant = firmware_spec.board_variant

        firmware_build_spec = self._already_build_firmwares.get(
            variant.name_normalized, None
        )
        if firmware_build_spec is None:
            builder = Builder(variant=variant, mpbuild_artifacts=mpbuild_artifacts)
            firmware_build_spec = builder.build(
                repo_micropython_firmware=self.repo_directory
            )
        self._already_build_firmwares[variant.name_normalized] = firmware_build_spec
        return firmware_build_spec


FirmwareBuilderBase = FirmwareBuilderSkipFlash


class Builder:
    def __init__(
        self,
        variant: BoardVariant,
        mpbuild_artifacts: pathlib.Path,
    ) -> None:
        assert isinstance(variant, BoardVariant)
        assert isinstance(mpbuild_artifacts, pathlib.Path)
        self.variant = variant
        self.mpbuild_artifacts = mpbuild_artifacts / self.variant.name_normalized
        self.mpbuild_artifacts.mkdir(parents=True, exist_ok=True)

    @property
    def docker_logfile(self) -> pathlib.Path:
        return self.mpbuild_artifacts / "docker_stdout.txt"

    def build(self, repo_micropython_firmware: pathlib.Path) -> FirmwareBuildSpec:
        """
        This will compile the firmware

        Input: The git repo containing the micropython source
        Output: The filename of the compiled firmware.
        """
        assert isinstance(repo_micropython_firmware, pathlib.Path)

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
        prefix = f"Firmware '{self.variant.name_normalized}'"
        logger.info(f"{prefix}: source:  {repo_micropython_firmware}")
        logger.info(f"{prefix}: docker output: {self.docker_logfile}")

        # Call mpbuild
        db = Database(repo_micropython_firmware)
        firmware = build_by_variant_normalized(
            logfile=self.docker_logfile,
            db=db,
            variant_normalized=self.variant.name_normalized,
            do_clean=False,
        )

        # Store build results
        filename = self.mpbuild_artifacts / firmware.filename.name
        filename.write_bytes(firmware.filename.read_bytes())

        spec = FirmwareBuildSpec(
            board_variant=BoardVariant(
                board=firmware.board.name,
                variant="" if firmware.variant is None else firmware.variant,
            ),
            _filename=firmware.filename,
            micropython_full_version_text=firmware.micropython_full_version_text,
        )

        filename.with_suffix(".spec").write_text(spec.text)

        return spec


def collect_firmware_specs(
    tentacles: list[TentacleMicropython],
) -> list[FirmwareSpecBase]:
    """
    Loops over all tentacles and finds
    the board variants that have to be
    build/downloaded.
    """
    set_variants: set[BoardVariant] = set()
    for tentacle in tentacles:
        if not tentacle.is_mcu:
            continue
        tentacle_spec = tentacle.tentacle_spec
        assert isinstance(tentacle_spec, TentacleSpecMicropython)
        for variant in tentacle_spec.build_variants:
            set_variants.add(
                BoardVariant(
                    board=tentacle.tentacle_spec.tentacle_tag,
                    variant=variant,
                )
            )
        # boards = tentacle.get_tag_mandatory(TAG_BOARDS)
        # for variant in board_variants(boards):
        #     set_variants.add(variant)
    list_variants = sorted(set_variants, key=lambda v: v.name_normalized)

    return [FirmwareBuildSpec(board_variant=variant) for variant in list_variants]
