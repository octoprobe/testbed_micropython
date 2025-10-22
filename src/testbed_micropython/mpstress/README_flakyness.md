# Testresults

### --scenario=NONE --test=RUN_TESTS_ALL

12 tentacles
--> no error!

### --scenario=DUT_ON_OFF --test=RUN_TESTS_ALL

12 tentacles
--> no error!

### --scenario=INFRA_MPREMOTE --test=RUN_TESTS_BASIC_B_INT_POW

12 tentacles
--> error after 20s - sometimes

### --scenario=INFRA_MPREMOTE --test=RUN_TESTS_BASIC_B_INT_POW --stress-tentacle-count=5

5 tentacles
--> no error!

### --scenario=SUBPROCESS_INFRA_MPREMOTE --test=RUN_TESTS_ALL

12 tentacles
--> no error!

### --scenario=SUBPROCESS_INFRA_MPREMOTE_C --test=RUN_TESTS_ALL

12 tentacles
--> no error!

### --scenario=INFRA_MPREMOTE --test=SERIAL_TEST

12 tentacles
--> error after 3s

### --scenario=INFRA_MPREMOTE --test=SERIAL_TEST --stress-tentacle-count=10

10 tentacles
--> error after 1.5s, 2s, 8s

### --scenario=INFRA_MPREMOTE --test=SERIAL_TEST --stress-tentacle-count=7

7 tentacles
--> error after 8s, 14s, 26s

### --scenario=INFRA_MPREMOTE --test=SERIAL_TEST --stress-tentacle-count=6

6 tentacles
--> no error!

### --scenario=INFRA_MPREMOTE --test=SIMPLE_SERIAL_WRITE

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


### --scenario=INFRA_MPREMOTE --test=SIMPLE_SERIAL_WRITE --stress-tentacle-count=8

8 tentacles
--> error after 9s, 19s

### --scenario=INFRA_MPREMOTE --test=SIMPLE_SERIAL_WRITE --stress-tentacle-count=7

7 tentacles
--> error after 5s, 25s

### --scenario=NONE --test=SIMPLE_SERIAL_WRITE

12 tentacles
--> no error
