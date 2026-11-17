from __future__ import annotations

import logging
import pathlib
import typing

import typer

from ..mptest import util_testrunner
from . import util_mcp_logging, util_mcp_tentacles

logger = logging.getLogger(__name__)

# 'typer' does not work correctly with typing.Annotated
# Required is: typing_extensions.Annotated
TyperAnnotated = typing.Annotated

# mypy: disable-error-code="valid-type"
# This will disable this warning:
#   op.py:58: error: Variable "octoprobe.scripts.op.TyperAnnotated" is not valid as a type  [valid-type]
#   op.py:58: note: See https://mypy.readthedocs.io/en/stable/common_issues.html#variables-vs-type-aliases

app = typer.Typer(pretty_exceptions_enable=False)


@app.command(help="List connected tentacles")
def list_tentacles(
    log_folder: TyperAnnotated[
        pathlib.Path,
        typer.Option(
            help="The directory to store the build and flash logfiles",
        ),
    ] = util_mcp_logging.DIRECTORY_MPMCP_LOGS,
) -> None:
    util_mcp_logging.mcp_init_logging(directory_logs=log_folder)
    try:
        connected_tentacles = util_testrunner.query_connected_tentacles_fast()
    except Exception as e:
        logger.error(f"Terminating test due to: {e!r}")
        raise typer.Exit(1) from e

    print("")
    print("Connected")
    for tentacle in connected_tentacles:
        print(f"  {tentacle.label}")
        print(f"RP_INFRA: {tentacle.infra.usb_tentacle.serial_port}")
        print(f"DUT: {tentacle.infra.usb_tentacle.usb_port_dut.device_text}")
        print(f"RP_PROBE: {tentacle.infra.usb_tentacle.usb_port_probe.device_text}")

        print(
            f"      infra: {tentacle.infra.usb_location_infra} {tentacle.infra.usb_tentacle.pico_infra.serial_port}"
        )
        print(
            f"      dut:   {tentacle.infra.usb_location_dut} {tentacle.infra.usb_tentacle.usb_port_dut.device_text}"
        )

        variants = ",".join(tentacle.tentacle_spec.board_build_variants)
        print(f"    variants={variants}")
        futs = ",".join([fut.name for fut in tentacle.tentacle_spec.futs])
        print(f"    futs={futs}")


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
    ] = util_mcp_logging.DIRECTORY_MPMCP_LOGS,
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
    pass
