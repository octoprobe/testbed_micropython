from __future__ import annotations

import dataclasses
import logging
import os
import time

import serial
import typer
import typing_extensions

from testbed_micropython.mpstress.util_stress import print_fds

logger = logging.getLogger(__file__)

# 'typer' does not work correctly with typing.Annotated
# Required is: typing_extensions.Annotated
TyperAnnotated = typing_extensions.Annotated

# mypy: disable-error-code="valid-type"
# This will disable this warning:
#   op.py:58: error: Variable "octoprobe.scripts.op.TyperAnnotated" is not valid as a type  [valid-type]
#   op.py:58: note: See https://mypy.readthedocs.io/en/stable/common_issues.html#variables-vs-type-aliases

app = typer.Typer(pretty_exceptions_enable=False)

CHARS = b"_ABCDEFGHIJKLMNOPQRSTUVWXYabcdefghijklmnopqrstuvwxy1234567890_"

MICROPYTHON_SCRIPT = """
# Based on
# <micropython>/tests/serial_test.py: read_test_script

import sys

CHARS = b"_ABCDEFGHIJKLMNOPQRSTUVWXYabcdefghijklmnopqrstuvwxy1234567890_"

def send_alphabet(count):
    for i in range(count):
        sys.stdout.buffer.write(CHARS)
        sys.stdout.buffer.write(f"{i:06d}")

send_alphabet(count=<COUNT>)
"""


class TestError(Exception):
    pass


@dataclasses.dataclass(repr=True, frozen=True)
class SimpleSerialWrite:
    serial: serial.Serial

    def drain_input(self) -> None:
        time.sleep(0.1)
        while self.serial.inWaiting() > 0:  # type: ignore[attr-defined]
            _data = self.serial.read(self.serial.inWaiting())  # type: ignore[attr-defined]
            time.sleep(0.1)

    def send_script(self, script: bytes) -> None:
        assert isinstance(script, bytes)
        chunk_size = 32
        for i in range(0, len(script), chunk_size):
            self.serial.write(script[i : i + chunk_size])
            time.sleep(0.01)
        self.serial.write(b"\x04")  # eof
        self.serial.flush()
        response = self.serial.read(2)
        if response != b"OK":
            response += self.serial.read(self.serial.inWaiting())  # type: ignore[attr-defined]
            raise TestError("could not send script", response)

    def read_test(self, count0: int) -> None:
        self.serial.write(b"\x03\x01\x04")  # break, raw-repl, soft-reboot
        self.drain_input()
        script = MICROPYTHON_SCRIPT.replace("<COUNT>", str(count0))
        self.send_script(script.encode("ascii"))

        start_s = time.monotonic()
        byte_count = 0
        for i0 in range(count0):
            i1 = i0 + 1
            read_start_s = time.monotonic()
            chars = self.serial.read(len(CHARS))
            read_duration_s = time.monotonic() - read_start_s
            if chars != CHARS:
                print(f"ERROR, read_duration_s={read_duration_s:0.6f}s")
                print("  expected:", CHARS)
                print("  received:", chars)
                read_start_s = time.monotonic()
                chars2 = self.serial.read(len(CHARS))
                read_duration_s = time.monotonic() - read_start_s
                print(
                    f"  try reading again: {chars2.decode('ascii')} read_duration_s={read_duration_s:0.6f}s"
                )
                print(f"   serial:{self.serial!r}")
                elements = [
                    f"{self.serial.fd=}",
                    f"{self.serial.in_waiting=}",
                    f"{self.serial.pipe_abort_read_r=}",
                    f"{self.serial.pipe_abort_read_w=}",
                    f"{self.serial.pipe_abort_write_r=}",
                    f"{self.serial.pipe_abort_write_w=}",
                    f"{self.serial._rts_state=}",  # type: ignore[attr-defined]
                    f"{self.serial._break_state=}",  # type: ignore[attr-defined]
                    f"{self.serial._dtr_state=}",  # type: ignore[attr-defined]
                    f"{self.serial._dsrdtr=}",  # type: ignore[attr-defined]
                ]
                print("  ", " ".join(elements))
                assert isinstance(self.serial.fd, int), self.serial.fd
                print(f"   {os.fstat(self.serial.fd)=!r}")

                print_fds()

                raise TestError("Received erronous data.")
            count_text = self.serial.read(6)
            count0 = int(count_text)
            assert count0 == i0
            byte_count += len(CHARS) + 6
            if (i1 % 1000) == 0:
                duration_s = time.monotonic() - start_s
                # print(i, chars, count, f"{byte_count / duration_s / 1_000:0.6f}kBytes/s")
                print(f"{i1:06d}: {byte_count / duration_s / 1_000:03.0f}kBytes/s")
                start_s = time.monotonic()
                byte_count = 0


@app.command(help="Write datastream from micropython ")
def write_alphabet(
    test_instance: TyperAnnotated[
        str,
        typer.Option(help="For example port:/dev/ttyACM3"),
    ],
    count: TyperAnnotated[
        int,
        typer.Option(help="The count of ~60byte-strings to be sent"),
    ] = 10_000,  # noqa: UP007
) -> None:
    assert isinstance(test_instance, str)
    assert str(test_instance).startswith("port:"), test_instance

    serial_port = test_instance[len("port:") :]  # type: ignore[index]
    ssw = SimpleSerialWrite(serial.Serial(serial_port, baudrate=115200, timeout=1))
    ssw.read_test(count0=count)


if __name__ == "__main__":
    app()
