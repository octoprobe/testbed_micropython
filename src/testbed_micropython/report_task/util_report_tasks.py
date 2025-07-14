from __future__ import annotations

import copy
import dataclasses
import typing

from ..report_task.util_report_renderer import (
    Align,
    RendererBase,
    Table,
    TableHeaderCol,
)

TENTACLE_MPBUILD = "mpbuild"

_TENTACLE_NONE = "."

# _QUANTIZE_FACTOR =  5  # 200ms
_QUANTIZE_FACTOR = 2  # 500ms


@dataclasses.dataclass
class ReportTentacle:
    label: str
    board_variant: str

    @property
    def text(self) -> str:
        return f"{self.label}({self.board_variant})"


@dataclasses.dataclass(repr=True)
class Task:
    start_s: float
    end_s: float
    label: str
    tentacles: typing.Sequence[ReportTentacle] = dataclasses.field(default_factory=list)
    """
    For mpbuild: This is an empty list
    For test: This contains the tentacles involved
    """

    def __post_init__(self) -> None:
        assert isinstance(self.start_s, float)
        assert isinstance(self.end_s, float)
        assert isinstance(self.label, str)
        assert isinstance(self.tentacles, list)
        for tentacle in self.tentacles:
            assert isinstance(tentacle, ReportTentacle)

    def __hash__(self) -> int:
        return hash(self.label)

    @property
    def is_mpbuild(self) -> bool:
        return len(self.tentacles) == 0

    @property
    def label_with_mpbuild_or_test(self) -> str:
        if self.is_mpbuild:
            return f"Build {self.label}"
        return f"Test {self.label}"

    @property
    def duration(self) -> float:
        return self.end_s - self.start_s

    @property
    def duration_text(self) -> str:
        return f"{self.duration:02.1f}s"

    @property
    def tentacle_text(self) -> str:
        return ", ".join([t.text for t in self.tentacles])


class Tasks(list[Task]):
    def quantize_times(self) -> None:
        def quantize(time_s: float) -> float:
            return int(time_s * _QUANTIZE_FACTOR) / _QUANTIZE_FACTOR

        for task in self:
            task.start_s = quantize(task.start_s)
            task.end_s = quantize(task.end_s)

    def align_start_s(self) -> None:
        first_start_s = self.first_start_s
        for task in self:
            task.start_s -= first_start_s
            task.end_s -= first_start_s

    def sort_by_start_s(self) -> None:
        self.sort(key=lambda t: t.start_s)

    @property
    def all_tentacles(self) -> set[str]:
        _all: set[str] = {TENTACLE_MPBUILD}
        for task in self:
            for tentacle in task.tentacles:
                _all.add(tentacle.label)
        return _all

    @property
    def all_tentacles_sorted(self) -> list[str]:
        """
        Sort the tentacles.
        But TENTACLE_MPBUILD has to be first!
        """

        def key(tentacle: str) -> tuple[bool, str]:
            return (tentacle != TENTACLE_MPBUILD, tentacle)

        return sorted(self.all_tentacles, key=key)

    @property
    def first_start_s(self) -> float:
        if len(self) == 0:
            return 0.0
        return min(task.start_s for task in self)

    def as_table(self) -> Table:
        return Table(
            header=[
                TableHeaderCol(Align.RIGHT, "Start"),
                TableHeaderCol(Align.RIGHT, "End"),
                TableHeaderCol(Align.RIGHT, "Duration"),
                TableHeaderCol(Align.LEFT, "Task"),
                TableHeaderCol(Align.LEFT, "Tentacles"),
            ],
            rows=[
                [
                    f"{task.start_s:0.1f}s",
                    f"{task.end_s:0.1f}s",
                    task.duration_text,
                    task.label_with_mpbuild_or_test,
                    task.tentacle_text,
                ]
                for task in self
            ],
        )


