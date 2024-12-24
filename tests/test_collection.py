from __future__ import annotations

import itertools

from octoprobe.lib_tentacle import Tentacle
from octoprobe.util_firmware_spec import FirmwaresBuilt

from testbed.constants import EnumFut
from testbed.multiprocessing.test_bartender import (
    AllTestsDoneException,
    CurrentlyNoTestsException,
    TestBartender,
)
from testbed.tentacle_specs import LOLIN_C3_MINI, LOLIN_D1_MINI, RPI_PICO2
from testbed.testcollection.baseclasses_run import TestRunSpecs
from testbed.testcollection.baseclasses_spec import (
    ConnectedTentacles,
)
from testbed.testcollection.testrun_specs import TestRunSpec


def main() -> None:

    connected_tentacles = ConnectedTentacles(
        [
            Tentacle(
                tentacle_spec=RPI_PICO2,
                tentacle_serial_number="1c4a",
                hw_version="1.0",
            ),
            Tentacle(
                tentacle_spec=RPI_PICO2,
                tentacle_serial_number="1c4b",
                hw_version="1.0",
            ),
            Tentacle(
                tentacle_spec=LOLIN_D1_MINI,
                tentacle_serial_number="1c4c",
                hw_version="1.0",
            ),
            Tentacle(
                tentacle_spec=LOLIN_C3_MINI,
                tentacle_serial_number="1c4d",
                hw_version="1.0",
            ),
        ]
    )

    testrun_specs = TestRunSpecs(
        [
            TestRunSpec(
                label="TESTA",
                helptext="Run perftest on each board.",
                command=["testa.py", "run-perfbench.py"],
                required_fut=EnumFut.FUT_MCU_ONLY,
                required_tentacles_count=1,
            ),
            TestRunSpec(
                label="TESTWLAN",
                helptext="Two boards have to access a AP",
                command=["testwlan.py", "wlantest.py"],
                required_fut=EnumFut.FUT_WLAN,
                required_tentacles_count=2,
            ),
        ]
    )
    testrun_specs.assign_tentacles(
        tentacles=connected_tentacles,
        only_board_variants=None,
        flash_skip=False,
    )

    bartender = TestBartender(
        connected_tentacles=connected_tentacles,
        testrun_specs=testrun_specs,
    )
    print(f"START: test_todo={bartender.tests_todo}")
    for testrun_spec in bartender.testrun_specs:
        print(f"  {testrun_spec!r} tests_todo={testrun_spec.tests_todo}")
        for tsv in testrun_spec.iter_text_tsvs:
            print(f"    tsv={tsv}")

    for i in itertools.count():
        # if i == 10:
        #     break
        try:
            test_run_next = bartender.testrun_next(
                firmwares_built=set(FirmwaresBuilt())
            )
            print(f"{i} test_dbd:{bartender.tests_todo} test_run_next:{test_run_next}")
            for test_run in bartender.actual_testruns:
                print("   ", test_run)
            if len(bartender.actual_testruns) >= 3:
                test_run_done = bartender.actual_testruns[-1]
                print("  test_run_done:", test_run_done)
                bartender.testrun_done(test_run_done)
            if test_run_next is None:
                return
        except CurrentlyNoTestsException:
            print(i, "CurrentlyNoTestsException")
            if len(bartender.actual_testruns) == 0:
                print("DONE")
                break
            test_run_done = bartender.actual_testruns[-1]
            bartender.testrun_done(test_run_done)
            print("  test_run_done:", test_run_done)

        except AllTestsDoneException:
            print("Done")
            for test_run in bartender.actual_testruns:
                print("   ", test_run)
            break


if __name__ == "__main__":
    main()
