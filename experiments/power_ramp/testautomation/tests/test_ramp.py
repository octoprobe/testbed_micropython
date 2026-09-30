from __future__ import annotations

import datetime
import inspect
import io
import logging
import pathlib

import dwfpy
from dwfpy_ad3 import dwfpy_ad3
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
        mtx.ad3.x()
        mtx.ad3.awg_2.setup(
            function="dc",
            offset=V,
            configure=True,
            start=True,
        )


if __name__ == "__main__":
    main()
