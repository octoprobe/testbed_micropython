from __future__ import annotations

import logging
import pathlib
import platform
import tarfile
import time

import requests
import urllib3
from octoprobe.util_constants import ExitCode

from .util_testreport import now_formatted

logger = logging.getLogger(__file__)


class TarAndHttpsPush:
    def __init__(self, directory: pathlib.Path, label: str | None):
        """
        Example label: notebook_hans-2025_04_22-12_33_22
        """
        assert isinstance(directory, pathlib.Path)
        assert isinstance(label, str | None)
        self.directory = directory
        if label is not None:
            self.label = label
            return
        self.label = self._create_local_label()

    def _create_local_label(self) -> str:
        return f"{platform.node()}_{now_formatted()}"

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
