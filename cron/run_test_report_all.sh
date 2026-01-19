#!/usr/bin/env bash

DIRECTORY_CRON="$(dirname "${BASH_SOURCE[0]}")"

"$DIRECTORY_CRON/run_test_report.sh" ~17782
"$DIRECTORY_CRON/run_test_report.sh" @master
