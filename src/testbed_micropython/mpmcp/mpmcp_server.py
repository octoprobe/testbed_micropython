"""
MCP server for testbed_micropython.

Uses the official MCP python sdk (mcp>=2), where 'FastMCP' was renamed to 'MCPServer'.

Example configuration for Claude Code (.mcp.json):

"mpmcp_server": {
    "command": "python",
    "args": [
        "-m",
        "testbed_micropython.mpmcp.mpmcp_server"
    ]
}
"""

from __future__ import annotations

import contextlib
import pathlib
import typing

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from testbed_micropython import __version__

from . import util_mcp_constants, util_mcp_logging, util_mcp_tentacles

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent


@contextlib.contextmanager
def _tool_errors() -> typing.Iterator[None]:
    """
    A ToolError reaches the model with its message.
    Any other exception is reported as a generic 'Error executing tool'.
    """
    try:
        yield
    except util_mcp_tentacles.McpSystemExit as e:
        raise ToolError(str(e)) from e


mcp = MCPServer(
    name="testbed_micropython",
    version=__version__,
    instructions=(DIRECTORY_OF_THIS_FILE / "instructions.md").read_text(),
)


@mcp.tool()
def get_version() -> str:
    """Return the version of testbed_micropython."""
    return __version__


@mcp.tool()
def list_tentacles(
    poweron: bool = False,
) -> list[util_mcp_tentacles.McpConnectedTentacle]:
    """
    List the tentacles connected via USB: Serial, board, USB locations,
    power state and the serial port of the DUT.

    This corresponds to 'mpmcp list_tentacles'.

    poweron: If PICO_INFRA of a tentacle is unpowered, the tentacle is not found.
    poweron=True powers PICO_INFRA on ALL tentacles before querying. Typically NOT required!

    This corresponds to 'mptest list-tentacles'.
    """
    with _tool_errors():
        return util_mcp_tentacles.mcp_list_tentacles(poweron=poweron)


@mcp.tool()
def build_and_flash(
    serial: str,
    firmware_build: str,
    log_folder: pathlib.Path = util_mcp_constants.DIRECTORY_MPMCP_LOGS
    / util_mcp_constants.FILENAME_MPMCP_LOG,
    board_variant: str = "",
) -> util_mcp_tentacles.McpBuildFlashResult:
    """
    Build a firmware and flash it to a tentacle.

    This corresponds to 'mpmcp build_andflash'.

    serial: The serial number of the tentacle. Might be short or long form ('4721' or 'e4641448133b-4721')."
    firmware_build: Directory of MicroPython-Repo to build the firmware from. Typically './micropython'.
    log_folder: The directory to store the build and flash logfiles
    board_variant: The board variant to build
    """
    with _tool_errors():
        return util_mcp_tentacles.mcp_build_and_flash(
            serial=serial,
            firmware_build=firmware_build,
            log_folder=log_folder,
            board_variant=board_variant,
        )


def main() -> None:
    util_mcp_logging.mcp_init_logging(
        # directory_logs=util_mcp_constants.DIRECTORY_MPMCP_LOGS
        directory_logs=pathlib.Path.cwd()
    )
    request_timeout = 300  # 5 minutes in seconds
    mcp.run(request_timeout=request_timeout)  # type: ignore[call-overload]

    # mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
