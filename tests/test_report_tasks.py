from __future__ import annotations

import pathlib
import sys

from testbed.reports.util_report_renderer import RendererAscii, RendererMarkdown
from testbed.reports.util_report_tasks import ReportTentacle, Task, TaskReport, Tasks


def main():
    tasks = Tasks(
        [
            Task(4.6, 12.1, "PICO2-RISCV"),
            Task(4.61, 13.4, "X", [ReportTentacle("PICO", "PICO2")]),
            Task(1.3, 4.5, "PICO2"),
            Task(13.5, 16.4, "Y", [ReportTentacle("PICO", "PICO2-RISCV")]),
            Task(13.6, 20.3, "ESP8266"),
            Task(
                12.2,
                15.5,
                "Test X",
                [
                    ReportTentacle("PICO2", "PICO2-RISCV"),
                    ReportTentacle("Lolin", "ESP8266"),
                ],
            ),
            Task(
                15.6,
                19.2,
                "Test Y",
                [
                    ReportTentacle("PICO2", "PICO2-RISCV"),
                    ReportTentacle("Lolin", "ESP8266"),
                ],
            ),
        ]
    )
    report = TaskReport(tasks=tasks)

    report.report(renderer=RendererMarkdown(f=sys.stdout))
    report.report(renderer=RendererAscii(f=sys.stdout))

    filename_report = pathlib.Path(__file__).with_suffix(".md")
    with filename_report.open("w", encoding="ascii") as f:
        report.report(renderer=RendererMarkdown(f=f))


if __name__ == "__main__":
    main()
