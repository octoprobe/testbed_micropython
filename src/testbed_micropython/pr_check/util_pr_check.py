from __future__ import annotations

import dataclasses
import logging
import shutil

from git_cached_repo import git_cached_repo

from .. import constants
from . import util_github, util_ports_from_pr

logger = logging.getLogger(__file__)


@dataclasses.dataclass(slots=True)
class PrCheck:
    json_pr_ports: util_github.JsonPrPorts
    lines: list[str] = dataclasses.field(default_factory=list)
    test_required: bool = True

    @property
    def return_code(self) -> int:
        return 1 if self.test_required else 0

    @property
    def return_text(self) -> str:
        return "test required" if self.test_required else "already tested"

    @staticmethod
    def factory(git_ref: str) -> PrCheck:
        """
        * Read PR comments
        * Check out micropython repo
        * if
        """
        # Call 'gh'
        json_pr_ports = util_github.gh_read_pr(git_ref=git_ref)
        p = PrCheck(json_pr_ports=json_pr_ports)

        commit_hash_tested = p.json_pr_ports.commit_hash_tested

        p.lines.append(
            f"{git_ref} is on commit '{p.json_pr_ports.commit_hash}'. The last tested version was '{commit_hash_tested}'."
        )
        pr_check(json_pr_ports=p.json_pr_ports, git_ref=git_ref)
        p.lines.append(
            f"MicroPython ports to be tested: {', '.join(p.json_pr_ports.ports)}"
        )
        p.lines.append("========================================")
        if commit_hash_tested == p.json_pr_ports.commit_hash:
            p.lines.append(
                f"{git_ref} is on commit '{p.json_pr_ports.commit_hash}'. This commit was already tested."
            )
            p.lines.append("!!!!!!!! We may skip testing this PR !!!!!!!!")
            p.test_required = False
            return p
        p.lines.append("!!!!!!!! We have to run tests on this PR  !!!!!!!!")
        p.test_required = True
        return p


def pr_check(
    git_ref: str,
    json_pr_ports: util_github.JsonPrPorts,
) -> None:
    """
    Example git_ref: https://github.com/micropython/micropython.git~17782

    json_pr_ports: The query result we get from 'get pr view'.

    Adds an entry for the MicroPython ports to be tested.
    """

    # Clone git repo
    git_repo = git_cached_repo.CachedGitRepo(
        directory_cache=constants.DIRECTORY_GIT_CACHE,
        git_spec=git_ref,
        prefix="pr_check_",
    )
    shutil.rmtree(git_repo.directory_git_work_repo, ignore_errors=True)
    git_repo.clone(git_clean=False)

    directory_micropython_repo = git_repo.directory_git_work_repo

    # Ports from files
    yfs = util_ports_from_pr.YamlFiles.factory(
        directory_micropython_repo / ".github/workflows"
    )
    list_ports = yfs.micropython_ports(files_modified=json_pr_ports.files_modified)
    json_pr_ports.ports = list_ports
