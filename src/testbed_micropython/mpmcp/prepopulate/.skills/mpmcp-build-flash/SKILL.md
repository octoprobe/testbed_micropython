---
name: mpmcp-build-flash
description: >
  How to use the mpmcp 'build_and_flash' tool to build MicroPython firmware and flash it onto a tentacle DUT.
---

# [Skill title]

## Overview

You should not build the firmware on your on. Always use the mpmcp 'build_and_flash' tool to handle the build and flashing process.

## When to use this skill

Use this skill when:

- The user needs to test a certain commit of the MicroPython firmware on a certain tentacle.


## Prerequisites

- The correct commit has been checked out in the MicroPython repository.

## Instructions

- Often you have to build to be able to run tests. When running tests on multiple tentacles please maintain this order: Build, flash and test the first tentacle. Now move to the second tentacle.

- The resulting json file has to important fields:

```json
  "outcome_error": "TransportError('failed to access /dev/ttyACM15')",
  "outcome_success": false
```

You must stop processing if `"outcome_success": false`!
