from __future__ import annotations

import importlib
import logging
import os
import pathlib

from octoprobe.lib_testbed import Testbed

logger = logging.getLogger(__file__)

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent
ENV_TESTBED = "OCTOPROBE_TESTBED"
TESTBED_FALLBACK = "testbed_ch_wetzikon_1.py"


def get_testbed() -> Testbed:
    python_testbed = os.environ.get(ENV_TESTBED)
    if python_testbed is None:
        python_testbed = TESTBED_FALLBACK
        logger.info(
            f"No environment '{ENV_TESTBED}' defined: Fallback to: {python_testbed}"
        )

    module_name = python_testbed.replace(".py", "")
    module_name = f"testbed.{module_name}"
    module = importlib.import_module(name=module_name)
    return module.TESTBED
