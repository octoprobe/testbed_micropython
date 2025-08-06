set -euox pipefail

docker build . --tag octoprobe-testbed_micropython

mkdir -p $HOME/docker_octoprobe


# Mounts
export PARAMS_MOUNTS="\
  --env HOME=/tmp \
  -v $HOME/docker_octoprobe:/docker_octoprobe \
  -v $(pwd):$(pwd) \
  -w $(pwd) \
  "

# journalctl
export PARAMS_JOURNALCTL="\
  -v /var/log/journal:/var/log/journal \
  -v /run/log/journal:/run/log/journal \
  -v /etc/machine-id:/etc/machine-id \
  "

# pyudev
export PARAMS_PYUDEV="\
  --cap-add=NET_ADMIN \
  --net=host \
  --pid=host \
  -v /run/udev:/run/udev \
  "

# user&groups
export PARAMS_USER="\
  --user $(id -u):$(id -g) \
  $(id -G | awk '{for(i=1;i<=NF;i++) print "--group-add " $i}') \
  "

# passwd
export PARAMS_PASSWD="\
  -v /etc/passwd:/etc/passwd:ro \
  -v /etc/group:/etc/group:ro \
  -v /etc/shadow:/etc/shadow:ro \
  -v /etc/sudoers:/etc/sudoers:ro \
  "

# USB devices
export PARAMS_USB="\
  --device /dev/bus/usb \
  -v /dev/bus/usb:/dev/bus/usb \
  -v /sys/bus/usb:/sys/bus/usb \
  "

# TTY/UART
export PARAMS_TTY="\
  -v /dev:/dev \
  "

# Docker in Docker (DinD)
export PARAMS_DOCKER_IN_DOCKER="\
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v $(which docker):/usr/bin/docker \
  "

docker run --rm -it \
  $PARAMS_MOUNTS \
  $PARAMS_USER \
  $PARAMS_PASSWD \
  $PARAMS_USB \
  $PARAMS_JOURNALCTL \
  $PARAMS_PYUDEV \
  $PARAMS_TTY \
  $PARAMS_DOCKER_IN_DOCKER \
  octoprobe-testbed_micropython

# removed
#   --privileged \
