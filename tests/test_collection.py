from __future__ import annotations

import itertools

from octoprobe.lib_tentacle import Tentacle

from testbed.constants import EnumFut
from testbed.tentacles_spec import (
    tentacle_spec_mcu_lolin_c3_mini,
    tentacle_spec_mcu_lolin_d1_mini,
    tentacle_spec_mcu_rpi_pico2,
)
from testbed.testcollection.bartender import (
    AllTestsDoneException,
    TestBartender,
    WaitForTestsToTerminateException,
)
from testbed.testcollection.baseclasses_run import TestRunSpecs
from testbed.testcollection.baseclasses_spec import (
    ConnectedTentacles,
)
from testbed.testcollection.testrun_specs import TestRunSpec


def main() -> None:

    connected_tentacles = ConnectedTentacles(
        [
            Tentacle(
                tentacle_spec=tentacle_spec_mcu_rpi_pico2,
                tentacle_serial_number="1c4a",
                hw_version="1.0",
            ),
            Tentacle(
                tentacle_spec=tentacle_spec_mcu_rpi_pico2,
                tentacle_serial_number="1c4b",
                hw_version="1.0",
            ),
            Tentacle(
                tentacle_spec=tentacle_spec_mcu_lolin_d1_mini,
                tentacle_serial_number="1c4c",
                hw_version="1.0",
            ),
            Tentacle(
                tentacle_spec=tentacle_spec_mcu_lolin_c3_mini,
                tentacle_serial_number="1c4d",
                hw_version="1.0",
            ),
        ]
    )

    testrun_specs = TestRunSpecs(
        [
            TestRunSpec(
                label="TESTA",
                command="testa.py",
                auxiliary_args=["run-perfbench.py"],
                required_fut=EnumFut.FUT_MCU_ONLY,
                required_tentacles_count=1,
            ),
            TestRunSpec(
                label="TESTWLAN",
                command="testwlan.py",
                auxiliary_args=["wlantest.py"],
                required_fut=EnumFut.FUT_WLAN,
                required_tentacles_count=2,
            ),
        ]
    )
    testrun_specs.assign_tsvs_todo(tsvs=connected_tentacles.tsvs)

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
            test_run_next = bartender.testrun_next()
            print(f"{i} test_dbd:{bartender.tests_todo} test_run_next:{test_run_next}")
            for test_run in bartender.actual_runs:
                print("   ", test_run)
            if len(bartender.actual_runs) >= 3:
                test_run_done = bartender.actual_runs[-1]
                print("  test_run_done:", test_run_done)
                bartender.testrun_done(test_run_done)
            if test_run_next is None:
                return
        except WaitForTestsToTerminateException:
            print(i, "WaitForTestsToTerminateException")
            if len(bartender.actual_runs) == 0:
                print("DONE")
                break
            test_run_done = bartender.actual_runs[-1]
            bartender.testrun_done(test_run_done)
            print("  test_run_done:", test_run_done)

        except AllTestsDoneException:
            print("Done")
            for test_run in bartender.actual_runs:
                print("   ", test_run)
            break


if __name__ == "__main__":
    main()
