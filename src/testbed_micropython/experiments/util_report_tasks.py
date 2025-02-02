from __future__ import annotations

import abc
import dataclasses
import enum
import pathlib
import sys
import typing

_TENTACLE_NONE = "-"


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


class FormatterBase(abc.ABC):
    def __init__(self, f: typing.TextIO) -> None:
        self.f = f

    @abc.abstractmethod
    def h1(self, title: str): ...

    @abc.abstractmethod
    def h2(self, title: str): ...

    @abc.abstractmethod
    def table(self, table: Table) -> None: ...


class FormatterAscii(FormatterBase):
    @typing.override
    def h1(self, title: str):
        self.f.write(f"{title}\n")
        self.f.write(f"{'='*len(title)}\n\n")

    @typing.override
    def h2(self, title: str):
        self.f.write(f"\n{title}\n")
        self.f.write(f"{'-'*len(title)}\n\n")

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

        line = " ".join([f(i, col.text) for i, col in enumerate(table.header)])
        self.f.write(f"{line}\n")
        for row in table.rows:
            line = " ".join([f(i, col) for i, col in enumerate(row)])
            self.f.write(f"{line}\n")


class FormatterMarkdown(FormatterBase):
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


@dataclasses.dataclass
class Table:
    header: list[TableHeaderCol]
    rows: list[list[str]]


@dataclasses.dataclass(repr=True, unsafe_hash=True)
class Task:
    tentacle: str | None
    label: str
    start_s: float
    end_s: float

    @property
    def duration(self) -> float:
        return self.end_s - self.start_s

    @property
    def duration_text(self) -> str:
        return f"{self.duration:02.1f}s"

    @property
    def tentacle_text(self) -> str:
        if self.tentacle is None:
            return ""
        return self.tentacle


class Tasks(list[Task]):
    def sort_by_start(self) -> None:
        self.sort(key=lambda t: t.start_s)

    @property
    def tentacles(self) -> set[str]:
        return {t.tentacle for t in self if t.tentacle is not None}

    def as_table(self, first_start_s: float) -> Table:
        return Table(
            header=[
                TableHeaderCol(Align.RIGHT, "start"),
                TableHeaderCol(Align.RIGHT, "end"),
                TableHeaderCol(Align.RIGHT, "duration"),
                TableHeaderCol(Align.LEFT, "tentacle"),
                TableHeaderCol(Align.LEFT, "task"),
            ],
            rows=[
                [
                    f"{task.start_s-first_start_s:0.1f}s",
                    f"{task.end_s-first_start_s:0.1f}s",
                    task.duration_text,
                    task.tentacle_text,
                    task.label,
                ]
                for task in self
            ],
        )


@dataclasses.dataclass(repr=True)
class ReportRow:
    start_s: float
    dict_columns: dict[str, LegendTask] = dataclasses.field(default_factory=dict)

    def columns(
        self, first_start_s: float, legend_tentacles: LegendTentacles
    ) -> list[str]:
        start_text = f"{self.start_s-first_start_s:0.1f}s"
        columns = [start_text]

        def get_column(legend_tentacle: LegendTentacle) -> str:
            legend_task = self.dict_columns.get(legend_tentacle.tentacle, None)
            if legend_task is None:
                return _TENTACLE_NONE
            return legend_task.task_id_text

        columns.extend([get_column(lt) for lt in legend_tentacles.legend_tentacles])
        return columns


class ReportRows(list[ReportRow]):
    def header_columns(self, legend_tentacles: LegendTentacles) -> list[TableHeaderCol]:
        columns = [
            TableHeaderCol(Align.LEFT, "time"),
            *[
                TableHeaderCol(Align.RIGHT, lt.tentacle_id_text)
                for lt in legend_tentacles.legend_tentacles
            ],
        ]
        return columns

    @property
    def first_start_s(self) -> float:
        if len(self) == 0:
            return 0.0

        return self[0].start_s

    def as_table(self, legend_tentacles: LegendTentacles) -> Table:
        first_start_s = self.first_start_s

        return Table(
            header=self.header_columns(legend_tentacles=legend_tentacles),
            rows=[
                row.columns(
                    first_start_s=first_start_s, legend_tentacles=legend_tentacles
                )
                for row in self
            ],
        )


@dataclasses.dataclass(repr=True)
class LegendTentacle:
    tentacle_id: int
    tentacle: str

    def __hash__(self) -> int:
        return hash(self.tentacle_id)

    @property
    def tentacle_id_text(self) -> str:
        return chr(self.tentacle_id)


