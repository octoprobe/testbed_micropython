# Running octoprobe / testbed_micropython in a docker container

Current state: Most of the mechanisms work but not usable yet!

Current errors are:
* Access of USB-uart: `mpremote.transport.TransportError: failed to access /dev/ttyACM0`
* Communication using `mpremote`: `octoprobe.util_baseclasses.OctoprobeAppExitException: Tentacle INFRA 1722-RPI_PICO: Failed to control relays: OSError(5, 'Input/output error')`

**Conclusion:** Even if it seems feasable to be able to run octoprobe in a container, the complexity is high! I would recommend not to use containers...

## Features

* Same user/groups on host and container
* Same directory path on host and container
* uv:
  * The container has `uv` installed, but nothing from octoprobe!
  * The octoprobe hooks are the scripts `uv_mpbuild`, `uv_op`, and `uv_mptest`. These scripts will use uv to clone the corresponding repos and run it.
* python
  * These commands are installed into the container `mpbuild`, `op` and `mptest`.

### Mounts

| Host | Container | Comment |
| - | - | - |
| ~/docker_octoprobe | /docker_octoprobe | Cache for octoprobe and uv |
| pwd | pwd | Work directory |
| - | $HOME | The homedirectory in the container is /tmp |

## Starting the container

```bash
./docker_rebuild_start.sh 
```

## commands within the container

The following command should behave the same within and outside of the container

```bash
$ uv tool run --from pyserial pyserial-ports

$ journalctl --follow

$ op query

$ op udev

Connect/disconnect USB devices and watch the output.

$ mpbuild list

$ mptest list
```

Final test:

```bash
$ cd micropython # A directory with the micropython repo
$ mptest test --only-test=RUN-TESTS_EXTMOD_HARDWARE
```