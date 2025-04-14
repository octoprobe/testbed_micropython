# Octoprobe test report

> [!TIP]
> This report will be attached to the MR

* Trigger: PR https://github.com/micropython/micropython/pull/17091

* Execution
  * testbed: ch_hans_1
  * start: 2025-04-18 23:22, 00:23 
  * firmware: https://github.com/micropython/micropython.git@master
  * tests: https://github.com/dpgeorge/micropython@master

* Results: http://octoprobe.org/reports/octoprobe-report-41

## Summary

| Test | error | skipped | passed | failed |
| - | :-: | :-: | :-: | :-: |
| RUN-PERFBENCH | 0 | 3 | 20 | 0 |
| RUN-TESTS_BASICS | 0 | 3 | 50 | **4** |
| RUN-TESTS_NET_INET | 0 | 2 | 30 | **6** |
| RUN-TESTS_EXTMOD_HARDWARE | 0 | 0 | 20 | 0 |

## Failed tests

**Note: Please review below failures - have they be introduced by this MR?**

| Testgroup | Test | Port-Variant | Tentacle | Text | Testresult |
| - | - | - | :-: | - | - |
| TESTS_BASICS | [machine_i2s_rate](https://github.com/micropython/micropython/blob/master/tests/extmod/machine_i2s_rate.py) | ESP32_C3_DEVKIT | b0c30 | - | [testresults.txt](http://octoprobe.org/reports/octoprobe-report-41/RUN-TESTS_BASICS%5b0c30-ESP32_C3_DEVKIT%5d/testresults.txt) |
| RUN-TESTS_EXTMOD_HARDWARE | [machine_pwm](https://github.com/micropython/micropython/blob/master/tests/extmod_hardware/machine_pwm.py) | ESP32_C3_DEVKIT | b0c30 | - | [testresults.txt](http://octoprobe.org/reports/octoprobe-report-41/RUN-TESTS_EXTMOD_HARDWARE%5b0c30-ESP32_C3_DEVKIT%5d/testresults.txt) |

Legend
* error: Test execution failed (error during firmware build, firmware flash)
* skipped: Test marked as skipped
* passed: Test result as expected
* failed: Test result not as expected

