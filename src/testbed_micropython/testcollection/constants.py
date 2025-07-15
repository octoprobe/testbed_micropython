TIMEOUT_FLASH_S = 60.0

MICROPYTHON_DIRECTORY_TESTS = "tests"
DELIMITER_TESTRUN = ","
"""
RUN-TESTS_STANDARD_VIA_MPY,c@5f2a-ADA_ITSYBITSY_M0
"""
DELIMITER_TENTACLE = "@"
# TODO: Find an merge other places where this ',' is used!
DELIMITER_TENTACLES = ","
"""
Example: 8f34-PICO_W,23ad-LOLIN_C3
"""
DELIMITER_TESTROLE = "-"
"""
Example: run-perfbench.py,a@2d2d-lolin_D1-ESP8266_GENERIC-first

Hint: '-first'
"""

ENV_PYTHONUNBUFFERED: dict[str, str] = {"PYTHONUNBUFFERED": "1"}

ENV_MICROPYTHON_TESTS: dict[str, str] = {"MICROPY_TEST_TIMEOUT": "60"}
"""
https://github.com/octoprobe/testbed_micropython/issues/40
https://github.com/micropython/micropython/pull/17538
https://github.com/micropython/micropython/blob/master/tests/run-tests.py#L19
MICROPY_TEST_TIMEOUT in s, defaults to 30
"""
ENV_MICROPYTHON_TESTS.update(ENV_PYTHONUNBUFFERED)
