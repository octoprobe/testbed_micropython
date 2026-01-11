# Testresults

### --stress_scenario==NONE --test=RUN_TESTS_ALL

12 tentacles
--> no error!

### --stress_scenario==DUT_ON_OFF --test=RUN_TESTS_ALL

12 tentacles
--> no error!

### --stress_scenario==INFRA_MPREMOTE --test=RUN_TESTS_BASIC_B_INT_POW

12 tentacles
--> error after 20s - sometimes

### --stress_scenario==INFRA_MPREMOTE --test=RUN_TESTS_BASIC_B_INT_POW --stress-tentacle-count=5

5 tentacles
--> no error!

### --stress_scenario==SUBPROCESS_INFRA_MPREMOTE --test=RUN_TESTS_ALL

12 tentacles
--> no error!

### --stress_scenario==SUBPROCESS_INFRA_MPREMOTE_C --test=RUN_TESTS_ALL

12 tentacles
--> no error!

### --stress_scenario==INFRA_MPREMOTE --test=SERIAL_TEST

12 tentacles
--> error after 3s

### --stress_scenario==INFRA_MPREMOTE --test=SERIAL_TEST --stress-tentacle-count=10

10 tentacles
--> error after 1.5s, 2s, 8s

### --stress_scenario==INFRA_MPREMOTE --test=SERIAL_TEST --stress-tentacle-count=7

7 tentacles
--> error after 8s, 14s, 26s

### --stress_scenario==INFRA_MPREMOTE --test=SERIAL_TEST --stress-tentacle-count=6

6 tentacles
--> no error!

### --stress_scenario==INFRA_MPREMOTE --test=SIMPLE_SERIAL_WRITE

`mpstress --stress_scenario==INFRA_MPREMOTE --test=SIMPLE_SERIAL_WRITE --tentacle=5f2c --micropython-tests=/home/octoprobe/gits/micropython`

12 tentacles
--> error after 4s
    006000: 197kBytes/s
    ERROR, read_duration_s=1.001166s
        expected: b'_ABCDEFGHIJKLMNOPQRSTUVWXYabcdefghijklmnopqrstuvwxy1234567890_'
        received: b'_ABCDEFGHIJKLMNOPQRSTUVWXYabcdefghijklmnopqrstuvwxy123456789'
        try reading again: b'' read_duration_s=1.001263s

    # Debug output from serialposix.py:
    read(6(6)) duration=0.000011s
    [4] = select(1.000s) duration=0.000018s
    read(44(62)) duration=0.000010s
    [] = select(1.000s) duration=1.000669s
    TIMEOUT!
    ERROR, read_duration_s=1.000970s
    expected: b'_ABCDEFGHIJKLMNOPQRSTUVWXYabcdefghijklmnopqrstuvwxy1234567890_'
    received: b'_ABCDEFGHIJKLMNOPQRSTUVWXYabcdefghijklmnopqr'
    [] = select(1.000s) duration=1.000536s
    TIMEOUT!
    try reading again: b'' read_duration_s=1.008089s


### --stress_scenario==INFRA_MPREMOTE --test=SIMPLE_SERIAL_WRITE --stress-tentacle-count=8

8 tentacles
--> error after 9s, 19s

### --stress_scenario==INFRA_MPREMOTE --test=SIMPLE_SERIAL_WRITE --stress-tentacle-count=7

7 tentacles
--> error after 5s, 25s

### --stress_scenario==NONE --test=SIMPLE_SERIAL_WRITE

12 tentacles
--> no error



### --stress_scenario==INFRA_MPREMOTE --test=SIMPLE_SERIAL_WRITE

==> 5f2c connected to RHS B7
`mpstress --stress_scenario==INFRA_MPREMOTE --test=SIMPLE_SERIAL_WRITE --tentacle=5f2c --micropython-tests=/home/octoprobe/gits/micropython`

12 tentacles
--> error after 4s

==> 5f2c connected to USB on computer rear

`mpstress --stress_scenario==INFRA_MPREMOTE --test=SIMPLE_SERIAL_WRITE --tentacle=5f2c --micropython-tests=/home/octoprobe/gits/micropython`

12 tentacles
--> error after 120s, 35s
--> no error 340s, 340s


## How to run test with ftrace

* tty_open: https://github.com/torvalds/linux/blob/master/drivers/tty/tty_io.c#L467

```bash
sudo chmod a+w /sys/kernel/tracing/trace_marker
cd /tmp/ftrace
sudo trace-cmd record -p function_graph \
  -l tty_open \
  -l tty_poll \
  -l tty_release \
  -l tty_read \
  -l tty_write \
  -l usb_serial_open \
  -l acm_open
```

```bash
mpstress --micropython-tests=/home/octoprobe/work_octoprobe/micropython --stress-scenario=NONE --test=SIMPLE_SERIAL_WRITE --stress-tentacle-count=99 2>&1 | tee > ./src/testbed_micropython/mpstress/ftrace/mpstress.log
```

```bash
trace-cmd report
```
