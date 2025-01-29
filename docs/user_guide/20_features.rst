Features
========

Features to support testing
-----------------------------------------

* Allows to test **by hand**

  Just connect one or more tentacles and run the tests from the micropython repo from the command line against the board on the tentacle.

  For example `tests/run-perfbench.py --pyboard --device=/dev/ttyUSB2`
  or `tests/run-tests.py -t /dev/xxx -d extmod_hardware`.

* Allows to test **ad hoc**
  
  Just connect one tentacle to your computer and run tests on that tentacle.

  For example `mptest test`.

* Allows to test **regressions**
  
  Set up a github runner and connect many tentacles to do automated regessions tests.

* Dynamic number of tentacles
  
  As soon as tentacles are connected via USB, they will be used for the tests.

  Every tentacle is identified by its serial number. A inventory lookup will provide the required information about that tentacle.

* Tab completion

  `mptest test --only-board / --only-test` provide tab completion.

* Timing report
  
  To save time, everything should run in parallel: Building and testing.
  `task_report.md/.txt/.html` summarizes where the time was spent.

* Labels `mptest labels`
  
  The labels in front of every tentacle may be created automatically.

* Current state `mptest list`

  This command shows the connected tentacles and the implemented tests.


Technical features
-----------------------------------------

* Verify flashed firmware

  After flashing a firmware, the strings `sys.version / sys.implementation` are compared against the build result.
  This allows to detect if the wrong firmware was flashed to the wrong tentacle.
  *Nothing is more tedious than testing against the wrong target*!

* One tentacle covering multipe `boards`
  
  For example the `RPI_PICO2_W` supports `FUT_WLAN` and is therefore a superset of `RPI_PICO2`.
  So it would be beneficial to have ONE tentacle to test both.
  I decided not to support this as it would increase overall complexity. The workaround is to solder TWO tentacles which is not very expensive/time consuming and speeds up the tests!

* Journalctl
  
  Some usb errors might pop up in `dmesg` or `Journalctl`. For example limited USB bandwidth.
  `testbed_micropython` starts `journalctl` in the background and terminates loudly when a critical message is detected.

* multiprocessing
  
  The python multiprocessing package is used to allow parallelism. The timeout feature of that package that package is used to recover from blocking which might be caused by a blocking test or mpremote.

* DAQ connector

  Every tentacle provides a 12 pin connector were a DAQ may be connected to spy on the signals.

* Bring boards in to boot mode (programming mode): `mptest debugbootmode`

  Figuring out how to put a board into boot mode is tedious work.
  `mptest debugbootmode` allows to run just that code.
