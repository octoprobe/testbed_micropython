from __future__ import annotations

import pathlib
import sys

from testbed_micropython.report_task import util_report_renderer
from testbed_micropython.report_task.util_report_tasks import (
    ReportTentacle,
    Task,
    TaskReport,
    Tasks,
)

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent
FILENAME_OF_THIS_FILE = pathlib.Path(__file__).name
DIRECTORY_RESULTS = DIRECTORY_OF_THIS_FILE / "test_report_tasks_testresults"
DIRECTORY_RESULTS.mkdir(parents=True, exist_ok=True)


def test_report_tasks() -> None:
    tasks = Tasks(
        [
            Task(4.6, 12.1, "PICO2_RISCV"),
            Task(4.61, 13.4, "X", [ReportTentacle("PICO", "PICO2")]),
            Task(1.3, 4.5, "PICO2"),
            Task(13.5, 16.4, "Y", [ReportTentacle("PICO", "PICO2_RISCV")]),
            Task(13.6, 20.3, "ESP8266"),
            Task(
                12.2,
                15.5,
                "Test X",
                [
                    ReportTentacle("PICO2", "PICO2_RISCV"),
                    ReportTentacle("Lolin", "ESP8266"),
                ],
            ),
            Task(
                15.6,
                19.2,
                "Test Y",
                [
                    ReportTentacle("PICO2", "PICO2_RISCV"),
                    ReportTentacle("Lolin", "ESP8266"),
                ],
            ),
        ]
    )
    report = TaskReport(tasks=tasks)

    report.report(renderer=util_report_renderer.RendererAscii(sys.stdout))

    for suffix, cls_renderer in (
        (".txt", util_report_renderer.RendererAscii),
        (".md", util_report_renderer.RendererMarkdown),
        (".html", util_report_renderer.RendererHtml),
    ):
        with (DIRECTORY_RESULTS / f"test_report{suffix}").open("w") as f:
            report.report(renderer=cls_renderer(f))


if __name__ == "__main__":
    test_report_tasks()
