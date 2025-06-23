"""
Some tests require mpbuild.

Directories and paths:
 * testresults/mpy-cross: The binary to be used by the tests.
 * repo_micropython_firmware/mpy-cross/build/mpy-cross: This binary will created by mpbuild
   and copied to testresults/mpy-cross.
 * repo_micropython_test/mpy-cross/build/mpy-cross: This binary will build if mpbuild was never called
   and copied to testresults/mpy-cross.

Sideeffects:
 * mpbuild builds mpy-cross too.
 * As mpbuild will be called multiple times, mpy-cross will be overwritten.

Solution:
 * We copy mpy-cross after mpbuild finished. But just the first time.
 * If '--flash-skip' is used:
   * mpbuild will not be called.
   * In this case, mpbuild will be build.

Enhancements
 * The build system must be installed. However, any mpbuild docker container may be used.
"""

from __future__ import annotations

import logging
import pathlib
import shutil

from octoprobe.util_subprocess import subprocess_run

logger = logging.getLogger(__file__)

FILENAME_MPCROSS = "mpy-cross"
_DIRECTORY_MPCROSS = "mpy-cross"
BUILD_DIRECTORY_MPCROSS = _DIRECTORY_MPCROSS
BUILD_FILENAME_MPCROSS = f"{_DIRECTORY_MPCROSS}/build/{FILENAME_MPCROSS}"


def copy_mpycross(
    repo_micropython: pathlib.Path,
    directory_mpbuild_artifacts: pathlib.Path,
) -> None:
    """
    After a firmware has been built, mpy_cross will be copied away.
    """
    filename = directory_mpbuild_artifacts / FILENAME_MPCROSS
    if filename.is_file():
        # We already have a version of mp-cross
        return

    # We copy mpy-cross from the repo into the artifacts directory
    build_filename = repo_micropython / BUILD_FILENAME_MPCROSS
    assert build_filename.is_file(), build_filename
    logger.info(f"cp {build_filename} {directory_mpbuild_artifacts}")
    shutil.copy(build_filename, directory_mpbuild_artifacts)
    assert filename.is_file(), filename


def get_filename_mpycross(
    directory_mpbuild_artifacts: pathlib.Path,
    repo_micropython: pathlib.Path,
) -> pathlib.Path:
    """
    If there is already a artifacts/mpy-cross return it.
    Else: compile it.
    """
    filename = directory_mpbuild_artifacts / FILENAME_MPCROSS
    if filename.is_file():
        return filename

    _compile_mpycross(
        directory_mpbuild_artifacts=directory_mpbuild_artifacts,
        repo_micropython=repo_micropython,
        filename=filename,
    )
    assert filename.is_file(), filename
    return filename


def _compile_mpycross(
    directory_mpbuild_artifacts: pathlib.Path,
    repo_micropython: pathlib.Path,
    filename: pathlib.Path,
) -> None:
    logfile = directory_mpbuild_artifacts / f"{FILENAME_MPCROSS}_make.txt"
    subprocess_run(
        args=["make", "-j", "8"],
        cwd=repo_micropython / BUILD_DIRECTORY_MPCROSS,
        logfile=logfile,
        timeout_s=60.0,
    )
    filename_build = repo_micropython / BUILD_FILENAME_MPCROSS
    assert filename_build.is_file(), filename_build
    shutil.copy(filename_build, filename)
