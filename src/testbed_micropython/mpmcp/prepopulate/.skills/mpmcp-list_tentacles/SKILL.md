---
name: mpmcp-query
description: >
  Queries the octoprobe testbed via the mpmcp MCP server to discover connected tentacles and their status.
---

# [Skill title]

## Overview

This skill allows the user to query the octoprobe testbed to identify connected tentacles, their board types, power states, and DUT serial ports. The outcome is a comprehensive view of the current testbed status, enabling informed decisions for further actions.


## When to use this skill

Use this skill when:

- The user needs to get an overview of the current testbed status, including connected tentacles, their board types, power states, and DUT serial ports.
- The user wants to run tests on specific tentacles.
  

## Prerequisites

- The required tentacles must be connected.
- If the user asks for a tentacle which is not connected, you must tell the user to get the required tentacle and connect it.


# JSON-Response Structure

## mcmcp: list_tentacles

Example of a tentacle:

```json
{
    "tentacle_label": "4721-ESP32_C5_DEVKIT",
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