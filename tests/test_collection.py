from __future__ import annotations

import itertools

from octoprobe.lib_tentacle import Tentacle

from testbed.tentacles_spec import (
    tentacle_spec_mcu_lolin_c3_mini,
    tentacle_spec_mcu_lolin_d1_mini,
    tentacle_spec_mcu_rpi_pico2w,
)
from testbed.testcollection.bartender import (
    AllTestsDoneException,
    TestBartender,
    WaitForTestsToTerminateException,
)
from testbed.testcollection.baseclasses_run import RunSpecContainer
from testbed.testcollection.baseclasses_spec import (
    ConnectedTentacles,
)
from testbed.testcollection.testrun_specs import (
    TestRunSpecSingle,
    TestRunSpecWlanAPvsSTA,
)


def main() -> None:

    connected_tentacles = ConnectedTentacles(
        [
            Tentacle(
                tentacle_spec=tentacle_spec_mcu_rpi_pico2w,
                tentacle_serial_number="1c4a",
                hw_version="1.0",
            ),
            Tentacle(
                tentacle_spec=tentacle_spec_mcu_rpi_pico2w,
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
    testrun_spec_container = RunSpecContainer(
        [
            TestRunSpecSingle(
                subprocess_args=["perftest.py"],
                tsvs_tbt=connected_tentacles.tsvs,
            ),
            TestRunSpecWlanAPvsSTA(
                subprocess_args=["wlantest.py"],
                tsvs_tbt=connected_tentacles.tsvs,
            ),
        ]
    )
    if False:
        test_runs = list(
            testrun_spec_container.generate(available_tentacles=connected_tentacles)
        )
        for test_run in test_runs:
            print(test_run)
        return

    bartender = TestBartender(
        connected_tentacles=connected_tentacles,
        testrun_spec_container=testrun_spec_container,
    )
    print(f"START: test_dbd={bartender.tests_tbd}")
    for testrun_spec in bartender.testrun_spec_container:
        print(f"  {testrun_spec!r} tests_tbd={testrun_spec.tests_tbd}")
        for tsv in testrun_spec.iter_text_tsvs:
            print(f"    tsv={tsv}")

    for i in itertools.count():
        # if i == 10:
        #     break
        try:
            test_run_next = bartender.test_run_next()
            print(f"{i} test_dbd:{bartender.tests_tbd} test_run_next:{test_run_next}")
            for test_run in bartender.actual_runs:
                print("   ", test_run)
            if len(bartender.actual_runs) >= 3:
                test_run_done = bartender.actual_runs[-1]
                print("  test_run_done:", test_run_done)
                bartender.test_run_done(test_run_done)
            if test_run_next is None:
                return
        except WaitForTestsToTerminateException:
            print(i, "WaitForTestsToTerminateException")
            if len(bartender.actual_runs) == 0:
                print("DONE")
                break
            test_run_done = bartender.actual_runs[-1]
            bartender.test_run_done(test_run_done)
            print("  test_run_done:", test_run_done)

        except AllTestsDoneException:
            print("Done")
            for test_run in bartender.actual_runs:
                print("   ", test_run)
            break


if __name__ == "__main__":
    main()
