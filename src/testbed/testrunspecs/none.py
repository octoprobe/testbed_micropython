from __future__ import annotations

import logging

from testbed.constants import EnumFut
from testbed.testcollection.testrun_specs import TestArgs, TestRun, TestRunSpec

logger = logging.getLogger(__file__)


class TestRunNone(TestRun):
    """ """

    def test(self, testargs: TestArgs) -> None:
        logger.info("Empty test")


TESTRUNSPEC_RUNTESTS_NONE = TestRunSpec(
    label="RUN-NONE",
    helptext="This tests is empty. It may be a placeholder for just flashing the tentacles.",
    command=["none.py"],
    required_fut=EnumFut.FUT_MCU_ONLY,
    required_tentacles_count=1,
    testrun_class=TestRunNone,
)
