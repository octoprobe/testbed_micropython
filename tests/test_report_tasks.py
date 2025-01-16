from __future__ import annotations

import pathlib

from testbed.reports import util_report_renderer
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
    report = TaskReport(tasks=tasks, align_time=True)

    renderer = util_report_renderer.RendererAscii()
    report.report(renderer=renderer)
    print(renderer.getvalue())

    for suffix, renderer in (
        (".txt", util_report_renderer.RendererAscii()),
        (".md", util_report_renderer.RendererMarkdown()),
        (".html", util_report_renderer.RendererHtml()),
    ):
        report.report(renderer=renderer)
        filename_report = pathlib.Path(__file__).with_suffix(suffix)
        filename_report.write_text(renderer.getvalue())


if __name__ == "__main__":
    main()
