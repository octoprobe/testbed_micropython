"""
Logging for the MCP server.

Derived from 'octoprobe.scripts.commissioning.init_logging()'.

Difference: The MCP stdio transport uses stdout for JSON-RPC messages.
Anything else written to stdout corrupts the protocol.
Therefore all logging goes to stderr.
"""

from __future__ import annotations

import logging.config
import pathlib

from . import util_mcp_constants


class Global:
    filename_log: pathlib.Path | None = None


_GLOBAL = Global()


def get_filename_log() -> pathlib.Path:
    assert _GLOBAL.filename_log is not None
    return _GLOBAL.filename_log


def mcp_init_logging(directory_logs: pathlib.Path) -> None:
    filename_log = directory_logs / util_mcp_constants.FILENAME_MPMCP_LOG
    filename_log.unlink(missing_ok=True)

    _GLOBAL.filename_log = filename_log

    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "simple": {
                "format": "%(levelname)-8s - %(message)s",
            },
        },
        "handlers": {
            "stderr": {
                "class": "logging.StreamHandler",
                "level": "DEBUG",
                "formatter": "simple",
                "stream": "ext://sys.stderr",
            },
            "filename_log": {
                "class": "logging.FileHandler",
                "level": "INFO",
                "formatter": "simple",
                "filename": str(filename_log),
            },
        },
        "root": {
            "level": "INFO",
            "handlers": ["stderr", "filename_log"],
        },
    }
    logging.config.dictConfig(logging_config)
