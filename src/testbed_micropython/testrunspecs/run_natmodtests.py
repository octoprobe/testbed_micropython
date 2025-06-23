from __future__ import annotations

import dataclasses
import logging
import os
import pathlib
import shutil
import sys

from octoprobe.util_cached_git_repo import CachedGitRepo
from octoprobe.util_constants import relative_cwd
from octoprobe.util_subprocess import SubprocessExitCodeException, subprocess_run

from testbed_micropython import constants

from ..constants import EnumFut
from ..mptest import util_common
from ..multiprocessing.util_multiprocessing import EVENTLOGCALLBACK
from ..testcollection.baseclasses_spec import TentacleVariant
from ..testcollection.testrun_specs import (
    TIMEOUT_FLASH_S,
    TestArgs,
    TestRun,
    TestRunSpec,
)

logger = logging.getLogger(__file__)

# bree: git submodule update --init lib/berkeley-db-1.xx
NATMOD_LIBS = ("btree", "deflate", "framebuf", "heapq", "random", "re")


@dataclasses.dataclass(frozen=True)
class Arch:
    arch: str
    container: str
    extra_args: str = ""
    pyelftools_patch: bool = True


# Container names have been copied from: mpbuild/build.py
ARM_BUILD_CONTAINER = "micropython/build-micropython-arm:bookworm"
# ARM_BUILD_CONTAINER = "micropython/build-micropython-arm"
ARCHS = [
    Arch(
        arch="armv6m",
        container=ARM_BUILD_CONTAINER,
        extra_args="LINK_RUNTIME=1",
    ),
    Arch(
        arch="armv7m",
        container=ARM_BUILD_CONTAINER,
    ),
    Arch(
        arch="armv7emsp",
        container=ARM_BUILD_CONTAINER,
    ),
    Arch(
        arch="armv7emdp",
        container=ARM_BUILD_CONTAINER,
    ),
    Arch(
        arch="rv32imc",
        container="micropython/build-micropython-rp2350riscv",
        extra_args="CROSS=riscv32-unknown-elf-",
    ),
    Arch(
        arch="xtensa",
        container="larsks/esp-open-sdk",
    ),
    Arch(
        arch="xtensawin",
        container="espressif/idf:v5.4.1",
    ),
]


class NatmodContainers:
    """
    The containers are missing some python libraries.
    We clone the missing libraries and add then to PYTHONPATH
    """

    PYLIBS = [
        ("pyelftools", "https://github.com/eliben/pyelftools.git@v0.32"),
        ("ar", "https://github.com/vidstige/ar.git@v1.0.0"),
    ]
    GIT_CACHE_SUBDIR = "natmodtests_pylibs"
    DIRECTORY_PYLIBS = constants.DIRECTORY_GIT_CACHE / GIT_CACHE_SUBDIR

    def __init__(self) -> None:
        self.clones_repos: dict[str, pathlib.Path] = {}
        "We remember the repos which have already been clones."

    def clone_python_libs(self) -> None:
        shutil.rmtree(self.DIRECTORY_PYLIBS, ignore_errors=True)
        for pylib, pylib_git_spec in self.PYLIBS:
            git_repo = CachedGitRepo(
                directory_cache=constants.DIRECTORY_GIT_CACHE,
                git_spec=pylib_git_spec,
                subdir=self.GIT_CACHE_SUBDIR,
                prefix="",
            )
            if pylib in self.clones_repos:
                continue
            git_repo.clone(git_clean=False)
            self.clones_repos[pylib] = git_repo.directory_git_work_repo

        for example, directory_repo in self.clones_repos.items():
            assert directory_repo.parent == self.DIRECTORY_PYLIBS, (
                example,
                directory_repo,
            )

    @property
    def docker_args_ext(self) -> list[str]:
        pythonpath = ":".join(str(d) for d in self.clones_repos.values())

        return [
            f"--volume={natmod_containers.DIRECTORY_PYLIBS}:{natmod_containers.DIRECTORY_PYLIBS}",
            f"--env=PYTHONPATH={pythonpath}",
        ]


natmod_containers = NatmodContainers()


