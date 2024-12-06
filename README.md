Welcome to the testbed_micropython wiki!

# Background

* There are many tests in https://github.com/micropython/micropython/tree/master/tests.

  * These tests require one board to be connected to the computer and will take about 15min per board.
  * WLAN: tentacle(AP) <-> tentacle(STA)
  * WLAN: tentacle(STA) <- AP -> tentalce(STA)
  * So testing 16 boards will take about 4h.

* Release testing

  * To release a new version of micropython, all above tests should succeed.
  * This is a lot of manual work!

# Main usecase

  * The aim of `testbed_micropython` is to automate these tests.
  * Minimalize flakeness.
  * Minimalize the need for manual interaction to keep the infrastructure running.
  * Be able to run multiple test instances to distribute knowledge, workload.

* Flexibility

  * `OctoprobeGithubAction`: The tests should be triggered by github actions and the testresults returned to github.
    * This will include powercycling and flashing of the MCUs.
  * `OctoprobeCL`: The tests may be started from the command line.
    * This will include powercycling and flashing of the MCUs.
  * `OctoprobeNone`: Test may run against a connected tentacle or Board withoug involving octoprobe.
    * This will NOT powercycle nor flash the MCUs. It is assumed, the the firmware was flashed previously by hand.

# Implementation

* No pytest:
  * As the tests should run in parallel, pytest might not be able the complexity.

* Implement new testrunner:
  * Which allows to run the tests for every tentacle in parallel.
    * Goal: Time for testing is constant: Test 1 tentacle will require the sime time a 10 tentacles.
    * Every parallel test have to be able to filter the udev event on the very same target.
  * We use asyncio to implement parallelism. Exceptions to this are:
    * The tests are based on mpremote which in NOT asyncio: Every test will run in its own thred (subprocess).
    * The flashing (picotool, esptool, dfu-util) will run in there own thread (subprocess).
  * The testrunner is in the PATH and have to be called from a `micropython-repo>/test` folder.
  * A parameter to the testrunner allows to specify a testdirectory/testfile.

* Tentacles
  * The tentacles will NOT use the octobus (the 40 pin connector). So tests are MCU only.
  * However the design should allow to make use of the octobus later.
  * As the tentacles will only require minimal connections to be soldered (ground and connecting two pins on the MCU), it will take only 15min to solder a tentacle.
   
* first `testbed_micropython` instances
  * au_dpgeorge_1: Run by @dpgeorge
  * ch_maerki_1: Run by @hmaerki

* `testbed_micropython` layering
  * Layering: octoprobe <- testbed_micropython <- testbed_tutorial
  * Summary of each layer:
    * octoprobe: Communication to the tentacles, usb hubs.
      * May be used to test micropython, circuitpython, zephyr, arduino.
    * testbed_micropython:
      * Includes flashing of all micropython boards and allows to run `<micropython-repo>/tests`.
      * Non pytest testrunner allow parallel testing.
    * testbed_tutorial:
      * Reuses flashing mechanisms from `test_micropython`.
      * Adds pytest.
      * Multi tentacle tests (MCU, devices, DAQ) using the octobus. 
