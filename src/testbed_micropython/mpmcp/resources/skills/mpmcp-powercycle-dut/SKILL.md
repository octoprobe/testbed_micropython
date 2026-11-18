---
name: mpmcp-powercycle-dut
description: >
  Powercycles the DUT on the tentacle given by serial.
---

# [Skill title]

## Overview

Powercycles the DUT on the tentacle given by serial.

## When to use this skill

Use this skill when:

- The DUT may crash if some micropython code made it crash. So the `dut_serial_port` is lost. In this case, powercycling the DUT most probably will recover it.
  
