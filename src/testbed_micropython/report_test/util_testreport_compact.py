from __future__ import annotations

import dataclasses

from ..constants import EnumFut
from . import util_constants
from .util_baseclasses import ResultTestGroup

_FUT_LABELS = {
    EnumFut.FUT_BLE: "BT",
}


def _fut_label(fut: EnumFut) -> str:
    """
    Example: FUT_EXTMOD_HARDWARE -> EXTMOD_HARDWARE
    """
    label = _FUT_LABELS.get(fut, None)
    if label is not None:
        return label
    return fut.name.removeprefix("FUT_")


@dataclasses.dataclass(slots=True)
class DataCompactRow:
    """
    One row in the compact PR report:
    | ✅ | ✅ | ✅ | esp32 | ESP32_C3_DEVKIT |
    """

    port: str
    board: str
    ok_by_fut: dict[EnumFut, bool] = dataclasses.field(default_factory=dict)
    testgroup_by_fut: dict[EnumFut, str] = dataclasses.field(default_factory=dict)
    """
    The testgroup the anchor points to. If a testgroup failed, it takes precedence.
    """

    def emoji(self, fut: EnumFut) -> str:
        """
        Empty string: This fut was not tested on this board.
        """
        ok = self.ok_by_fut.get(fut, None)
        if ok is None:
            return ""
        return "✅" if ok else "❌"

    def anchor(self, fut: EnumFut) -> str:
        """
        Example: anchor_RUN-NATMODTESTS
        The anchor in the summary report.
        """
        testgroup = self.testgroup_by_fut.get(fut, None)
        if testgroup is None:
            return ""
        return util_constants.PREFIX_ANCHOR + testgroup


@dataclasses.dataclass(slots=True)
class DataCompactTable:
    """
    One column per tested fut, one row per tested board.
    """

    futs: list[EnumFut]
    rows: list[DataCompactRow]

    @property
    def fut_labels(self) -> list[str]:
        return [_fut_label(fut) for fut in self.futs]

    @staticmethod
    def factory(testgroups: list[ResultTestGroup]) -> DataCompactTable:
        dict_rows: dict[tuple[str, str], DataCompactRow] = {}
        futs: set[EnumFut] = set()
        for testgroup in testgroups:
            testrun_spec = testgroup.testrun_spec
            if testrun_spec is None:
                continue
            fut = testrun_spec.required_fut
            if testgroup.is_skip:
                continue
            futs.add(fut)

            key = (testgroup.tentacle_mcu, testgroup.board_variant)
            row = dict_rows.get(key, None)
            if row is None:
                row = DataCompactRow(
                    port=testgroup.tentacle_mcu,
                    board=testgroup.board_variant,
                )
                dict_rows[key] = row

            ok = (not testgroup.is_error) and len(testgroup.results_failed) == 0
            prev_ok = row.ok_by_fut.get(fut, True)
            if (fut not in row.testgroup_by_fut) or (prev_ok and not ok):
                # The anchor of a failed testgroup takes precedence
                row.testgroup_by_fut[fut] = testgroup.testgroup
            row.ok_by_fut[fut] = prev_ok and ok

        futs_ordered = list(EnumFut)
        return DataCompactTable(
            futs=sorted(futs, key=futs_ordered.index),
            rows=sorted(dict_rows.values(), key=lambda row: (row.port, row.board)),
        )
