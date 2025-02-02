# build-micropython-esp32

This docker image is ment to be used with mpbuild and eventually replace `espressif/idf` in `https://github.com/mattytrentini/mpbuild/blob/main/src/mpbuild/build.py`.

## Links

### Micropython repo

Description on how to set up the toolchain

* https://github.com/micropython/micropython/blob/master/.github/workflows/ports_esp32.yml
* https://github.com/micropython/micropython/blob/master/tools/ci.sh
* https://github.com/micropython/micropython/blob/master/ports/esp32/README.md
* https://docs.espressif.com/projects/esp-idf/en/latest/esp32/get-started/linux-macos-setup.html

This is used in the github ci pipelines.

### Official espressif prebuild docker images

https://hub.docker.com/r/espressif/idf

This image does not work on `ESP32_GENERIC_S3`. Why? It seems to be outdated.

### Official espressif `Dockerfile`

This script uses the official Dockerfiles. These images build micropython successfully.


## Build the container

```bash
./build_image.sh
```
This will build the image and display the command which is required to push to docker hub.
