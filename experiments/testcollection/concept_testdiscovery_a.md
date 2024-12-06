# Test Discovery A

# Goal

Strategy to run test so that the test run terminates as quick as possible.
* In other words: All tests terminate at the same time.
* In ohter words: All boards with variants have been programmed as view times as possible.

# Concept

## Components

* Terms
  * MpTest: Running a micropython test. For example <micropython-repo>/tests/perf-test.py
    * Every MpTest has a PriorityFactor.
  * TentacleBoard: For example 'RP2_PICO2W', 'LolinC3': Just the board name, no variant.
  * FirmwareSpec: For example 'RP2_PICO2W', 'RP2_PICO2W-RISCV'. Identifies the firmware to be flashed.
  * ConnectedTentacle with a board mounted. Identified by the tentacle serial number.
  * Example of ConnectedTentacles:
    * Tentacle 2346, TentacleBoard='RP2_PICO2W'
    * Tentacle 2347, TentacleBoard='RP2_PICO2W'
    * Tentacle 2348, TentacleBoard='LolinC3'
  * RedundantConnectedTentacle
  * TestRunSpec. Specifies what should be tested, but without assigning ConnectedTentacles. This includes:
      * test to run (perftest.py, wlan-test, basic-test)
      * FirmwareSpec 
  * TestRun. Everything required to run a test. This consists of:
    * n Tentacles
    * For each tentacle:
      * Tentacle serial number
        * TentacleBoard
      * FirmwareSpec
      * portRequired
      * test to run (perftest.py, wlan-test, basic-test)

* TestGenerator
* ListTestsRemaining: Bag with tests to be done
  * Just temporaly
* ListTestsDone: Bag with tests done or running
* PriorityCalculater. Calculates a priority for every TestRun
  * Tentacle with multiple variants: Hi priority if the correct firmware is flashed
  * Tentacle typeTestRunSpec

# Algorithm

```
list_remaining_test_run_specs = generate_specs()
While ConnectedTentacle available:
  if len(list_remaining_test_run_specs) == 0:
      return # We are done
  for test_run_spec in list_remaining_test_run_specs:
    for TestRunSpec in test_run_spec.generate():
      list_testrun = generate_tests(TestRunSpec)
      calculate_priority(list_testrun)
      TestRun = max(list_testrun)
      TestRun.test_run_spec.decrement()
      yield TestRun
```

Problem of above algorithm:
  * Single ConnectedTentacle tests will be selected till they are exhausted. Eventually, more than one ConnectedTentacle will be available and will get a chance to be selected.
  * TestSpec could be: Test 'RP2_PICO2W-RISCV'WLAN_STA againts to other boards. One TestRun would satisfy 1-2 Testspecs! 
