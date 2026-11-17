from __future__ import annotations

import logging
import pathlib
import shutil
import typing

import typer

from . import util_mcp_constants, util_mcp_logging, util_mcp_tentacles

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent
logger = logging.getLogger(__name__)

# 'typer' does not work correctly with typing.Annotated
# Required is: typing_extensions.Annotated
TyperAnnotated = typing.Annotated

app = typer.Typer(pretty_exceptions_enable=False)


@app.command(
    help="Populate an empty directory with the initial MCP configuration and skills"
)
def populate(
    directory: TyperAnnotated[
        pathlib.Path,
        typer.Argument(
            help="The directory to populate. Must be empty.",
        ),
    ] = ".",
) -> None:
    directory = directory.expanduser().resolve()

    if directory.exists():
        if list(directory.iterdir()):
            typer.echo(f"Error: Directory {directory} is not empty", err=True)
            raise typer.Exit(code=1)

    directory.mkdir(parents=True, exist_ok=True)

    prepopulate_dir = DIRECTORY_OF_THIS_FILE / "prepopulate"

    assert prepopulate_dir.exists(), str(prepopulate_dir)

    for item in prepopulate_dir.iterdir():
        if item.is_dir():
            shutil.copytree(item, directory / item.name, dirs_exist_ok=True)
        else:
            shutil.copy2(item, directory / item.name)

    typer.echo(f"Successfully populated {directory}")


@app.command(help="List connected tentacles")
def list_tentacles(
    log_folder: TyperAnnotated[
        pathlib.Path,
        typer.Option(
            help="The directory to store the build and flash logfiles",
        ),
    ] = util_mcp_constants.DIRECTORY_MPMCP_LOGS,
) -> None:
    util_mcp_logging.mcp_init_logging(directory_logs=log_folder)

    mscp_list_tentacles_result = util_mcp_tentacles.mcp_list_tentacles(poweron=False)
    json_text = util_mcp_tentacles.dataclasses_to_json(mscp_list_tentacles_result)
    print(json_text)


@app.command(help="Flashes all tentacles without running any tests")
def flash_tentacle(
    serial: TyperAnnotated[
        str,
        typer.Option(
            help="The serial number of the tentacle. Might be short or long form ('4721' or 'e4641448133b-4721').",
        ),
    ],
    firmware_build: TyperAnnotated[
        str,
        typer.Option(
            envvar="TESTBED_MICROPYTHON_FIRMWARE_BUILD",
            help="Directory of MicroPython-Repo to build the firmware from. Example: ~/micropython or  https://github.com/micropython/micropython.git@v1.24.1",
        ),
    ],
    log_folder: TyperAnnotated[
        pathlib.Path,
        typer.Option(
            help="The directory to store the build and flash logfiles",
        ),
    ] = util_mcp_constants.DIRECTORY_MPMCP_LOGS,
    board_variant: TyperAnnotated[
        str,
        typer.Option(
            help="The board variant to build.",
        ),
    ] = "",
) -> None:
    util_mcp_logging.mcp_init_logging(directory_logs=log_folder)

    mscp_build_flash_result = util_mcp_tentacles.mcp_build_and_flash(
        serial=serial,
        firmware_build=firmware_build,
        log_folder=log_folder,
        board_variant=board_variant,
    )
    json_text = util_mcp_tentacles.dataclasses_to_json(mscp_build_flash_result)
    print(json_text)


if __name__ == "__main__":
    app()