class NatmodExamples:
    def __init__(self) -> None:
        self.compiled = False

    def compile_all(
        self,
        repo_micropython_tests: pathlib.Path,
        directory_mpbuild_artifacts: pathlib.Path,
    ) -> None:
        if self.compiled:
            return
        self.compiled = True
        natmod_containers.clone_python_libs()
        directory_natmodtests = directory_mpbuild_artifacts / "compile_natmodtests"

        logfile = directory_natmodtests / "submodule_checkout.txt"
        args = [
            "git",
            "submodule",
            "update",
            "--init",
            "lib/berkeley-db-1.xx",
        ]
        subprocess_run(
            args=args,
            cwd=repo_micropython_tests,
            logfile=logfile,
            timeout_s=300.0,
        )

        for example in NATMOD_LIBS:
            for arch in ARCHS:
                args_extra: list[str] = []
                opt_extra = ""
                if arch.pyelftools_patch:
                    args_extra = natmod_containers.docker_args_ext

                arg_trace = "--trace"
                arg_trace = ""
                args = [
                    "/usr/bin/docker",
                    "run",
                    "--rm",
                    f"--volume={repo_micropython_tests}:{repo_micropython_tests}",
                    *args_extra,
                    f"--user={os.getuid()}:{os.getgid()}",
                    arch.container,
                    "bash",
                    "-c",
                    f"{opt_extra} make {arg_trace} --always-make -C {repo_micropython_tests}/examples/natmod/{example} ARCH={arch.arch} {arch.extra_args}",
                ]
                logfile = (
                    directory_natmodtests / f"natmodtest-{arch.arch}-{example}.txt"
                )
                logger.info(
                    f"compile '{example}' for '{arch.arch}'. Logfile: {logfile}"
                )

                try:
                    subprocess_run(
                        args=args,
                        cwd=repo_micropython_tests,
                        logfile=logfile,
                        timeout_s=300.0,
                    )
                except SubprocessExitCodeException as e:
                    logger.error(f"compile '{example}' for '{arch.arch}' failed: {e}")

                shutil.rmtree(
                    repo_micropython_tests / example / "build", ignore_errors=True
                )


NATMOD_EXAMPLES = NatmodExamples()


class TestRunRunTests(TestRun):
    """
    This tests runs: run-natmodtests.py

    https://github.com/micropython/micropython/blob/master/tests/README.md
    https://github.com/micropython/micropython/blob/master/tests/run-natmodtests.py
    """

    def test(self, testargs: TestArgs) -> None:
        assert len(self.list_tentacle_variant) == 1
        tentacle_variant = self.list_tentacle_variant[0]
        assert isinstance(tentacle_variant, TentacleVariant)
        tentacle = tentacle_variant.tentacle
        tentacle_spec = tentacle.tentacle_spec
        assert tentacle_spec.mcu_config is not None

        # Work out which tests can be run.
        tests_extmod_dir = testargs.repo_micropython_tests / "tests" / "extmod"
        tests_natmod = [
            f"extmod/{file.name}"
            for file in tests_extmod_dir.glob("*.py")
            if file.stem.startswith(NATMOD_LIBS)
        ]

        # Run tests
        serial_port = tentacle.dut.get_tty()
        logfile = testargs.testresults_directory("testresults.txt").filename
        EVENTLOGCALLBACK.log(msg=f"Logfile: {relative_cwd(logfile)}")
        args = [
            sys.executable,
            *self.testrun_spec.command,
            f"--result-dir={testargs.testresults_directory.directory_test}",
            "--pyboard",
            f"--device={serial_port}",
        ] + tests_natmod
        subprocess_run(
            args=args,
            cwd=testargs.repo_micropython_tests / "tests",
            env=util_common.ENV_PYTHONUNBUFFERED,
            logfile=logfile,
            timeout_s=self.timeout_s,
            # TODO: Remove the following line as soon returncode of 'run-natmodtests.py' is fixed.
            success_returncodes=[0, 1],
        )


TESTRUNSPEC_RUN_NATMODTESTS = TestRunSpec(
    label="RUN-NATMODTESTS",
    helptext="Run tests using native modules in external .mpy files",
    command=["run-natmodtests.py"],
    required_fut=EnumFut.FUT_MCU_ONLY,
    required_tentacles_count=1,
    testrun_class=TestRunRunTests,
    timeout_s=2 * 60.0 + TIMEOUT_FLASH_S,
)