@dataclasses.dataclass(repr=True)
class LegendTentacles:
    next_tentacle_id: int = ord("A")
    legend_tentacles: list[LegendTentacle] = dataclasses.field(default_factory=list)

    def add(self, tentacle: str) -> str:
        legend_tentacle = LegendTentacle(
            tentacle_id=self.next_tentacle_id, tentacle=tentacle
        )
        self.legend_tentacles.append(legend_tentacle)
        self.next_tentacle_id += 1
        return legend_tentacle.tentacle_id_text

    def as_table(self) -> Table:
        return Table(
            header=[
                TableHeaderCol(Align.RIGHT, "Tentacle-ID"),
                TableHeaderCol(Align.LEFT, "Tentacle"),
            ],
            rows=[[lt.tentacle_id_text, lt.tentacle] for lt in self.legend_tentacles],
        )


@dataclasses.dataclass(repr=True)
class LegendTask:
    task_id: int
    task: Task

    def __hash__(self) -> int:
        return hash(self.task_id)

    @property
    def task_id_text(self) -> str:
        return str(self.task_id)


@dataclasses.dataclass(repr=True)
class LegendTasks:
    next_task_id: int = 1
    legend_tasks: list[LegendTask] = dataclasses.field(default_factory=list)

    def add(self, task: Task) -> LegendTask:
        legend_task = LegendTask(task_id=self.next_task_id, task=task)
        self.legend_tasks.append(legend_task)
        self.next_task_id += 1
        return legend_task

    def as_table(self) -> Table:
        return Table(
            header=[
                TableHeaderCol(Align.RIGHT, "Tentacle-ID"),
                TableHeaderCol(Align.LEFT, "Tentacle"),
                TableHeaderCol(Align.LEFT, "Task"),
                TableHeaderCol(Align.RIGHT, "Duration"),
            ],
            rows=[
                [
                    lt.task_id_text,
                    lt.task.tentacle_text,
                    lt.task.label,
                    lt.task.duration_text,
                ]
                for lt in self.legend_tasks
            ],
        )


@dataclasses.dataclass(repr=True)
class TaskReport:
    tasks: Tasks
    active_legend_tasks: set[LegendTask] = dataclasses.field(default_factory=set)

    def report(self, formatter: FormatterAscii):
        self.tasks.sort_by_start()
        legend_tentacles = LegendTentacles()
        for tentacle in sorted(self.tasks.tentacles):
            legend_tentacles.add(tentacle=tentacle)
        legend_tasks = LegendTasks()
        rows = ReportRows()
        for task in self.tasks:
            legend_task = legend_tasks.add(task)

            row = ReportRow(start_s=task.start_s)
            rows.append(row)

            def update_active_tasks(start_s: float, legend_task: LegendTask):
                for active_legend_task in self.active_legend_tasks.copy():
                    if active_legend_task.task.end_s < start_s:
                        self.active_legend_tasks.remove(active_legend_task)
                self.active_legend_tasks.add(legend_task)

            update_active_tasks(start_s=task.start_s, legend_task=legend_task)

            for active_legend_task in self.active_legend_tasks:
                if active_legend_task.task.tentacle is None:
                    continue
                row.dict_columns[active_legend_task.task.tentacle] = active_legend_task

        formatter.h1("Timing report")
        formatter.table(rows.as_table(legend_tentacles=legend_tentacles))
        formatter.h2("Legend: Tentacles")
        formatter.table(legend_tentacles.as_table())
        formatter.h2("Legend: Tasks")
        formatter.table(legend_tasks.as_table())
        formatter.h2("Detail report")
        formatter.table(self.tasks.as_table(first_start_s=rows.first_start_s))


def main():
    tasks = Tasks(
        [
            Task(None, "Build A", start_s=1.3, end_s=4.5),
            Task(None, "Build B", start_s=4.6, end_s=12.1),
            Task("PICO", "Test X", start_s=4.6, end_s=13.4),
            Task("PICO", "Test Y", start_s=13.5, end_s=16.4),
            Task("PYBV11", "Test X", start_s=12.2, end_s=15.5),
            Task("PYBV11", "Test Y", start_s=15.6, end_s=19.2),
        ]
    )
    report = TaskReport(tasks=tasks)

    # report.report(formatter=FormatterMarkdown(f=sys.stdout))
    report.report(formatter=FormatterAscii(f=sys.stdout))

    filename_report = pathlib.Path(__file__).with_suffix(".md")
    with filename_report.open("w") as f:
        report.report(formatter=FormatterMarkdown(f=f))


if __name__ == "__main__":
    main()
