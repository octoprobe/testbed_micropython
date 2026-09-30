from __future__ import annotations

import logging
import pathlib
import time

import dwfpy

from esp32ramp.context_measure import MeasureContext, Scope
from esp32ramp import constants

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
            scope = Scope(ad3=mtx.ad3)
            scope.channel0.setup()
            scope.channel1.setup()
            scope.setup()

            # mtx.ad3.scope_1.setup(range=50.0, offset=0.0, coupling="dc")
            # mtx.ad3.scope.setup_edge_trigger(
            #     channel=0,
            #     slope="rising",
            #     level=0.75,
            #     position=0.01,
            #     mode="auto",
            # )
            # mtx.ad3.scope.setup_acquisition(
            #     mode="single",
            #     sample_rate=2e5,
            #     buffer_size=16384,
            #     configure=True,
            # )
            # mtx.ad3.scope.configure(start=True)

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

            mtx.ad3.scope.wait_for_status(dwfpy.Status.DONE, read_data=True)
            scope.save(filename=constants.DIRECTORY_TESTRESULTS / "scope.html")

        if False:
            awg = mtx.ad3.device.analog_output["ch1"]
            awg.setup(function="ramp-up", frequency=0.25, amplitude=2.0, offset=3.0)
            awg.repeat_count = 1
            awg.configure(start=True)


if __name__ == "__main__":
    main()
