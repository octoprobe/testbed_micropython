from __future__ import annotations

import logging
import pathlib

from octoprobe import util_jinja2
from octoprobe.util_constants import DirectoryTag

from testbed_micropython.testreport.util_testreport import Data

logger = logging.getLogger(__file__)

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent


class ReportRenderer:
    def __init__(
        self,
        directory_results: pathlib.Path,
        label: str | None = None,
    ) -> None:
        assert isinstance(directory_results, pathlib.Path)
        assert isinstance(label, str | None)
        self.directory_results = directory_results
        self.label = label
        self.data = Data.factory(directory_results=directory_results)

    def render(self, action_url: str | None = None) -> None:
        assert isinstance(action_url, str | None)
        filename = self.directory_results / "octoprobe_summary_report.md"
        filename_template = DIRECTORY_OF_THIS_FILE / "octoprobe_summary_report.jinja"
        template = filename_template.read_text()

        report_text = util_jinja2.render(
            template,
            data=self.data,
            action_url=action_url,
        )

        report_text = self._fix_links(report_text=report_text)

        filename.write_text(report_text)

    def _fix_links(self, report_text: str) -> str:
        dict_expansions = {
            DirectoryTag.R: f"https://reports.octoprobe.org/{self.label}/testresults/",
            DirectoryTag.P: "",
        }
        for tag, directory in self.data.tests.directories.items():
            if not directory.endswith("/"):
                directory += "/"
            expansion = dict_expansions.get(tag, None)
            if expansion is None:
                continue
            report_text = report_text.replace("[" + directory, "[")
            report_text = report_text.replace("(" + directory, "(" + expansion)
        return report_text
