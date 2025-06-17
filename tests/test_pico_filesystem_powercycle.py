import logging
import pathlib
import time

from octoprobe.lib_mpremote import ExceptionCmdFailed, MpRemote
from octoprobe.scripts.commissioning import init_logging
from octoprobe.usb_tentacle.usb_tentacle import UsbTentacles
from octoprobe.util_pyudev import UdevPoller

from testbed_micropython.mptest.util_common import mip_install
from testbed_micropython.mptest.util_testrunner import ResultsDir, instantiate_tentacles
from testbed_micropython.testcollection.testrun_specs import TestArgs

DIRECTORY_MICROPYTHON_TESTS = pathlib.Path("/home/maerki/gits/micropython")
assert DIRECTORY_MICROPYTHON_TESTS.is_dir()
DIRECTORY_TESTRESULTS = pathlib.Path("/tmp/tests/test_pico_filesystem_powercycle")
DIRECTORY_TESTRESULTS.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger(__file__)


def main() -> None:
    usb_tentacles = UsbTentacles.query(poweron=False)
    init_logging()
    if len(usb_tentacles) != 1:
        raise ValueError(
            f"Expect exactly one tentacle to be connected but found {len(usb_tentacles)}!"
        )
    tentacle = instantiate_tentacles(usb_tentacles)[0]

    with UdevPoller() as udev:
        for i in range(1000):
            tty = tentacle.dut.dut_mcu.application_mode_power_up(
                tentacle=tentacle, udev=udev
            )
            # tentacle.dut.application_mode_power_up_delay()
            logger.info(f"***** {i} {tty} *****")
            if True:
                tentacle.infra.connect_mpremote_if_needed()
                with MpRemote(tty=tty) as mp_remote:
                    try:
                        mp_remote.exec_raw(
                            "import os; os.remove('/lib/unittest/__init__.mpy')"
                        )
                        mp_remote.exec_raw(
                            "import os; os.rmdir('/lib/unittest'); os.rmdir('/lib')"
                        )
                    except ExceptionCmdFailed as e:
                        print(f"{e!r}")
            testargs = TestArgs(
                repo_micropython_tests=DIRECTORY_MICROPYTHON_TESTS,
                testresults_directory=ResultsDir(
                    directory_top=DIRECTORY_TESTRESULTS,
                    test_name="pico_filesystem_powercycle",
                    test_nodeid=tentacle.label_short,
                ),
            )
            mip_install(
                testargs=testargs,
                tentacle=tentacle,
                serial_port=tty,
                mip_package="unittest",
            )
            # tentacle.power_dut_off_and_wait()
            tentacle.power.dut = False
            # time.sleep(2.0)


if __name__ == "__main__":
    main()
