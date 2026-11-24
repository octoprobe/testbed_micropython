from __future__ import annotations

import dataclasses

from ..constants import EnumFut
from .util_baseclasses import ResultTestGroup

_FUTS_HIDDEN = (EnumFut.FUT_MCU_ONLY,)

_FUT_LABELS = {
    EnumFut.FUT_BLE: "BT",
}


def _fut_label(fut: EnumFut) -> str:
    """
    Example: FUT_EXTMOD_HARDWARE -> EXTMOD_HARDWARE
    """
    return fut.name
    label = _FUT_LABELS.get(fut, None)
    if label is not None:
        return label
    return fut.name.removeprefix("FUT_")


@dataclasses.dataclass(slots=True)
class DataCompactLine:
    """
    One line in the compact PR report:
    | ✅ EXTMOD_HARDWARE | esp32 | ESP32_C3_DEVKIT |
    """

    fut: EnumFut
    port: str
    board: str
    ok: bool = True

    @property
    def fut_text(self) -> str:
        return _fut_label(self.fut)

    @property
    def emoji(self) -> str:
        return "✅" if self.ok else "❌"

    @staticmethod
    def factory_compact_lines(
        testgroups: list[ResultTestGroup],
    ) -> list[DataCompactLine]:
        dict_lines: dict[tuple[EnumFut, str, str], DataCompactLine] = {}
        for testgroup in testgroups:
            testrun_spec = testgroup.testrun_spec
            if testrun_spec is None:
                continue
            fut = testrun_spec.required_fut
            if fut in _FUTS_HIDDEN:
                continue
            if testgroup.is_skip:
                continue
            key = (fut, testgroup.tentacle_mcu, testgroup.board_variant)
            line = dict_lines.get(key, None)
            if line is None:
                line = DataCompactLine(
                    fut=fut,
                    port=testgroup.tentacle_mcu,
                    board=testgroup.board_variant,
                )
                dict_lines[key] = line

            if testgroup.is_error or len(testgroup.results_failed) > 0:
                line.ok = False

        futs_ordered = list(EnumFut)
        return sorted(
            dict_lines.values(),
            key=lambda line: (futs_ordered.index(line.fut), line.port, line.board),
        )
