import json
import logging
import pathlib

import typer
from octoprobe.usb_tentacle.usb_tentacle import UsbTentacles
from octoprobe.util_dut_programmers import get_dict_programmers
from octoprobe.util_pyudev import UdevPoller

from .util_testrunner import instantiate_tentacles

logger = logging.getLogger(__file__)

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent
FILENAME_LOGGING_JSON = DIRECTORY_OF_THIS_FILE / "util_testbootmode_logging.json"
assert FILENAME_LOGGING_JSON.is_file()


def init_logging() -> None:
    logging.config.dictConfig(json.loads(FILENAME_LOGGING_JSON.read_text()))


def get_programmer_labels() -> str:
    return ",".join(sorted(get_dict_programmers()))


def do_debugbootmode(programmer: str) -> None:
    usb_tentacles = UsbTentacles.query(poweron=False)
    init_logging()
    if len(usb_tentacles) != 1:
        print(
            f"Expect exactly one tentacle to be connected but found {len(usb_tentacles)}!"
        )
        raise typer.Exit(code=1)
    tentacle = instantiate_tentacles(usb_tentacles)[0]
    tentacle.infra.connect_mpremote_if_needed()
    try:
        programmer_cls = get_dict_programmers()[programmer]
    except KeyError as e:
        logger.error(
            f"Programmer '{programmer}' not found. Choose one of {get_programmer_labels()}"
        )
        raise typer.Exit(code=1) from e

    programmer_obj = programmer_cls()
    with UdevPoller() as udev:
        logger.info("Test enter_boot_mode")

        event = programmer_obj.enter_boot_mode(tentacle=tentacle, udev=udev)
        logger.info(f"SUCCESS: {event=}")
