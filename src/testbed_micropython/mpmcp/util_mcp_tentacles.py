"""
Tentacle related functionality for the MCP server.

These functions are independent of MCP and may be tested standalone.

Conventions:
* A tentacle is identified by its serial, for example 'de6528b3cb38-5f33'.
  A unique prefix/suffix is also accepted, for example '5f33'.
* All USB access is serialized using a lock as the MCP server
  runs synchronous tools in worker threads.
* Nothing may be written to stdout: The stdio transport of the MCP
  server uses stdout. Output of octoprobe is redirected to stderr.
"""

from __future__ import annotations

import dataclasses
import json
import logging
import pathlib
import typing

from octoprobe import octoprobe
from octoprobe.usb_tentacle.usb_tentacle import UsbTentacles
from octoprobe.util_mcu import FILENAME_FLASHING
from octoprobe.util_micropython_boards import BoardVariant
from octoprobe.util_pyudev import UDEV_POLLER_LAZY

from testbed_micropython import util_firmware_mpbuild
from testbed_micropython.mpmcp import util_mcp_logging
from testbed_micropython.mptest import util_testrunner
from testbed_micropython.tentacle_spec import TentacleSpecMicropython
from testbed_micropython.testcollection import baseclasses_spec

logger = logging.getLogger(__name__)


class McpResultException(BaseException):
    """
    We return with a mcp_result which will then be passed as a json-string to the agent.
    If the function was called by 'mptest ...', the this will trigger a SystemExit(0) exception.
    """

    mcp_result: typing.Any


class McpSystemExit(BaseException):
    """
    If the function was called by 'mptest ...', the this will trigger a SystemExit(1) exception.
    If the function was called by the mcp server, then this will become the 'outcome' property of the McpXyResult.
    """

    pass


@dataclasses.dataclass(frozen=True)
class McpConnectedTentacle:
    label: str
    tentacle_serial_number: str
    tentacle_spec_board: str
    tentacle_spec_build_variants: list[str]
    tentacle_spec_doc: str
    tentacle_spec_tags: str
    tentacle_spec_futs: list[str]
    tentacle_state_last_firmware_flashed: str
    infra_usb_location: str
    infra_usb_serial_port: str
    probe_usb_location: str
    probe_usb_serial_port: str
    dut_usb_location: str
    dut_usb_serial_port: str

    def __post_init__(self) -> None:
        assert isinstance(self.label, str)
        assert isinstance(self.tentacle_serial_number, str)
        assert isinstance(self.tentacle_spec_board, str)
        assert isinstance(self.tentacle_spec_build_variants, list)
        assert isinstance(self.tentacle_spec_doc, str)
        assert isinstance(self.tentacle_spec_tags, str)
        assert isinstance(self.tentacle_spec_futs, list)
        assert isinstance(self.tentacle_state_last_firmware_flashed, str)
        assert isinstance(self.infra_usb_location, str)
        assert isinstance(self.infra_usb_serial_port, str)
        assert isinstance(self.probe_usb_location, str)
        assert isinstance(self.probe_usb_serial_port, str)
        assert isinstance(self.dut_usb_location, str)
        assert isinstance(self.dut_usb_serial_port, str)
        for fut in self.tentacle_spec_futs:
            assert isinstance(fut, str)
        for variant in self.tentacle_spec_build_variants:
            assert isinstance(variant, str)

    def as_json_dict(self) -> dict[str, typing.Any]:
        return dataclasses.asdict(self)

    @staticmethod
    def factory(tentacle: baseclasses_spec.TentacleMicropython) -> McpConnectedTentacle:
        tentacle_spec = tentacle.tentacle_spec
        assert isinstance(tentacle_spec, TentacleSpecMicropython)
        tentacle_state = tentacle.tentacle_state
        usb_tentacle = tentacle.infra.usb_tentacle

        last_firmware_flashed = tentacle_state.last_firmware_flashed or ""

        return McpConnectedTentacle(
            label=tentacle.label_short,
            tentacle_serial_number=tentacle.tentacle_serial_number,
            tentacle_spec_board=tentacle_spec.board,
            tentacle_spec_build_variants=tentacle_spec.build_variants,
            tentacle_spec_doc=tentacle_spec.doc,
            tentacle_spec_tags=tentacle_spec.tags,
            tentacle_spec_futs=[fut.name for fut in tentacle_spec.futs],
            tentacle_state_last_firmware_flashed=last_firmware_flashed,
            infra_usb_location=usb_tentacle.pico_infra.location.short,
            infra_usb_serial_port=usb_tentacle.pico_infra.serial_port,
            probe_usb_location=usb_tentacle.pico_probe.location.short,
            probe_usb_serial_port=usb_tentacle.pico_probe.serial_port or "",
            dut_usb_location=tentacle.infra.usb_location_dut,
            dut_usb_serial_port=tentacle.infra.usb_tentacle.usb_port_dut.serial_port,
        )


