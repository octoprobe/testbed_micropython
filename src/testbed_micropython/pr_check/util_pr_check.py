import logging
import shutil

from octoprobe import util_cached_git_repo

from .. import constants
from . import util_github, util_ports_from_pr

logger = logging.getLogger(__file__)


def pr_check(
    git_ref: str,
    json_pr_ports: util_github.JsonPrPorts,
) -> util_github.JsonPrPorts:
    """
    Example git_ref: https://github.com/micropython/micropython.git~17782

    json_pr_ports: The query result we get from 'get pr view'.
    """

    # Clone git repo
    git_repo = util_cached_git_repo.CachedGitRepo(
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
    return json_pr_ports
