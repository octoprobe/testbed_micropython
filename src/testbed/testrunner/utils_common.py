"""
These methods may be used by
testbed_showcase and testbed_micropython
"""

import dataclasses
import pathlib
from testbed.util_firmware_mpbuild import CachedGitRepo
from tests.micropython_repo.test_run import un_monkey_patch


@dataclasses.dataclass
class ArgsMpTest:
    micropython_tests_git: str | None
    micropython_tests: str | None

    def clone_git_micropython_tests(
        self, directory_git_cache: pathlib.Path
    ) -> pathlib.Path:
        """
        We have to clone the micropython git repo and use the tests from the subfolder "test".
        """
        if self.micropython_tests is not None:
            _directory = pathlib.Path(self.micropython_tests).expanduser().resolve()
            if not _directory.is_dir():
                raise ValueError(
                    f"parameter '{self.micropython_tests}': Directory does not exist: {_directory}"
                )
            return _directory

        if self.micropython_tests_git is None:
            raise ValueError(
                "MicroPython repo not cloned - argument '{PYTEST_OPT_GIT_MICROPYTHON_TESTS}'not given to pytest !"
            )

        git_repo = CachedGitRepo(
            directory_cache=directory_git_cache,
            git_spec=self.micropython_tests_git,
            prefix="micropython_tests_",
        )
        git_repo.clone()

        # Avoid hanger in run-perfbench.py/run-tests.py
        un_monkey_patch()

        return git_repo.directory
