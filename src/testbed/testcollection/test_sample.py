from __future__ import annotations

import itertools

from testbed.constants import EnumFut
from testbed.testcollection.bartender import (
    AllTestsDoneException,
    TestBartender,
    WaitForTestsToTerminateException,
)
from testbed.testcollection.baseclasses_run import RunSpecContainer
from testbed.testcollection.baseclasses_spec import (
    ConnectedTentacles,
    Tentacle,
    TentacleSpec,
)
from testbed.testcollection.testrun_specs import TestRunSpecSingle, TestRunSpecWlan


def main() -> None:
    spec_pico2w = TentacleSpec(
        board="RPI_PICO2W",
        variants=["default", "RISCV"],
        list_futs=[EnumFut.FUT_MCU_ONLY, EnumFut.FUT_EXTMOD_HARDWARE, EnumFut.FUT_WLAN],
    )
    spec_d1 = TentacleSpec(
        board="LolinD1",
        variants=["default", "Flash512k"],
        list_futs=[EnumFut.FUT_MCU_ONLY, EnumFut.FUT_EXTMOD_HARDWARE, EnumFut.FUT_WLAN],
    )
    spec_c3 = TentacleSpec(
        board="LolinC3",
        variants=["default"],
        list_futs=[EnumFut.FUT_MCU_ONLY, EnumFut.FUT_EXTMOD_HARDWARE, EnumFut.FUT_WLAN],
    )

    connected_tentacles = ConnectedTentacles(
        [
            Tentacle(tentacle_spec=spec_pico2w, serial="AA"),
            Tentacle(tentacle_spec=spec_pico2w, serial="AB"),
            Tentacle(tentacle_spec=spec_d1, serial="AC"),
            Tentacle(tentacle_spec=spec_c3, serial="AD"),
        ]
    )
    testrun_spec_container = RunSpecContainer(
        [
            TestRunSpecSingle(
                subprocess_args=["perftest.py"],
                tsvs_tbt=connected_tentacles.tsvs,
            ),
            TestRunSpecWlan(
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
    else:
        test_bartender = TestBartender(
            connected_tentacles=connected_tentacles,
            testrun_spec_container=testrun_spec_container,
        )
        for i in itertools.count():
            # if i == 10:
            #     break
            print(f"START: test_dbd:{test_bartender.tests_tbd}")
            for testrun_spec in test_bartender.testrun_spec_container:
                print(f"  {testrun_spec!r}")
            try:
                test_run_next = test_bartender.test_run_next()
                print(
                    f"{i} test_dbd:{test_bartender.tests_tbd} test_run_next:{test_run_next}"
                )
                for test_run in test_bartender.actual_runs:
                    print("   ", test_run)
                if len(test_bartender.actual_runs) >= 3:
                    test_run_done = test_bartender.actual_runs[-1]
                    print("  test_run_done:", test_run_done)
                    test_bartender.test_run_done(test_run_done)
                if test_run_next is None:
                    return
            except WaitForTestsToTerminateException:
                print(i, "WaitForTestsToTerminateException")
                if len(test_bartender.actual_runs) == 0:
                    print("DONE")
                    break
                test_run_done = test_bartender.actual_runs[-1]
                test_bartender.test_run_done(test_run_done)
                print("  test_run_done:", test_run_done)

            except AllTestsDoneException:
                print("Done")
                for test_run in test_bartender.actual_runs:
                    print("   ", test_run)
                break

    # list_test_run = TestRuns([TestRun()])
    # connected_tentacles.used("MCU_LOLIN_D1_MINI")
    # test_run = get_next_test(connected_tentacles, list_test_run)


main()
