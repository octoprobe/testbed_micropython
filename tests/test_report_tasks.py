from __future__ import annotations

import dataclasses
import pathlib
import sys

import pytest

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


@dataclasses.dataclass
class Ttestparam:
    filename_base: str
    tasks: Tasks

    @property
    def pytest_id(self) -> str:
        return self.filename_base


_TESTPARAMS = [
    Ttestparam(
        "test_report",
        Tasks(
            [
                Task(start_s=4.6, end_s=12.1, label="PICO2_RISCV"),
                Task(
                    start_s=4.61,
                    end_s=13.4,
                    label="X",
                    tentacles=[ReportTentacle(label="PICO", board_variant="PICO2")],
                ),
                Task(start_s=1.3, end_s=4.5, label="PICO2"),
                Task(
                    start_s=13.5,
                    end_s=16.4,
                    label="Y",
                    tentacles=[
                        ReportTentacle(label="PICO", board_variant="PICO2_RISCV")
                    ],
                ),
                Task(start_s=13.6, end_s=20.3, label="ESP8266"),
                Task(
                    start_s=12.2,
                    end_s=15.5,
                    label="Test X",
                    tentacles=[
                        ReportTentacle(label="PICO2", board_variant="PICO2_RISCV"),
                        ReportTentacle(label="Lolin", board_variant="ESP8266"),
                    ],
                ),
                Task(
                    start_s=15.6,
                    end_s=19.2,
                    label="Test Y",
                    tentacles=[
                        ReportTentacle(label="PICO2", board_variant="PICO2_RISCV"),
                        ReportTentacle(label="Lolin", board_variant="ESP8266"),
                    ],
                ),
            ]
        ),
    ),
    Ttestparam(
        "test_RPI_PICO2",
        Tasks(
            [
                Task(
                    start_s=272368.571032019,
                    end_s=272430.121997467,
                    label="RPI_PICO2",
                    tentacles=[],
                ),
                Task(
                    start_s=272430.224855193,
                    end_s=272445.324893713,
                    label="RUN-TESTS_EXTMOD_HARDWARE@5334-RPI_PICO2",
                    tentacles=[
                        ReportTentacle(
                            label="5334-RPI_PICO2", board_variant="RPI_PICO2"
                        )
                    ],
                ),
                Task(
                    start_s=272430.122841108,
                    end_s=272468.234852466,
                    label="RPI_PICO2-RISCV",
                    tentacles=[],
                ),
                Task(
                    start_s=272468.388994379,
                    end_s=272483.717806491,
                    label="RUN-TESTS_EXTMOD_HARDWARE@5334-RPI_PICO2-RISCV",
                    tentacles=[
                        ReportTentacle(
                            label="5334-RPI_PICO2", board_variant="RPI_PICO2-RISCV"
                        )
                    ],
                ),
            ]
        ),
    ),
]


@pytest.mark.parametrize(
    "testparam", _TESTPARAMS, ids=lambda testparam: testparam.pytest_id
)
def test_report_tasks(testparam: Ttestparam) -> None:
    report = TaskReport(tasks=testparam.tasks)

    report.report(renderer=util_report_renderer.RendererAscii(sys.stdout))

    for suffix, cls_renderer in (
        (".txt", util_report_renderer.RendererAscii),
        (".md", util_report_renderer.RendererMarkdown),
        (".html", util_report_renderer.RendererHtml),
    ):
        with (DIRECTORY_RESULTS / f"{testparam.filename_base}{suffix}").open("w") as f:
            report.report(renderer=cls_renderer(f))
