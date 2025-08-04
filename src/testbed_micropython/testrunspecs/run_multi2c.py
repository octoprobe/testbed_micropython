from __future__ import annotations

import logging

from octoprobe.lib_mpremote import MpRemote

from ..constants import EnumFut
from ..tentacle_spec import TentacleMicropython
from ..testcollection.constants import (
    TIMEOUT_FLASH_S,
)
from ..testcollection.testrun_specs import (
    TestArgs,
    TestRun,
    TestRunSpec,
)

logger = logging.getLogger(__file__)

CODE_I2C_TARGET = """
import time
from machine import Pin, I2CTarget

I2C_TARGET_ADDRESS = 0x42

SDA_PIN = 10
SCL_PIN = 11

memory = bytearray(b'Memory before.....')

def i2c_event_handler(i2c_target):
    flags = i2c_target.irq().flags()

    if flags & I2CTarget.IRQ_END_WRITE:
        print(f"I2C Master wrote data to memory, starting at address: {i2c_target.memaddr}")
        print(f"New memory data: {memory}")

    elif flags & I2CTarget.IRQ_ADDR_MATCH_READ:
        print("I2C Master requested a read.")

def start_i2c_target():
    i2c_slave = I2CTarget(
        id=1,
        addr=I2C_TARGET_ADDRESS,
        mem=memory,
        scl=Pin(SCL_PIN),
        sda=Pin(SDA_PIN)
    )
    i2c_slave.irq(i2c_event_handler)

    print(f"Initial memory data: {memory}")

start_i2c_target()
"""

CODE_I2C_CONTROLLER = """
import time
from machine import Pin, I2C

I2C_TARGET_ADDRESS = 0x42

SDA_PIN = 10
SCL_PIN = 11

data_to_write = bytearray(b'Memory after.....')
memory_len = len(b'Memory before.....')

def run_i2c_controller():
    i2c_master = I2C(
        id=1,
        scl=Pin(SCL_PIN),
        sda=Pin(SDA_PIN),
        freq=100_000  # 100 kHz is a common I2C frequency
    )

    time.sleep(1)

    data_read = i2c_master.readfrom_mem(
        I2C_TARGET_ADDRESS,
        0,
        memory_len,
        addrsize=8
    )
    print(f"Read {len(data_read)} bytes from target: {data_read.decode()}")

    i2c_master.writeto_mem(
        I2C_TARGET_ADDRESS,
        0,
        data_to_write,
        addrsize=8
    )
    print(f"Wrote '{data_to_write.decode()}' to target at address 0x00.")

    data_read = i2c_master.readfrom_mem(
        I2C_TARGET_ADDRESS,
        0,
        memory_len,
        addrsize=8
    )
    print(f"Read {len(data_read)} bytes from target: {data_read.decode()}")

run_i2c_controller()
"""


class TestRunMultiI2C(TestRun):
    def test_using_mpremote(self, testargs: TestArgs) -> None:
        tentacle = self.tentacle_variant.tentacle
        assert isinstance(tentacle, TentacleMicropython)
        mpremote_infra = tentacle.infra.mp_remote
        mpremote_dut = tentacle.dut.mp_remote
        assert isinstance(mpremote_infra, MpRemote)

        rc_infra = mpremote_infra.exec_raw(cmd=CODE_I2C_TARGET)
        logger.info(f"rc_infra: {rc_infra.strip()}")

        rc_dut = mpremote_dut.exec_raw(cmd=CODE_I2C_CONTROLLER)
        logger.info(f"rc_dut: {rc_dut.replace('\r\n', '\n'.strip())}")

        # mpremote_infra.state.transport.ensure_raw_repl(soft_reset=None)
        # mpremote_infra.state.ensure_raw_repl(soft_reset=True)
        rc_infra = mpremote_infra.exec_raw(cmd="print('hello')", soft_reset=True)
        logger.info(f"rc_infra: {rc_infra.strip()}")

    def test_using_dev(self, testargs: TestArgs) -> None:
        tentacle = self.tentacle_variant.tentacle
        assert isinstance(tentacle, TentacleMicropython)

        with tentacle.infra.borrow_tty() as serial_port_infra:
            serial_port_dut = tentacle.dut.get_tty()
            print(f"Go for it! {serial_port_dut} {serial_port_infra}")

    def test(self, testargs: TestArgs) -> None:
        self.test_using_dev(testargs=testargs)


TESTRUNSPEC_RUNTESTS_MULTI2C = TestRunSpec(
    label="RUN-MULTITESTS_I2C",
    helptext="See https://github.com/octoprobe/testbed_micropython/issues/57",
    command=["run-multitests.py", "multi_net/*.py"],
    required_fut=EnumFut.FUT_I2C,
    requires_reference_tentacle=False,
    testrun_class=TestRunMultiI2C,
    timeout_s=4 * 60.0 + 2 * TIMEOUT_FLASH_S,
)
