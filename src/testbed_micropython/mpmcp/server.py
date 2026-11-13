"""
MCP server for testbed_micropython.

Uses the official MCP python sdk (mcp>=2), where 'FastMCP' was renamed to 'MCPServer'.

Example configuration for Claude Code (.mcp.json):

    {
      "mcpServers": {
        "testbed_micropython": {
          "command": "mpmcp"
        }
      }
    }
"""

from __future__ import annotations

import contextlib
import pathlib
import typing

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from testbed_micropython import __version__

from . import util_mcp_tentacles
from .util_mcp_logging import mcp_init_logging

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
    instructions="""\
Octoprobe HIL (hardware in the loop) testbed for MicroPython. Documentation: https://www.octoprobe.org

A tentacle is a PCB which hosts a MicroPython board (the DUT: device under test).
The infrastructure side of the tentacle (PICO_INFRA, a RP2040) controls the switches of the tentacle:
* 'dut': USB power of the DUT. When powered, the DUT typically provides a serial port like /dev/ttyACM4.
* 'infra', 'infraboot': Power and boot button of PICO_INFRA.
* 'proberun', 'probeboot': Run and boot button of PICO_PROBE (tentacle >= v0.6).
* 'led_error', 'led_active': LEDs.
* 'relay1'..'relay7': Relays connecting the DUT to the octobus/gadgets.

A tentacle is identified by its serial, for example 'de6528b3cb38-5f33'. A unique suffix like '5f33' is accepted too.
Use 'query_tentacles' to find the connected tentacles and the serial port of their DUT.
""",
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

    poweron: If PICO_INFRA of a tentacle is unpowered, the tentacle is not found.
    poweron=True powers PICO_INFRA on ALL tentacles before querying.

    This corresponds to 'mptest list-tentacles'.
    """
    with _tool_errors():
        return util_mcp_tentacles.mcp_list_tentacles(poweron=poweron)
        # x = util_mcp_tentacles.mcp_list_tentacles(poweron=poweron)
        # return util_mcp_tentacles.dataclasses_to_json(x)


@mcp.tool()
def build_and_flash(
    serial: str,
    firmware_build: str,
    log_folder: pathlib.Path,
    board_variant: str = "",
) -> util_mcp_tentacles.McpBuildFlashResult:
    """
    Build a firmware and flash it to a tentacle.

    This corresponds to 'mptest mcp_build_andflash'.

    serial: The serial number of the tentacle. Might be short or long form ('4721' or 'e4641448133b-4721')."
    firmware_build: Directory of MicroPython-Repo to build the firmware from. Example: ~/micropython or  https://github.com/micropython/micropython.git@v1.24.1
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
    mcp_init_logging(directory_logs=DIRECTORY_OF_THIS_FILE)
    mcp.run(request_timeout=300)  # 5 minutes in seconds
    # mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
