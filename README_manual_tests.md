# Manual tests

These manual tests allow to verify the functionality of `testbed_micropython`.

## Group: Flash

### repl blocks

* Precondition: RPI_PICO flashed with https://github.com/gusmanb/logicanalyzer
* Stimuli: Start test
* Expected: RPI_PICO must be correctly reprogrammed

### USB connection missing

* Precondition: DUT disconnected
* Stimuli: Start test
* Expected: Test fails with message 'is USB connected?'

### Firmware which conflicts with mpremote

Rationale:
mpremote expects the firmware respond. However, not micropython firmware does not respond to mpremote.
This tests should provoke a timeout in mpremote which then should install the micropython firmware.

* Precondition: Flash firmware and connect tentacle
* Stimuli: Start test
* Expected: Micropython firmware could successfully be flashed

Conflicting firmwares are:
* ESP32: https://rainmaker.espressif.com
* RP2: https://github.com/raspberrypi/debugprobe/releases/tag/debugprobe-v2.2.0

## Group: TestBartender

### Only 1 tentacle with FUT_WLAN

* Stimuli: Start test
* Expected: test is not executed

### Two RPI_PICO2_W

* Stimuli: Start test with FUT_WLAN
* Expected: The test is only run on 1 tentacle

### Two RPI_PICO2_W

* Stimuli: Start test with FUT_EXTMOD_HARDWARE
* Expected: The test is only run on 1 tentacle

## Group: git clone

There are many different situations in cloning git.

See: `src/octoprobe/util_cached_git_repo.py: # Git specs to be used for manual testing`.

Test all above combinations for success.

Test error conditions for:
* Tag not found.
* Commit not found.
* Rebase failed.