@dataclasses.dataclass(repr=True)
class ReportRow:
    time_s: float
    duration_s: float | None = None
    _dict_columns: dict[str, LegendTask] = dataclasses.field(default_factory=dict)
    """
    Key: tentacle label: For example "mpbuild" or "Lolin_C3"
    """

    def get_legendtask(self, tentacle: str) -> LegendTask | None:
        assert isinstance(tentacle, str)
        return self._dict_columns.get(tentacle, None)

    def set_legendtask(self, tentacle: str, legendtask: LegendTask) -> None:
        assert isinstance(tentacle, str)
        assert isinstance(legendtask, LegendTask)
        self._dict_columns[tentacle] = legendtask

    @property
    def legend_tasks_ordered_by_end_s(self) -> list[LegendTask]:
        return sorted(self._dict_columns.values(), key=lambda lt: lt.task.end_s)

    @property
    def duration_text(self) -> str:
        if self.duration_s is None:
            return ""
        return f"+{self.duration_s:0.1f}s"

    @property
    def time_text(self) -> str:
        return f"{self.time_s:0.1f}s"

    def columns(
        self,
        legend_tentacles: LegendTentacles,
        legend_tasks: LegendTasks,
    ) -> list[str]:
        def get_column(legend_tentacle: LegendTentacle) -> str:
            legend_task = self.get_legendtask(legend_tentacle.tentacle)
            if legend_task is None:
                return _TENTACLE_NONE

            return legend_task.get_combined_id(legend_tasks)

        return [
            self.time_text,
            self.duration_text,
            *[get_column(lt) for lt in legend_tentacles.legend_tentacles],
        ]


class ReportRows(list[ReportRow]):
    def header_columns(self, legend_tentacles: LegendTentacles) -> list[TableHeaderCol]:
        return [
            TableHeaderCol(Align.RIGHT, "start"),
            TableHeaderCol(Align.RIGHT, "duration"),
            *[
                TableHeaderCol(Align.RIGHT, lt.tentacle_id)
                for lt in legend_tentacles.legend_tentacles
            ],
        ]

    def finalize(self) -> None:
        previous_row: ReportRow | None = None
        for row in self:
            if previous_row is not None:
                previous_row.duration_s = row.time_s - previous_row.time_s
            previous_row = row

    def as_table(
        self, legend_tentacles: LegendTentacles, legend_tasks: LegendTasks
    ) -> Table:
        return Table(
            header=self.header_columns(legend_tentacles=legend_tentacles),
            rows=[
                row.columns(
                    legend_tentacles=legend_tentacles, legend_tasks=legend_tasks
                )
                for row in self
            ],
        )


@dataclasses.dataclass(repr=True)
class LegendTentacle:
    tentacle_id: str
    tentacle: str


@dataclasses.dataclass(repr=True)
class LegendTentacles:
    next_tentacle_id: int = ord("A")
    legend_tentacles: list[LegendTentacle] = dataclasses.field(default_factory=list)

    def add(self, tentacle: str) -> None:
        is_mpbuild = tentacle == TENTACLE_MPBUILD
        if is_mpbuild:
            tentacle_id = TENTACLE_MPBUILD
        else:
            tentacle_id = chr(self.next_tentacle_id)
            self.next_tentacle_id += 1
        legend_tentacle = LegendTentacle(tentacle_id=tentacle_id, tentacle=tentacle)
        self.legend_tentacles.append(legend_tentacle)

    def as_table(self) -> Table:
        return Table(
            header=[
                TableHeaderCol(Align.RIGHT, "Tentacle-ID"),
                TableHeaderCol(Align.LEFT, "Tentacles"),
            ],
            rows=[[lt.tentacle_id, lt.tentacle] for lt in self.legend_tentacles],
        )


@dataclasses.dataclass(repr=True)
class LegendTask:
    task_id: str
    task: Task
    build_id: str = "?"

    @property
    def is_mpbuild(self) -> bool:
        return self.task.is_mpbuild

    def get_combined_id(self, legend_tasks: LegendTasks) -> str:
        """
        Example return: b       The mpbuild task 'b' does not depend on builds
        Example return: 2(b,c)  The test task '2' depends on mpbuilds 'b' and 'c'
        """
        assert isinstance(legend_tasks, LegendTasks)
        if self.is_mpbuild:
            return self.task_id

        build_ids = [legend_tasks.get_task_id(rt) for rt in self.task.tentacles]
        build_ids_text = ",".join(build_ids)
        return f"{self.task_id}({build_ids_text})"


