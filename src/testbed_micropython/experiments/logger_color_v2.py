import logging
import logging.config

import click

logger = logging.getLogger(__file__)

LOGGER_PROGRESS = "LOGGER_PROGRESS"
logger_red = logging.getLogger(LOGGER_PROGRESS)


def init_logging() -> None:
    """
    This method will be used to initialize a multiprocessing subprocess.
    """
    log_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {"simple": {"format": "%(levelname)-8s - %(message)s"}},
        "handlers": {
            "stdout": {
                "class": "logging.StreamHandler",
                "level": "INFO",
                "formatter": "simple",
                "stream": "ext://sys.stdout",
            },
            "stderr": {
                "class": "logging.StreamHandler",
                "level": "ERROR",
                "formatter": "simple",
                "stream": "ext://sys.stderr",
            },
            "progress": {
                "class": "logging.StreamHandler",
                "level": "INFO",
                "formatter": "simple",
                "stream": "ext://sys.stderr",
            },
        },
        "root": {
            "level": "DEBUG",
            "handlers": ["stderr", "stdout"],
        },
        "LOGGER_PROGRESS": {
            "level": "DEBUG",
            "handlers": ["progress"],
        },
    }
    logging.config.dictConfig(log_config)


def main() -> None:
    init_logging()
    click.echo(click.style("Hello World!", fg="green", dim=False))
    click.echo(click.style("Hello World!", fg="green", bold=True))
    click.echo(click.style("Hello World!", fg="green", dim=True))
    click.echo(click.style("Hello World!", fg="green", dim=True, reverse=True))

    logger.info("INFO")
    logger_red.info("PROGRESS RED")


if __name__ == "__main__":
    main()
