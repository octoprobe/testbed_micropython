## Set up environment

Recommended workflow.

Create directory structure

* `<mpmcp_top>` Topfolder where the agent has access to
* `<mpmcp_top>/micropython` A clone of https://github.com/micropython/micropython.git
* `<mpmcp_top>/log/mpbuild` The build log files
* `<mpmcp_top>/log/flash` The flashing log files


## mcmcp: list_tentacles

Example of a tentacle:

```json
{
    "label": "4721-ESP32_C5_DEVKIT",
    "tentacle_serial_number": "e4641448133b-4721",
    "tentacle_spec_board": "ESP32_GENERIC_C5",
    "tentacle_spec_build_variants": [""],
    "tentacle_spec_doc": "...",
    "tentacle_spec_tags": "board=ESP32_GENERIC_C5,mcu=esp32,programmer=esptool,tier=1",
    "tentacle_spec_futs": [
        "FUT_MCU_ONLY",
        "FUT_EXTMOD_HARDWARE",
        "FUT_WLAN",
        "FUT_BLE"
    ],
    "tentacle_state_last_firmware_flashed": null,
    "infra_usb_location": "0",
    "infra_usb_serial_port": "/dev/ttyACM1",
    "probe_usb_location": "0",
    "probe_usb_serial_port": null,
    "dut_usb_location": "3-6.2.3",
    "dut_usb_serial_port": "/dev/ttyACM2"
},
```

Relevant entries

* tentacle_serial_number
  Unique identification of the tentacle
* tentacle_spec_board, tentacle_spec_build_variants
  May be used to build the firmware. `mpbuild <tentacle_spec_board> <tentacle_spec_build_variants>`. Example `mpbuild build RPI_PICO2 RISCV`. 

  The board definition may be found with `find <micropython_repo> -name <tentacle_spec_board>`. Example `find . -name RPI_PICO2`.
 
* tentacle_spec_futs
  Feature under test

## Compile the firmware using mpbuild

## mcmcp: Compile and flash

...

## Start mptest

`mptest --only-board=<tentacle_spec_board>-<tentacle_spec_build_variants>`. Example `mptest --only-board=RPI_PICO2-RISCV`. Default variant: `mptest --only-board=RPI_PICO2`.

Important: You can not specify the tentacle by serial number. `mptest` will find a matching tentacle.

## Connect to a board

`mpremote connect <dut_usb_serial_port>`. Example `mpremote connect /dev/ttyUSB0`.

Use `mpmcp:list_tentacles` to make sure the serial port is visible.

## Powercycling a crashed board