@dataclasses.dataclass(repr=True)
class LegendTasks:
    next_task_id: int = 1
    next_mpbuild_id: int = ord("a")
    legend_tasks: list[LegendTask] = dataclasses.field(default_factory=list)
    dict_legend_task: dict[Task, LegendTask] = dataclasses.field(default_factory=dict)
    # dict_build_label_2_id: dict[str, str] = dataclasses.field(default_factory=dict)

    @property
    def legend_tasks_sorted(self) -> list[LegendTask]:
        def key(task: LegendTask) -> tuple[bool, str]:
            """
            First: characters before numbers
            Second: alphabetically ascending
            """
            return task.task_id.isdigit(), task.task_id

        return sorted(self.legend_tasks, key=key)

    def get_task_id(self, report_tentacle: ReportTentacle) -> str:
        assert isinstance(report_tentacle, ReportTentacle)
        board_variant = report_tentacle.board_variant
        for legend_task in self.legend_tasks:
            if legend_task.task.label == board_variant:
                return legend_task.task_id
        return f"<lookup-failed={board_variant}>"

    def add(self, task: Task) -> None:
        if task.is_mpbuild:
            task_id = chr(self.next_mpbuild_id)
            self.next_mpbuild_id += 1
            # self.dict_build_label_2_id[task.label] = task_id
        else:
            task_id = str(self.next_task_id)
            self.next_task_id += 1
        legend_task = LegendTask(task_id=task_id, task=task)
        self.legend_tasks.append(legend_task)
        self.dict_legend_task[task] = legend_task

    def as_table(self) -> Table:
        return Table(
            header=[
                TableHeaderCol(Align.RIGHT, "Task-ID"),
                TableHeaderCol(Align.LEFT, "Task"),
                TableHeaderCol(Align.LEFT, "Tentacle"),
                TableHeaderCol(Align.RIGHT, "Duration"),
            ],
            rows=[
                [
                    lt.task_id,
                    lt.task.label_with_mpbuild_or_test,
                    lt.task.tentacle_text,
                    lt.task.duration_text,
                ]
                for lt in self.legend_tasks_sorted
            ],
        )


class TaskReport:
    def __init__(self, tasks: Tasks) -> None:
        self.tasks = copy.deepcopy(tasks)
        self.tasks.quantize_times()
        self.tasks.sort_by_start_s()
        self.tasks.align_start_s()

        self.legend_tasks = LegendTasks()
        for task in self.tasks:
            self.legend_tasks.add(task=task)

        self.legend_tentacles = LegendTentacles()
        for tentacle in self.tasks.all_tentacles_sorted:
            self.legend_tentacles.add(tentacle=tentacle)

        self.rows = self._append_rows()

    def _append_rows(self):
        timestamps = set()
        for task in self.tasks:
            timestamps.add(task.start_s)
            timestamps.add(task.end_s)

        timestamps_sorted = sorted(timestamps)

        rows = ReportRows()
        for timestamp_s in timestamps_sorted:
            row = ReportRow(time_s=timestamp_s)
            rows.append(row)
            for task in self.tasks:
                if task.start_s <= timestamp_s < task.end_s:
                    task_legend = self.legend_tasks.dict_legend_task[task]
                    if task.is_mpbuild:
                        row.set_legendtask(TENTACLE_MPBUILD, task_legend)

                    for tentacle in task.tentacles:
                        row.set_legendtask(tentacle.label, task_legend)
        rows.finalize()
        return rows

    def report(self, renderer: RendererBase) -> RendererBase:
        renderer.h1("Timing report")
        renderer.table(
            self.rows.as_table(
                legend_tentacles=self.legend_tentacles, legend_tasks=self.legend_tasks
            )
        )
        renderer.h2("Legend: Tentacles")
        renderer.table(self.legend_tentacles.as_table())
        renderer.h2("Legend: Tasks")
        renderer.table(self.legend_tasks.as_table())
        renderer.h2("Report input data")
        renderer.table(self.tasks.as_table())
        renderer.close()
        return renderer
