# Use cron to run octoprobe

Links

 * https://cronitor.io/guides/cron-jobs
 * https://crontab.guru/

## Setup

Login as `githubrunner`

The test should start at 00:00 melbourne time. This is 14:00 swiss time.

```bash
crontab -e

# m h dom mon dow   command
0 14 * * * cd /home/githubrunner/testbed_micropython && /home/githubrunner/testbed_micropython/cron/run_test_report_all.sh >> /home/githubrunner/testbed_micropython/cron/cron_log.txt 2>&1
```

## Debugging

Crontab file

```bash
cat /var/spool/cron/crontabs/githubrunner

crontag -l # list user's crontab
```

Test command


```bash
env -i /bin/bash --noprofile --norc
<-- here goes to cron-command
```

Observer running jobs

```bash
tail -f ~githubrunner/testbed_micropython/cron/cron_log.txt

journalctl -t CRON | tail
```
