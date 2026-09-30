from __future__ import annotations

import logging
import pathlib
import time

from esp32ramp.context_measure import MeasureContext

# from testautomation import lib_tests
# from testautomation.context_measure import MeasureContext
# from testautomation.context_mpremote import RemoteMpContext
# from testautomation.context_result import ResultContext


# def main():
#     with ResultContext() as rtx:
#         with MeasureContext() as mtx:
#             mtx.power_up_device()

#             with RemoteMpContext() as mp:
#                 mp.load_code_py()

#                 lib_tests.test_calibrate_pogo84_dev(mtx=mtx, mp=mp, rtx=rtx)


# if __name__ == "__main__":
#     main()


DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent
DIRECTORY_TESTRESULTS = DIRECTORY_OF_THIS_FILE.parent.parent / "testresults"
DIRECTORY_TESTRESULTS.mkdir(parents=True, exist_ok=True)


logger = logging.getLogger(__name__)

LOGGING_FORMAT = "%(asctime)s %(levelname)s %(filename)s:%(lineno)d %(message)s"
LOGGING_DATEFMT = "%H:%M:%S"
logging.basicConfig(
    level=logging.DEBUG,
    format=LOGGING_FORMAT,
    datefmt=LOGGING_DATEFMT,
)
logger_dwfpy = logging.getLogger("dwfpy")
logger_dwfpy.setLevel("INFO")


def main():
    with MeasureContext() as mtx:
        if False:
            for voltage in range(2, 6):
                time.sleep(1.0)
                mtx.ad3.supply_P.V = float(voltage)
        if True:
            mtx.ad3.supply_P.enable = True
            mtx.ad3.supply_P.V = 0.5
            begin_s = time.monotonic()
            step_duration_s = 0.01
            # Measured: 8.1ms for 5 steps
            for idx0, voltage in enumerate((1.0, 2.0, 3.0, 4.0, 5.0)):
                duration_required_s = idx0 * step_duration_s
                duration_actual_s = time.monotonic() - begin_s
                time_to_wait_s = duration_required_s - duration_actual_s
                if time_to_wait_s > 0:
                    time.sleep(time_to_wait_s)
                print(f"{voltage:0.1f}V {1000 * (time.monotonic() - begin_s):0.1f}ms")
                mtx.ad3.supply_P.V = voltage
            time.sleep(10.0)
        if False:
            awg = mtx.ad3.device.analog_output["ch1"]
            awg.setup(function="ramp-up", frequency=0.25, amplitude=2.0, offset=3.0)
            awg.repeat_count = 1
            awg.configure(start=True)


if __name__ == "__main__":
    main()
