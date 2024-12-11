#
# HOW TO USE
#
# 'cd' into a micropython repo
# and start this script.
#
# If the scripts runs to the end, all firmwares
# could be built successfully
#
set -euox pipefail

export ARGS="--build-container=hmaerki/build-micropython-esp32:v5.2.2"

git clean -fxd; mpbuild build $ARGS ARDUINO_NANO_ESP32 
git clean -fxd; mpbuild build $ARGS ESP32_GENERIC 
git clean -fxd; mpbuild build $ARGS ESP32_GENERIC D2WD
git clean -fxd; mpbuild build $ARGS ESP32_GENERIC OTA
git clean -fxd; mpbuild build $ARGS ESP32_GENERIC SPIRAM
git clean -fxd; mpbuild build $ARGS ESP32_GENERIC UNICORE
git clean -fxd; mpbuild build $ARGS ESP32_GENERIC_C3 
git clean -fxd; mpbuild build $ARGS ESP32_GENERIC_C6 
git clean -fxd; mpbuild build $ARGS ESP32_GENERIC_S2 
git clean -fxd; mpbuild build $ARGS ESP32_GENERIC_S3 
git clean -fxd; mpbuild build $ARGS ESP32_GENERIC FLASH_4M
git clean -fxd; mpbuild build $ARGS ESP32_GENERIC SPIRAM_OCT
git clean -fxd; mpbuild build $ARGS OLIMEX_ESP32_EVB 
git clean -fxd; mpbuild build $ARGS OLIMEX_ESP32_POE
