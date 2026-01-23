# Use cron to run octoprobe

Links

 * https://cronitor.io/guides/cron-jobs
 * https://crontab.guru/

## Setup

Login as `githubrunner`

```bash
crontab -e

# m h dom mon dow   command
0 20 * * * cd /home/githubrunner/testbed_micropython && /home/githubrunner/testbed_micropython/cron/run_test_report_all.sh >> /home/githubrunner/testbed_micropython/cron/cron_log.txt 2>&1
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
