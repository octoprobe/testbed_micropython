import logging
import pathlib

logger = logging.getLogger(__file__)

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent


PYTEST_OPT_GIT_MICROPYTHON_TESTS = "--git-micropython-tests"
DEFAULT_GIT_MICROPYTHON_TESTS = "https://github.com/micropython/micropython.git@master"

PYTEST_OPT_DIR_MICROPYTHON_TESTS = "--dir-micropython-tests"