def mcp_list_tentacles(poweron: bool = False) -> list[McpConnectedTentacle]:
    try:
        connected_tentacles = util_testrunner.query_connected_tentacles_fast()
    except Exception as e:
        logger.error(f"Terminating test due to: {e!r}")
        raise McpSystemExit(e) from e

    return [McpConnectedTentacle.factory(tentacle) for tentacle in connected_tentacles]


@dataclasses.dataclass(repr=True)
class McpBuildFlashResult:
    tentacle: McpConnectedTentacle | None = None
    filename_output_build: str = ""
    filename_output_flash: str = ""
    filename_python_log: str = ""
    filename_firmware: str = ""
    dut_serial_port: str = ""
    outcome_error: str = "early failure"
    outcome_success: bool = False

    def set_success(self) -> None:
        self.outcome_error = ""
        self.outcome_success = True


LOG_FOLDER_MPBUILD = "mpbuild"
LOG_FOLDER_FLASH = "flash"


def mcp_build_and_flash(
    serial: str,
    firmware_build: str,
    log_folder: pathlib.Path,
    board_variant: str,
) -> McpBuildFlashResult:
    try:
        result = McpBuildFlashResult(
            filename_python_log=str(log_folder / util_mcp_logging.FILENAME_LOG)
        )
        usb_tentacles = UsbTentacles.query(poweron=False)
        usb_tentacles_selected = usb_tentacles.select(serials=[serial])
        if len(usb_tentacles_selected) != 1:
            msg = f"Tentacle with serial '{serial}' is not connected!"
            logger.warning(msg)
            result.outcome_error = msg
            return result
        connected_tentacles = util_testrunner.instantiate_tentacles(
            usb_tentacles=usb_tentacles_selected
        )
        assert len(connected_tentacles) == 1
        connected_tentacle = connected_tentacles[0]

        if board_variant not in connected_tentacle.tentacle_spec.build_variants:
            msg = f"Tentacle '{serial}'/'{connected_tentacle.tentacle_spec.board}' supports {connected_tentacle.tentacle_spec.build_variants} but you provided '{board_variant}'!"
            logger.warning(msg)
            result.outcome_error = msg
            return result

        result.tentacle = McpConnectedTentacle.factory(tentacle=connected_tentacle)

        builder = util_firmware_mpbuild.Builder(
            variant=BoardVariant(
                board=connected_tentacle.tentacle_spec.board,
                variant=board_variant,
            ),
            mpbuild_artifacts=log_folder / LOG_FOLDER_MPBUILD,
        )
        repo_micropython_firmware = pathlib.Path(firmware_build).expanduser()
        if not repo_micropython_firmware.is_dir():
            msg = f"Expect '--firmware-build={firmware_build}' to point to a micropython-repo directory. But got: '{firmware_build}!"
            logger.warning(msg)
            result.outcome_error = msg
            return result

        result.filename_output_build = str(builder.docker_logfile)
        firmware_build_spec = builder.build(
            repo_micropython_firmware=repo_micropython_firmware
        )
        result.filename_firmware = str(firmware_build_spec.filename)
        connected_tentacle.tentacle_state.firmware_spec = firmware_build_spec
        connected_tentacle.tentacle_state.flash_force = True

        ctx = octoprobe.CtxTestRun(connected_tentacles=connected_tentacles)
        directories_log = log_folder / LOG_FOLDER_FLASH
        result.filename_output_flash = str(directories_log / FILENAME_FLASHING)
        ctx.function_setup_infa_and_dut(
            udev_poller=UDEV_POLLER_LAZY.udev_poller,
            tentacle=connected_tentacle,
            directory_logs=directories_log,
        )
        connected_tentacle.dut.mp_remote_close()
        result.dut_serial_port = (
            connected_tentacle.infra.usb_tentacle.usb_port_dut.serial_port
        )
        result.set_success()
        return result

    except Exception as e:
        logger.error(f"Terminating test due to: {e!r}", exc_info=e)
        result.outcome_error = repr(e)
        return result


def dataclasses_to_dict(o: object) -> dict[str, typing.Any] | str:
    if dataclasses.is_dataclass(o):
        return dataclasses.asdict(o)
    return str(0)


def dataclasses_to_json(o: object) -> str:
    json_text = json.dumps(o, indent=4, default=dataclasses_to_dict)
    return json_text


def main() -> None:
    json_text = dataclasses_to_json(mcp_list_tentacles())
    print(f"list_tentacles={json_text}")


if __name__ == "__main__":
    main()
