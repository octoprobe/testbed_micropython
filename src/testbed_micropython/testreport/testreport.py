from __future__ import annotations

import logging
import pathlib

from octoprobe.util_constants import DirectoryTag
from octoprobe.util_jinja2 import JinjaEnv

from testbed_micropython.testreport.util_markdown2 import markdown2html, md_escape
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
        self.data = Data.gather_json_files(directory_results=directory_results)
        self.list_directory_expansion: list[tuple[str, str]] = []
        self._init()

    def _init(self) -> None:
        dict_expansions: dict[str, str] = {
            DirectoryTag.R: f"https://reports.octoprobe.org/{self.label}/",
            DirectoryTag.P: "",
        }
        for tag, directory in self.data.tests.directories.items():
            if not directory.endswith("/"):
                directory += "/"
            expansion = dict_expansions.get(tag, None)
            if expansion is None:
                continue
            self.list_directory_expansion.append((directory, expansion))
        # Take the longest path first
        self.list_directory_expansion.sort(key=lambda e: len(e[0]), reverse=True)

    def render(self, action_url: str | None = None) -> None:
        assert isinstance(action_url, str | None)
        filename_md = self.directory_results / "octoprobe_summary_report.md"
        filename_template = DIRECTORY_OF_THIS_FILE / "octoprobe_summary_report.jinja"

        template = filename_template.read_text()

        title = "Octoprobe test report"

        jinja_env = JinjaEnv()
        jinja_env.env.filters["hidezero"] = lambda i: "" if i == 0 else i
        jinja_env.env.filters["hidezerobold"] = lambda i: "" if i == 0 else f"**{i}**"
        jinja_env.env.filters["md_escape"] = md_escape
        jinja_env.env.filters["fix_links"] = lambda text: self._fix_links(text)

        report_md = jinja_env.render_string(
            micropython_code=template,
            data=self.data,
            action_url=action_url,
            title=title,
        )

        filename_md.write_text(report_md)

        filename_html = filename_md.with_suffix(".html")
        filename_html.write_text(markdown2html(report_md, title=title))

    def _fix_links(self, report_text: str) -> str:
        for directory, expansion in self.list_directory_expansion:
            report_text = report_text.replace(directory, expansion)
        return report_text
