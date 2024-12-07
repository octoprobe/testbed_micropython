import pytest
from octoprobe.lib_mpremote import ExceptionCmdFailed
from octoprobe.lib_tentacle import Tentacle

from testbed.constants import EnumFut

# pylint: disable=W0613:unused-argument


@pytest.mark.required_futs(EnumFut.FUT_I2C)
def test_i2c_pattern(
    mcu: Tentacle,
    device_potpourry: Tentacle,
    daq_saleae: Tentacle,
) -> None:
    """
    This tests creates pulses:
    trig1: 1ms
    trig2: 2ms
    data1: 3ms
    data2: 4ms

    Have a look at docs/schematics_kicad/schematics.pdf to find testpoints to measure with a scope.
    """
    assert mcu.is_mcu
    mcu_config = mcu.tentacle_spec.mcu_config
    mp_program = """
# For any generic python board
from machine import Pin, I2C
from machine import PWM

# 'trig1' triggers the DAQ. So we initialize it last!
ticks_ms=int((2**16)/10)
PWM(Pin('{{mcu_config.data2}}'), freq=100, duty_u16=4*ticks_ms)
PWM(Pin('{{mcu_config.data1}}'), freq=100, duty_u16=3*ticks_ms)
PWM(Pin('{{mcu_config.trig2}}'), freq=100, duty_u16=2*ticks_ms)
PWM(Pin('{{mcu_config.trig1}}'), freq=100, duty_u16=1*ticks_ms)
"""

    if "PYBV11" in mcu.get_tag_mandatory("boards"):
        mp_program = """
# Pyboard only
from pyb import Pin, Timer

def run_timer(pin, tim, channel, pulse_width_percent):
    tim.channel(channel,
                Timer.PWM,
                pin=Pin(pin),
                pulse_width_percent=pulse_width_percent)

tim2 = Timer(2, freq=100)
tim4 = Timer(4, freq=100)
tim8 = Timer(8, freq=100)
run_timer('{{mcu_config.data2}}', tim2, 4, 40)
run_timer('{{mcu_config.data1}}', tim2, 3, 30)
run_timer('{{mcu_config.trig2}}', tim4, 3, 20)
run_timer('{{mcu_config.trig1}}', tim8, 2, 10)
"""
    mcu.dut.mp_remote.exec_render(mp_program, mcu_config=mcu_config)
    # mcu.dut.inspection_exit()


@pytest.mark.required_futs(EnumFut.FUT_I2C)
def test_i2c(
    mcu: Tentacle,
    device_potpourry: Tentacle,
    daq_saleae: Tentacle,
) -> None:
    assert mcu.is_mcu
    mcu_config = mcu.tentacle_spec.mcu_config

    mp_program = """
from machine import Pin, I2C

{{mcu_config.i2c}}

pin_trigger_1 = Pin('{{mcu_config.trig1}}', mode=Pin.OUT, value=0)
pin_trigger_2 = Pin('{{mcu_config.trig2}}', mode=Pin.OUT, value=0)
pin_trigger_1.value(1)
i2c_data = i2c.readfrom(0x50, 10, True)
pin_trigger_1.value(0)
"""
    mcu.dut.mp_remote.exec_render(mp_program, mcu_config=mcu_config)

    i2c_data = mcu.dut.mp_remote.read_bytes("i2c_data")
    print(f"i2c_data: {i2c_data!r}")
    assert i2c_data == b"\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff"


@pytest.mark.required_futs(EnumFut.FUT_ONEWIRE)
def test_onewire(
    mcu: Tentacle,
    device_potpourry: Tentacle,
    daq_saleae: Tentacle,
) -> None:
    assert mcu.is_mcu

    # Install mip if not already linked in firmware
    try:
        mcu.dut.mp_remote.exec_render(
            "import ds18x20", mcu_config=mcu.tentacle_spec.mcu_config
        )
    except ExceptionCmdFailed:
        mcu.dut.mp_remote.mip_install_package(package="ds18x20@0.1.0")
        mcu.dut.mp_remote.exec_render(
            "from mip import ds18x20", mcu_config=mcu.tentacle_spec.mcu_config
        )

    mp_program = """
from machine import Pin
import onewire
import time

ow = onewire.OneWire(Pin('{{mcu_config.onewire}}'))
ds = ds18x20.DS18X20(ow)

pin_trigger_1 = Pin('{{mcu_config.trig1}}', mode=Pin.OUT, value=0)
pin_trigger_2 = Pin('{{mcu_config.trig2}}', mode=Pin.OUT, value=0)
pin_trigger_1.value(1)
roms = ds.scan()
pin_trigger_1.value(0)

ds.convert_temp()
time.sleep_ms(750)
temperatures_c = [ds.read_temp(rom) for rom in roms]
"""
    mcu.dut.mp_remote.exec_render(mp_program, mcu_config=mcu.tentacle_spec.mcu_config)

    roms = mcu.dut.mp_remote.read_list("roms")
    print(f"roms: {roms}")

    assert (
        len(roms) == 2
    ), f"Two DS18 temperature sensors expected, but got {len(roms)}!"

    temperatures_c = mcu.dut.mp_remote.read_list("temperatures_c")
    print(f"temperatures_c: {temperatures_c}")
