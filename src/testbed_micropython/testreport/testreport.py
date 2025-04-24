from __future__ import annotations

import logging
import pathlib

from octoprobe import util_jinja2

from testbed_micropython.testreport.util_testreport import Data

logger = logging.getLogger(__file__)

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent


class ReportRenderer:
    def __init__(self, directory_results: pathlib.Path) -> None:
        self.directory_results = directory_results
        self.data = Data.factory(directory_results=directory_results)

    def render(self) -> None:
        filename = self.directory_results / "octoprobe_summary_report.md"
        filename_template = DIRECTORY_OF_THIS_FILE / "octoprobe_summary_report.jinja"
        template = filename_template.read_text()

        report_text = util_jinja2.render(template, data=self.data)

        filename.write_text(report_text)
