FROM python:3.13.5-slim-bookworm
# FROM debian:bookworm-slim

WORKDIR /work_octoprobe
RUN chmod a+rwx /work_octoprobe

RUN apt-get update && \
    apt-get install -y systemd \
    libusb-1.0-0 libusb-1.0-0-dev \
    net-tools iproute2 iputils-ping usbutils \
    sudo git && \
    apt-get autoremove -y && \
    rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY ./support_files/bin /bin/

ENV UV_CACHE_DIR=/docker_octoprobe/uv_cache
ENV OCTOPROBE_DOWNLOADS=/docker_octoprobe/octoprobe_downloads

RUN python3 -m pip install --break-system-packages git+https://github.com/octoprobe/testbed_micropython.git

ENTRYPOINT ["/bin/bash"]