from __future__ import annotations

import os
import pathlib

ENV_MPMCP_LOGS = "MPMCP_LOGS"
try:
    DIRECTORY_MPMCP_LOGS = pathlib.Path(os.environ[ENV_MPMCP_LOGS])
except KeyError:
    DIRECTORY_MPMCP_LOGS = pathlib.Path.home() / "octoprobe_mpmcp/logs"
DIRECTORY_MPMCP_LOGS.mkdir(parents=True, exist_ok=True)
assert DIRECTORY_MPMCP_LOGS.is_dir()

FILENAME_MPMCP_LOG = "mpmcp_log.txt"
