"""
WIP, Experiment
"""

import pytest
from octoprobe.lib_tentacle import Tentacle

from testbed.constants import EnumFut


@pytest.mark.required_futs(EnumFut.FUT_MCU_ONLY)
def wip_test_extmod(mcu: Tentacle) -> None:
    """
    Same as <micropython>tests/extmod/machine_uart_tx.py

    Test that write+flush takes the expected amount of time to execute.
    """
    assert mcu.is_mcu
    mcu_config = mcu.tentacle_spec.mcu_config

    for bits_per_s in (2400, 9600, 115200):

        mp_program = """
from machine import Pin, UART

{{mcu_config.i2c}}

text = "Hello World"
uart = UART(uart_id, {{bits_per_s}}, bits=8, parity=None, stop=1, **pins)
time.sleep_ms(initial_delay_ms)

start_us = time.ticks_us()
uart.write(text)
uart.flush()
duration_us = time.ticks_diff(time.ticks_us(), start_us)
    """
        mcu.dut.mp_remote.exec_render(
            mp_program, mcu_config=mcu_config, bits_per_s=bits_per_s
        )

        duration_us = mcu.dut.mp_remote.read_int("duration_us")
        print(f"duration_us: {duration_us}")
