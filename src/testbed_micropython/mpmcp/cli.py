from __future__ import annotations

import logging
import pathlib
import typing

import typer

from . import util_mcp_constants, util_mcp_logging, util_mcp_tentacles

logger = logging.getLogger(__name__)

app = typer.Typer(pretty_exceptions_enable=False)


@app.command(help="List connected tentacles")
def list_tentacles(
    log_folder: typing.Annotated[
        pathlib.Path,
        typer.Option(
            help="The directory to store the build and flash logfiles",
        ),
    ] = util_mcp_constants.DIRECTORY_MPMCP_LOGS,
) -> None:
    util_mcp_logging.mcp_init_logging(directory_logs=log_folder)

    mscp_result = util_mcp_tentacles.mcp_list_tentacles(poweron=False)
    json_text = util_mcp_tentacles.dataclasses_to_json(mscp_result)
    print(json_text)


@app.command(help="Powercycle the DUT of the given tentacle")
def powercycle_dut(
    serial: typing.Annotated[
        str,
        typer.Option(
            help="The serial number of the tentacle. Might be short or long form ('4721' or 'e4641448133b-4721').",
        ),
    ],
    log_folder: typing.Annotated[
        pathlib.Path,
        typer.Option(
            help="The directory to store the build and flash logfiles",
        ),
    ] = util_mcp_constants.DIRECTORY_MPMCP_LOGS,
) -> None:
    util_mcp_logging.mcp_init_logging(directory_logs=log_folder)

    mscp_result = util_mcp_tentacles.mcp_powercycle_dut(serial=serial)
    json_text = util_mcp_tentacles.dataclasses_to_json(mscp_result)
    print(json_text)


@app.command(help="Flashes all tentacles without running any tests")
def flash_tentacle(
    serial: typing.Annotated[
        str,
        typer.Option(
            help="The serial number of the tentacle. Might be short or long form ('4721' or 'e4641448133b-4721').",
        ),
    ],
    firmware_build: typing.Annotated[
        str,
        typer.Option(
            envvar="TESTBED_MICROPYTHON_FIRMWARE_BUILD",
            help="Directory of MicroPython-Repo to build the firmware from. Example: ~/micropython or  https://github.com/micropython/micropython.git@v1.24.1",
        ),
    ],
    log_folder: typing.Annotated[
        pathlib.Path,
        typer.Option(
            help="The directory to store the build and flash logfiles",
        ),
    ] = util_mcp_constants.DIRECTORY_MPMCP_LOGS,
    board_variant: typing.Annotated[
        str,
        typer.Option(
            help="The board variant to build.",
        ),
    ] = "",
) -> None:
    util_mcp_logging.mcp_init_logging(directory_logs=log_folder)

    mscp_result = util_mcp_tentacles.mcp_build_and_flash(
        serial=serial,
        firmware_build=firmware_build,
        log_folder=log_folder,
        board_variant=board_variant,
    )
    json_text = util_mcp_tentacles.dataclasses_to_json(mscp_result)
    print(json_text)


if __name__ == "__main__":
    app()
