# Use cron to run octoprobe

Links

 * https://cronitor.io/guides/cron-jobs
 * https://crontab.guru/

## Setup

Login as `githubrunner`

```bash
crontab -e

# m h dom mon dow   command
0 20 * * * cd ~/testbed_micropython && ./cron/run_test_report_all.sh >> ~/testbed_micropython/cron/cron_log.txt 2>&1
```

## Debugging

```bash
tail -f ~githubrunner/testbed_micropython/cron/cron_log.txt

journalctl -t CRON | tail
```