from __future__ import annotations

import json
import logging

from octoprobe.util_constants import TAG_MCU

from ..constants import EnumFut
from ..testcollection.constants import (
    TIMEOUT_FLASH_S,
)
from ..testcollection.testrun_specs import (
    TestArgs,
    TestRun,
    TestRunSpec,
)

logger = logging.getLogger(__file__)

CMD_FLASH_FORMAT = """
import sys

def flash_format():
    if sys.platform == "rp2":
        import os, vfs, rp2
        vfs.VfsLfs2.mkfs(rp2.Flash(), progsize=256)
        os.sync()
        print("PASS")
        return
    if sys.platform == "pyboard":
        if "WB55" in sys.implementation._machine:
            import os, vfs, pyb
            vfs.VfsLfs2.mkfs(pyb.Flash(start=0))
            os.sync()
        else:
            import os, vfs, pyb
            vfs.umount('/flash')
            vfs.VfsLfs2.mkfs(pyb.Flash(start=0))
            vfs.mount(pyb.Flash(start=0), '/flash')
            os.chdir('/flash')
            os.sync()
        print("PASS")
        return
    if sys.platform == "esp32":
        pass
    if sys.platform == "mimxrt":
        pass
    if sys.platform == "samd":
        pass

    print("SKIP. Please add support for flash format on this platform.")
    raise SystemExit

flash_format()
"""


class TestRunFlashFormat(TestRun):
    def test(self, testargs: TestArgs) -> None:
        if testargs.debug_skip_tests_with_message:
            return

        tentacle = self.tentacle_variant.tentacle
        mcu = tentacle.get_tag(TAG_MCU)
        if mcu is None:
            logger.info(f"{tentacle.label_short}: Skip flash format: Not mcu defined.")
            return

        mp_remote = tentacle.dut.mp_remote
        rc = mp_remote.exec_raw(cmd=CMD_FLASH_FORMAT)
        logger.debug(f"CMD_FLASH_FORMAT: {CMD_FLASH_FORMAT}")
        logger.info(f"See flash format command in debug-log. Return code: {rc.strip()}")

        outcome = "fail"
        if "SKIP" in rc:
            outcome = "skip"
        if "PASS" in rc:
            outcome = "pass"
        dict_result = {
            "args": {},
            "results": [
                ["format_flash", outcome, ""],
            ],
        }
        filename_results = (
            testargs.testresults_directory.directory_test / "_results.json"
        )
        filename_results.write_text(json.dumps(dict_result))


TESTRUNSPEC_RUN_FLASH_FORMAT = TestRunSpec(
    label="RUN-FLASH_FORMAT",
    helptext="Reformat the flash (repair broken filesystem)",
    command=["format_flash"],
    required_fut=EnumFut.FUT_MCU_ONLY,
    testrun_class=TestRunFlashFormat,
    timeout_s=10.0 + TIMEOUT_FLASH_S,
    priority=10,
)
