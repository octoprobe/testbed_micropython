# Tests for mpbuild

These tests have to be started manually.

The tests succeeded if they do not throw an exception and run till the end.
These tests make mpbuild building various firmwares.
It is a end to end test: So it tests the mpbuild-api and that all docker containers build a firmware.

## Testing the command line interface `mpbuild build`:

```bash
export MICROPY_DIR=~/micropython_firmware
./tests/test_build_some_variants.sh
```

## Testing the API

```bash
export MICROPY_DIR=~/micropython_firmware
python tests/test_build_board_for_each_port.py
python tests/test_build_some_variants.py
```
