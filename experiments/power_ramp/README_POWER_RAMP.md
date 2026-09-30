# POWER RAMP

## Goal

ESP32 boards sometimes do not start. This has been observed on ESP32_C3_DEVKIT, ESP32_C5_DEVKIT, ESP32_S2_DEVKIT.

Simple solution: Know how to power up ESP32 boards correctly
Comples solution: Control ESP32-reset/ESP32-PO to support Power up

## Links

* ESP32_C5_DEVKIT
  * https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32c5/esp32-c5-devkitc-1/index.html
  * [Pinout](https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32c5/_images/esp32-c5-devkitc-1-pin-layout_v1.2.png)
  * [Schematic](https://dl.espressif.com/dl/schematics/SCH_ESP32-C5-DevkitC-1_V1.2_20250211.pdf)
  * [Datasheet](https://www.espressif.com/sites/default/files/documentation/esp32-c5_datasheet_en.pdf)

  * Pins
    * RST, input, CHIP_PU.
      * chip pin: 
      * connected with SW2
      * 10kOhm, 1uF: tau=10ms
    * Boot
      * chip pin: GPIO28
      * connected with SW1

  * Datasheet
    * Chip boot mode: Strapping pins: GPIO26, GPIO27, and GPIO28

    | Strapping Pin | Default Configuration | Bit Value |
    | - | - | - |
    | GPIO0 | Weak pull-up| 1 |
    | GPIO25 | Floating | – |
    | GPIO26 | Floating | – |
    | GPIO27 | Pull-up | 1 |
    | GPIO28 | Pull-up | 1 |
    | GPIO7 | Floating | – |
    | MTMS | Floating | – |
    | MTDI | Floating | – |

    * Chip Boot Mode Control: GPIO26, GPIO27, and GPIO28 control the boot mode after the reset is released

* ESP32_S2_DEVKIT
  * https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32s2/esp32-s2-devkitc-1/index.html
  * [Pinout](https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32s2/_images/esp32-s2-devkitc-1-v1-pinout.png)
  * [Schematic](https://dl.espressif.com/dl/schematics/esp-idf/SCH_ESP32-S2-DEVKITC-1_V1_20220817.pdf)
  * [Datasheet](https://www.espressif.com/sites/default/files/documentation/esp32-s2_datasheet_en.pdf)

  * Pins
    * RST, input, CHIP_PU.
      * chip pin: EN
      * connected with SW2
      * 10kOhm, 1uF: tau=10ms
    * Boot
      * chip pin: GPIO0
      * connected with SW1
      * no pull up/down

  * Datasheet
    * Chip boot mode: Strapping pins: GPIO0 and GPIO46

    | Strapping Pin | Default Configuration | Bit Value |
    | - | - | - |
    | GPIO0 | Weak pull-up| 1 |
    | GPIO45 | Weak pull-down|  0 |
    | GPIO46 | Weak pull-down|  0 |

## Questions

...

## Measuring concept

* Components
  * PC: Linux PC
    * No software required on Linux PC
  * AD3: Digilent Discovery 3
  * ESP32: Any ESP32 board
  * USB: A USB Micro Male to USB C Male cable where USB5V is detached

* Connections
  * PC: USB cable <=> ESP32-D+/D-
  * AD3 digital in <= ESP32-D+/D-
  * AD3 analog in <=> ESP32-RST
  * AD3 analog in <=> ESP32-Boot
  * AD3 supply+ => ESP32-VCC

* VCC ramp test
  * Stimuli
    * AD3: ESP32-VCC ramp
    * AD3: Measure ESP32-RST, ESP32-Boot, ESP32-D+
  * Expected
    * ESP32-D+ communication

  + Vary over ESP32 boards and VCC ramps/power cycles


* Expected conclusions

  * Does D+/D- power the ESP32 chip so I can not powercycle?
  * What VCC Ramps will fail to start ESP32.
  * How do different ESP32 behave - production tolerances...

## Netlist

### USB Cable

| Part/Pin | Part/Pin | Function | Female jumper wire |
| - | - | - | - |
| USB-Micro/Gnd | USB-A/Gnd | Common GND | USBblack |
| USB-Micro/D+ | USB-A/D+ | D+ | USBgreen |
| USB-Micro/D- | USB-A/D | D- | USBwhite |
| USB-Micro/VCC | not connected | VCC | USBred |

### AD3

| Part/Pin | Part/Pin | Function |
| - | - | - |
| AD3/GROUND | USBblack | Common GND
| AD3/V+ | USBred | USB Power 5V |
| AD3/0 | USBwhite | USB D- |
| AD3/1 | USBgreen | USB D+ |
| AD3/Scope 1 neg | AD3/GROUND | Common GND |
| AD3/Scope 2 neg | AD3/GROUND | Common GND |
| AD3/Scope 1 pos | ESP32-RST | RST |
| AD3/Scope 2 pos | ESP32-Boot | Boot |

### ESP32-C5 DevKitC

[Guide](https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32c5/esp32-c5-devkitc-1/user_guide.html)
[pinout](https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32c5/_images/esp32-c5-devkitc-1-pin-layout_v1.2.png)
[schematics](https://dl.espressif.com/dl/schematics/SCH_ESP32-C5-DevkitC-1_V1.2_20250211.pdf)

| Function | pin | Silkscreen | Schematics |
| - | - | - | - |
| RST | J1-pin2 | RST | CHIP_PU, ESP32-EN |
| Boot | J3-pin11 | 28 | GPIO28 |
