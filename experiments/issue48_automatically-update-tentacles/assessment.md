
https://github.com/octoprobe/testbed_micropython/issues/57


## Assessments: GPIO

Tentacle v3, file:///home/maerki/Downloads/schematics.pdf
GPIO9 - GPIO14

Tentacle v4
GPIO2, 3, 4, 5, 10, 11, 12, 13

Selected:
GPIO10,11,12,13 for I2C,SPI


## Assessments: Code

PICO Infra: Controller

```python
import time
from machine import Pin, I2C

I2C_TARGET_ADDRESS = 0x42

SDA_PIN = 10
SCL_PIN = 11

data_to_write = bytearray(b'Memory after.....')
memory_len = len(b'Memory before.....')

def main():
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

if __name__ == "__main__":
    main()
```

DUT : Target

```python
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

def main():
    i2c_slave = I2CTarget(
        id=1,
        addr=I2C_TARGET_ADDRESS,
        mem=memory,
        scl=Pin(SCL_PIN),
        sda=Pin(SDA_PIN)
    )
    i2c_slave.irq(i2c_event_handler)

    print(f"Initial memory data: {memory}")


if __name__ == "__main__":
    main()
```


## Tests in micropython directory

tests/run-multitests.py
