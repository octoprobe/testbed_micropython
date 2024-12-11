# Current state 2024-12-15

* testbed_showcase (ex. tutorial). Uses octobus.
* testbed_micropython. NO octobus.

## Used case Damien

```bash
  cd into microptyhon folder
  mpremote
  mpbuild
  mptest
```

* Connect 1 board for single tests
* Connect 2 boards for multiple tests
  
* Build firmware
* Flash boards
* Start test
  
### Use with mptest

* Usecase github
  * mptest without parameter
    * Query tentacles
    * Build all firmware using mpbuild
    * Run all tests on all tentacles using all variants
    
* Usecase: Damien is fixing tests
  * mptest --flash-only
  * mptest --flash-skip
  
* Usecase: Damien is floating point on fixing RP_PICO2-RISCV
  * mptest --only-board-variant=RP_PICO2-RISCV --only-test RUN-TEST_BASIC

## mptest

* NO pytest
* can run all tentacles in parallel
* mptest list
* parameter completion
  
## Eventually
* 20 tentacles in Geelong and CH
* all tests in parallel
* NO pytest
*NO octobus

## Ordered 50 Tentacles
* 40 pin connector NOT assembled
* sigrok plug
* Bolzone due

## Next Tentacle Version
* Copper free zones for antennas.
* Add Raspberry Pi Debug Probe
