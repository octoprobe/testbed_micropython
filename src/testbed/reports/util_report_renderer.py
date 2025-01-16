"""
A simple formatter which allows to format titles and tables in ascii and markdown
"""

from __future__ import annotations

import abc
import dataclasses
import enum
import io
import typing

import markdown2


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


@dataclasses.dataclass
class TableHeaderCol:
    align: Align
    text: str


class RendererBase(abc.ABC):
    def __init__(self) -> None:
        self.f = io.StringIO()

    @abc.abstractmethod
    def h1(self, title: str): ...

    @abc.abstractmethod
    def h2(self, title: str): ...

    @abc.abstractmethod
    def table(self, table: Table) -> None: ...

    def getvalue(self) -> str:
        return self.f.getvalue()


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
            width = max([len(col) for col in cols])
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
        self.f.write(f"# {title}\n")

    @typing.override
    def h2(self, title: str):
        self.f.write(f"\n## {title}\n")

    @typing.override
    def table(self, table: Table) -> None:
        cols = " | ".join([col.text for col in table.header])
        self.f.write(f"| {cols} |\n")
        cols = " | ".join([col.align.markdown for col in table.header])
        self.f.write(f"| {cols} |\n")
        for row in table.rows:
            cols = " | ".join(row)
            self.f.write(f"| {cols} |\n")


class RendererHtml(RendererMarkdown):
    HTML_START = """
    <!DOCTYPE HTML>
    <html>
    <head>
        <meta charset="utf-8" />
        <meta http-equiv="refresh" content="5" />
        <title>Report</title>
    </head>
    <body>
    """.strip()
    HTML_END = """
    </body>
    </html>
    """.strip()

    @typing.override
    def getvalue(self) -> str:
        """
        Convert md to html
        """
        self.f.write(self.HTML_END)
        html = markdown2.markdown(
            super().getvalue(),
            extras=[
                "tables",
            ],
        )

        return f"{self.HTML_START}\n{html}\n{self.HTML_END}"
