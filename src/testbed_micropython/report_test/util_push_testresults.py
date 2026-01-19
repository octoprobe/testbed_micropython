from __future__ import annotations

import datetime
import logging
import pathlib
import platform
import re
import tarfile
import time

import requests
import urllib3
from octoprobe.util_constants import ExitCode

from . import util_baseclasses, util_constants

logger = logging.getLogger(__file__)


class TarAndHttpsPush:
    def __init__(self, directory: pathlib.Path, label: str):
        """
        Example label: notebook_hans-2025_04_22-12_33_22
        """
        assert isinstance(directory, pathlib.Path)
        assert isinstance(label, str)
        self.directory = directory
        self.label = label

    def _create_tarfile(self) -> pathlib.Path:
        filename_tar = pathlib.Path("/tmp") / f"{self.label}.tar.gz"
        with tarfile.open(filename_tar, "w:gz") as tar:
            for file in self.directory.rglob("*"):
                if file.is_file():
                    # arcname = f"{DIRECTORY_NAME_TESTRESULTS}/{file.relative_to(self.directory)}"
                    arcname = str(file.relative_to(self.directory))
                    tar.add(file, arcname=arcname)
        logger.info(f"Created {filename_tar}.")
        return filename_tar

    def _http_push(self, url: str, filename: pathlib.Path) -> ExitCode:
        logger.info(f"About to push to {url}...")

        begin_s = time.monotonic()
        with filename.open("rb") as tar_file:
            files = {
                "label": (None, self.label),
                "file": (filename.name, tar_file, "application/gzip"),
            }
            verify_ssl = False
            if not verify_ssl:
                urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            response = requests.post(
                url,
                files=files,  # type: ignore[arg-type]
                verify=verify_ssl,
                timeout=20.0,
            )

        duration_s = time.monotonic() - begin_s
        duration_text = f"{duration_s:0.1f}s"
        if response.status_code == 200:
            size_mb = filename.stat().st_size / (1024 * 1024)
            logger.info(
                f"Successfully uploaded {size_mb:0.3f} MBytes in {duration_text}."
            )
            return ExitCode.SUCCESS
        logger.error(
            f"Failed to upload to {url}: {response.status_code} {response.text}!"
        )
        return ExitCode.ERROR

    def https_push(self, url: str) -> ExitCode:
        filename_tar = self._create_tarfile()
        return self._http_push(url=url, filename=filename_tar)


class DirectoryManualWorkflow:
    """
    local_hostname_20250116-185542
    """

    REGEX = re.compile(r"^(?P<hostname>.*)_(?P<start>\d{8}-\d{6})$")
    FORMAT = "%Y%m%d-%H%M%S"
    FORMAT_SHORT = "%m%d-%H%M"

    def __init__(self, hostname: str, started_at: datetime.datetime) -> None:
        self.hostname = hostname
        self.started_at = started_at

    @property
    def directory_name(self) -> str:
        return f"{self.hostname}_{self.started_at.strftime(self.FORMAT)}"

    @property
    def started_ad_short(self) -> str:
        return self.started_at.strftime(self.FORMAT_SHORT)

    @property
    def started_at_text(self) -> str:
        return self.started_at.strftime(util_constants.FORMAT_HTTP_STARTED_AT)

    @classmethod
    def factory_now(cls) -> DirectoryManualWorkflow:
        return cls(
            hostname=platform.node(),
            started_at=datetime.datetime.now(),
        )

    @classmethod
    def factory_directory_results(
        cls,
        directory_results: pathlib.Path,
    ) -> DirectoryManualWorkflow:
        """
        The directory 'testresults' is given which
        must include a directory 'context.json'.
        The starttime from 'context.json' will be used.
        The hostname is not part of 'context.json', hence we use platform.node().
        """
        assert isinstance(directory_results, pathlib.Path)

        result_context = util_baseclasses.ResultContext.factory(
            directory_results / util_constants.FILENAME_CONTEXT_JSON
        )
        return cls(
            hostname=platform.node(),
            started_at=result_context.time_start_datetime,
        )

    @classmethod
    def factory_directory(cls, directory: str) -> DirectoryManualWorkflow | None:
        assert isinstance(directory, str)

        match = cls.REGEX.match(directory)
        if match is None:
            return None
        started_at_text = match.group("start")
        return cls(
            hostname=match.group("hostname"),
            started_at=datetime.datetime.strptime(started_at_text, cls.FORMAT),
        )
