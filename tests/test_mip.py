import pytest
from octoprobe.lib_tentacle import Tentacle

from testbed.constants import EnumFut


@pytest.mark.required_futs(EnumFut.FUT_MCU_ONLY)
def test_mip(mcu: Tentacle) -> None:
    """
    https://micropython.org/pi/v2/index.json
    https://mim.oliverrobson.tech/
    tests/test_simple.py

    site-packages/mpremote/mip.py: def do_mip(state, args)

    _install_package(
        state.transport,
        package,
        args.index.rstrip("/"),
        args.target,
        version,
        args.mpy,
    )
    """
    assert mcu.is_mcu
    url = "github:Thomascountz/micropython_i2c_lcd/hd44780.py"
    url = "https://github.com/micropython/micropython-lib/tree/master/python-stdlib/pprint"
    url = "github:micropython/micropython-lib/python-stdlib/pprint/pprint.py@master"
    # url = "github:python-ecosys/aiohttp
    url = "aiohttp"
    # https://micropython.org/pi/v2/index.json
    url = "aiohttp@0.0.2"
    mcu.dut.mp_remote.mip_install_package(package=url)
