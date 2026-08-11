"""
This package defines the json report which is the interface between MicroPython
tests and testbed_micropython.
This is an example:
{
  "args": {
    "trace_output": false,
    "test_instance": "port:/dev/ttyUSB2",
  },
  "results": [
    [
      "extmod_hardware/machine_can_instances.py",
      "skip",
      ""
    ],
    [
      "extmod_hardware/machine_i2c_target.py",
      "fail",
      ""
    ],
    [
      "extmod_hardware/machine_pwm.py",
      "fail",
      ""
    ],
    [
      "extmod_hardware/machine_uart_irq_rxidle.py",
      "ok",
      ""
    ]
  ],
  "failed_tests": [
    "extmod_hardware/machine_i2c_target.py",
    "extmod_hardware/machine_pwm.py",
    "extmod_hardware/machine_uart_irq_break.py",
  ],
  "ignored_tests": []
}
"""

import json
import pathlib


class MpResults:
    SKIP = "skip"
    FAIL = "fail"
    PASS = "pass"

    def __init__(self) -> None:
        self.results: list[tuple[str, str, str]] = []

    def add_pass(self, name: str, comment: str = "") -> None:
        self._add_outcome(name, self.PASS, comment)

    def add_skip(self, name: str, comment: str = "") -> None:
        self._add_outcome(name, self.SKIP, comment)

    def add_fail(self, name: str, comment: str = "") -> None:
        self._add_outcome(name, self.FAIL, comment)

    def _add_outcome(self, name: str, outcome: str, comment: str = "") -> None:
        self.results.append((name, outcome, comment))

    @property
    def failures(self) -> list[str]:
        return sorted(
            [
                name
                for name, outcome, comment in self.results
                if outcome not in ("ok", "skip")
            ]
        )

    def save_results(
        self,
        directory: pathlib.Path,
        filename: str = "_results.json",
    ) -> None:
        filename_results = directory / filename

        dict_file = {"args": {}, "results": self.results, "failed_tests": self.failures}
        filename_results.write_text(json.dumps(dict_file))
