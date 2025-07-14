"""
A simple formatter which allows to format titles and tables in ascii and markdown
"""

from __future__ import annotations

import abc
import dataclasses
import enum
import html
import typing

from ..report_test.util_markdown2 import md_escape


@dataclasses.dataclass
class Table:
    header: list[TableHeaderCol]
    rows: list[list[str]]


class Align(enum.IntEnum):
    LEFT = 0
    CENTER = 1
    RIGHT = 2

    @property
    def markdown(self) -> str:
        return {self.LEFT: ":-", self.CENTER: ":-:", self.RIGHT: "-:"}[self]

    @property
    def fstring(self) -> str:
        return {self.LEFT: "<", self.CENTER: "^", self.RIGHT: ">"}[self]

    @property
    def html(self) -> str:
        return f"text-align:{self.name.lower()};"


@dataclasses.dataclass
class TableHeaderCol:
    align: Align
    text: str


class RendererBase(abc.ABC):
    def __init__(self, f: typing.TextIO) -> None:
        self.f = f

    @abc.abstractmethod
    def h1(self, title: str) -> None: ...

    @abc.abstractmethod
    def h2(self, title: str) -> None: ...

    @abc.abstractmethod
    def table(self, table: Table) -> None: ...

    def close(self) -> None:
        pass


class RendererAscii(RendererBase):
    COLUMN_SPACER = "  "

    @typing.override
    def h1(self, title: str):
        self.f.write(f"{title}\n")
        self.f.write(f"{'=' * len(title)}\n\n")

    @typing.override
    def h2(self, title: str):
        self.f.write(f"\n{title}\n")
        self.f.write(f"{'-' * len(title)}\n\n")

    @typing.override
    def table(self, table: Table) -> None:
        column_count = len(table.header)
        for row in table.rows:
            assert column_count == len(row)

        def fstring(i: int) -> str:
            """
            Returns a format string for every column.
            Example "<20", "^20", ">20"
            """
            cols = [table.header[i].text, *[row[i] for row in table.rows]]
            width = max(len(col) for col in cols)
            return f"{table.header[i].align.fstring}{width:d}"

        fstrings = [fstring(i) for i in range(column_count)]

        def f(i: int, text: str) -> str:
            return format(text, fstrings[i])

        line = self.COLUMN_SPACER.join(
            [f(i, col.text) for i, col in enumerate(table.header)]
        )
        self.f.write(f"{line}\n")
        for row in table.rows:
            line = self.COLUMN_SPACER.join([f(i, col) for i, col in enumerate(row)])
            self.f.write(f"{line}\n")


class RendererMarkdown(RendererBase):
    @typing.override
    def h1(self, title: str):
        self.f.write(f"# {md_escape(title)}\n")

    @typing.override
    def h2(self, title: str):
        self.f.write(f"\n## {md_escape(title)}\n")

    @typing.override
    def table(self, table: Table) -> None:
        cols = " | ".join([md_escape(col.text) for col in table.header])
        self.f.write(f"| {cols} |\n")
        cols = " | ".join([col.align.markdown for col in table.header])
        self.f.write(f"| {cols} |\n")
        for row in table.rows:
            cols = " | ".join(md_escape(col) for col in row)
            self.f.write(f"| {cols} |\n")


class RendererHtml(RendererBase):
    HTML_START = """
<!DOCTYPE HTML>
<html>
<head>
    <meta charset="utf-8" />
    <title>Report</title>
    <style>
        table {
            border: 1px solid gray;
            border-collapse: collapse;
        }
        th, td {
            border: 1px solid gray;
            padding: 8px;
        }
        thead th {
            font-weight: bold;
        }
    </style>
</head>
<body>
    <label>
        <input type="checkbox" id="refreshCheckbox" onclick="toggleRefresh()">auto refresh
    </label>
""".strip()

    HTML_END = """
    <script>
        let refreshInterval;

        function toggleRefresh() {
            const checkbox = document.getElementById('refreshCheckbox');
            if (checkbox.checked) {
                const interval = 5000;
                refreshInterval = setInterval(() => {
                    const url = new URL(window.location);
                    url.searchParams.set('refresh', interval);
                    window.location.href = url.toString();
                }, interval);
            } else {
                clearInterval(refreshInterval);
                const url = new URL(window.location);
                url.searchParams.delete('refresh');
                window.history.replaceState({}, '', url.toString());
            }
        }

        function getRefreshIntervalFromURL() {
            const params = new URLSearchParams(window.location.search);
            return params.get('refresh');
        }

        window.onload = function() {
            const interval = getRefreshIntervalFromURL();
            if (interval) {
                document.getElementById('refreshCheckbox').checked = true;
                refreshInterval = setInterval(() => {
                    window.location.reload();
                }, interval);
            }
        }
    </script>
</body>
</html>
""".strip()

    def __init__(self, f: typing.TextIO) -> None:
        super().__init__(f=f)
        self.f.write(self.HTML_START)

    @typing.override
    def h1(self, title: str):
        self.f.write(f"<h1>{html.escape(title)}</h1>")

    @typing.override
    def h2(self, title: str):
        self.f.write(f"<h2>{html.escape(title)}</h2>")

    @typing.override
    def table(self, table: Table) -> None:
        self.f.write("<table>\n")
        self.f.write("<thead>\n")
        self.f.write("  <tr>\n")
        for col_header in table.header:
            self.f.write(
                f'    <th style="{col_header.align.html}">{html.escape(col_header.text)}</th>\n'
            )
        self.f.write("  </tr>\n")
        self.f.write("</thead>\n")

        for row in table.rows:
            self.f.write("<tr>\n")
            for col_header, col in zip(table.header, row, strict=True):
                self.f.write(
                    f'  <th style="{col_header.align.html}">{html.escape(col)}</th>\n'
                )
            self.f.write("</tr>\n")
        self.f.write("</table>\n")

    @typing.override
    def close(self) -> None:
        self.f.write(self.HTML_END)
