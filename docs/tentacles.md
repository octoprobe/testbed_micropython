# Tentacles

Priority: Board

* High: RP2_PICO2W
* Done: LolinC3
* Low: LolinD1 

## Tentacle RP2_PICO2W

[Datasheet](https://www.raspberrypi.com/documentation/microcontrollers/pico-series.html#raspberry-pi-pico-2-w24)

FUTS: WLAN_STA, WLAN_AP, BLE

Connections

* Bootmode
  * Board TP6 (Bootsel) <>=> Tentacle Relay 1d
  * Tentacle Relay 1a <=> Tentacle GND

* Board Power
  * Board GND <=> Tentacle GND

* FUT_EXTMOD_HARDWARE
  * Board GPIO0 <=> Board GPIO1