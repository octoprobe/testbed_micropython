---
name: mpremote
description: >-
  How to use the mpremote tool to connect to a tentacle DUT and manage it, including powercycling and flashing firmware.
---

# Connect with mpremote

## Connect to a board

`mpremote connect <dut_usb_serial_port>`. Example `mpremote connect /dev/ttyUSB0`.

Use `mpmcp:list_tentacles` to make sure the serial port is visible.
