# Reporting

## Big Picture

* A MR triggers a test run.
* When done, the testresults are pushed to https://reports.octoprobe.org
* When done, the summary report is attached to the MR

## Summary report

[octoprobe_summary_report.md](./octoprobe_summary_report.md)

## Implementation

### Existing result files - created by `run-tests.py`:

  * [RUN-TESTS_STANDARD-xxx/testresults.txt](subreports/testresults.txt) [#41](http://octoprobe.org/reports/octoprobe-report-41/RUN-TESTS_STANDARD%5b0c30-ESP32_C3_DEVKIT%5d/testresults.txt)
  * [RUN-TESTS_STANDARD-xxx/_results.json](subreports/_results.json)


### New result files - created by `mptest`:

```json
// ./context.json
{
  "testbed": "ch_hans_1",
  "time_start": "2025-04-18 23:22:12",
  "time_end": "2025-04-18 23:43:14",
  "ref_firmware": "https://github.com/micropython/micropython.git@master",
  "ref_tests": "https://github.com/dpgeorge/micropython@master",
  "trigger": "https://github.com/micropython/micropython/pull/17091",
  // "backlink": "https://github.com/micropython/micropython/pull/17091#issuecomment-2784673205",
}
```


```json
// ./RUN-xxx/context_test.json
{
  "testgroup": "RUN-TESTS_STANDARD",
  "tentacle": "b0c30",
  "port-variant": "ESP32_C3_DEVKIT",
  "time_start": "2025-04-18 23:22:12",
  "time_end": "2025-04-18 23:43:14",
  "log_output": "logger_20_info.log",
  "results" [
    {
      "name": "basics/async_for.py",
      "result": "pass",
    },
    {
      "name": "machine_i2s_rate",
      "result": "fail",
      "text": "Why the test failed...",
    },
    {
      "name": "perf_bench/core_yield_from.py",
      "result": "pass",
      "text": "71705.62 0.0048 278.92 0.0048",
    }
  ]
}
```

### Reporting

After all tests have been processed

* Collect `./context.json`
* Collect all `./RUN-xxx/context_test.json` and `./RUN-xxx/_results.json`

* Create [octoprobe_summary_report.md](octoprobe_summary_report.md)

* Push testresults to https://reports.octoprobe.org
* Attach `octoprobe_summary_report.md` to MR.

## https://reports.octoprobe.org

* static website
* Allow `ch_hans_1`, `au_damien_1` to https-push the testresults.
* dynamic reporting (allure, own reports) might be added later.

## Open Questions

* [ ] All reports (created by ch_hans_1, au_damien_1) will be pushed to https://reports.octoprobe.org.
  * Manuall started tests will remain locally and will not be archived.

* [ ] Define how to trigger/start the tests:
  * By MR github action
  * By any developer similar as in [Run workflow](https://github.com/octoprobe/testbed_micropython_runner/actions/workflows/testbed_micropython.yml)
  * By a script/workflow scanning all open MR.

* [ ] Limit tests by files which have changed. See as example [ports_esp8266.yml](https://github.com/micropython/micropython/blob/master/.github/workflows/ports_esp8266.yml#L7-L14)
* [ ] How to know which files have been changed?

* [ ] Avoid secrets to enter testresults
* [ ] How to link tests to the corresponding repo/commit? Example: [machine_i2s_rate](https://github.com/micropython/micropython/blob/master/tests/extmod/machine_i2s_rate.py)

* [x] Base Line
  * Not implemented yet (could be done the same way as code-size-report).
  * We assume that all tests on the baseline pass.
