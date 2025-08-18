# ESP32_DEVKIT

This sheet collects all information to build the wireing list in `tentacle_specs.py`.

Columns

* `Octoprobe function`: If for example `FUT_EXTMOD_HARDWARE` appears on multiple lines, this implies that all these lines are electically connected. 
* `Silkscreen` refers to the printed text on the board. This often differs from GPIO.

| Octoprobe function | Silkscreen | GPIO | Functions | test sourccode |
| - | - | - | - | - |
| **UART loopback** |||||
| FUT_EXTMOD_HARDWARE TX-RX | - | - | - | tests/extmod_hardware/machine_pwm.py, tests/extmod_hardware/machine_uart_irq_rx.py |
| FUT_EXTMOD_HARDWARE TX-RX | - | - | - | - |
| **I2C loopback** |||||
| FUT_EXTMOD_HARDWARE SCL | - | - | - | tests/extmod_hardware/machine_i2c_target.py |
| FUT_EXTMOD_HARDWARE SDA | - | - | - | - |
| **I2C** |||||
| FUT_I2C_EXTERNAL SCL | - | - | - | tests/multi_extmod/machine_i2c_target_irq.py |
| FUT_I2C_EXTERNAL SDA | - | - | - | - |

Tested with micropython:

* GPIO4: <silkscreen 4>
* GPIO5: <silkscreen 5>
* GPIO6: <silkscreen CLK>



### tests/extmod_hardware/machine_pwm.py

FUT_EXTMOD_HARDWARE (UART loopback)

```python
if "esp32" in sys.platform:
    pwm_pulse_pins = ((4, 5),)
    freq_margin_per_thousand = 2
    duty_margin_per_thousand = 1
    timing_margin_us = 20
```

### tests/extmod_hardware/machine_uart_irq_rx.py

FUT_EXTMOD_HARDWARE (UART loopback)

```python
elif "esp32" in sys.platform:
    uart_id = 1
    tx_pin = 4
    rx_pin = 5
```

### tests/extmod_hardware/machine_i2c_target.py

FUT_EXTMOD_HARDWARE (I2C loopback)

```python
elif sys.platform == "esp32":
    args_controller = {"scl": 5, "sda": 6}
    args_target = (0,)  # on pins 9/8 for C3 and S3, 18/19 for others
    kwargs_target = {"scl": 9, "sda": 8}
```


### tests/multi_extmod/machine_i2c_target_irq.py

```python
elif sys.platform == "esp32":
    i2c_args = (1,)  # on pins 9/8 for C3 and S3, 18/19 for others
    i2c_kwargs = {"scl": 9, "sda": 8}
```


## Micropython testcode

```python
from machine import Pin
import time

gpio_DUT = 6
pin_DUT = Pin(gpio_DUT, Pin.OUT)

while True:
  for v in (0, 1):
    time.sleep(0.2)
    print(f"{pin_DUT}: {v}")
    pin_DUT.value(v)
```