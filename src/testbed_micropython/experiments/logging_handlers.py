import enum
import logging
import logging.config

logger = logging.getLogger(__file__)

LOGGER_PROGRESS = "LOGGER_PROGRESS"
logger_red = logging.getLogger(LOGGER_PROGRESS)

CSI = "\033["

Color = enum.Enum("Color", "BLACK RED GREEN YELLOW BLUE MAGENTA CYAN WHITE", start=30)


class AnsiColorHandler(logging.StreamHandler):
    # https://stackoverflow.com/questions/384076/how-can-i-color-python-logging-output/45394501
    LOGLEVEL_COLORS = {
        "DEBUG": Color.BLUE,
        "INFO": Color.GREEN,
        "WARNING": Color.RED,
        "ERROR": Color.RED,
        "CRITICAL": Color.RED,
    }

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.formatter = logging.Formatter("%(levelname)-8s - %(message)s")

    def format(self, record: logging.LogRecord) -> str:
        message: str = super().format(record)
        # use colors in tty
        if self.stream.isatty() and (
            color := self.LOGLEVEL_COLORS.get(record.levelname)
        ):
            message = f"{CSI}{color.value}m{message}{CSI}0m"
        return message
