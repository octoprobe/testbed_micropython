---
name: micropython-tests
description: >
  Runs tests from the upstream MicroPython test suite (micropython/tests) on a tentacle DUT.
---

# [Skill title]

## Overview

micropython/tests is the directory containing the upstream MicroPython test suite, which includes tests for various MicroPython features and modules.

## When to use this skill

Use this skill when:

- If the user wants to run the upstream MicroPython tests on a tentacle DUT

## Prerequisites

- You need a tentacle with a connected DUT to run the tests on.

## Instructions

1. mpmcp build_and_flash. In the response you will get <dut_usb_serial_port>. Example: `/dev/ttyACM2`.
2. `cd micropython/tests`
3. Run the tests using `run-tests.py  --jobs=1 --trace-output --test-dirs=extmod_hardware --result-dir=...--test-instance=port:<dut_usb_serial_port>`

