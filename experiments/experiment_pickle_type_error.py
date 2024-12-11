from __future__ import annotations

import pathlib
import pickle

# class MultiprocessingException(Exception):
#     def __init__(self, msg: str, log_filename: pathlib.Path) -> None:
#         self.log_filename = log_filename
#         super().__init__(msg)


class Base:
    def __init__(self, msg: str) -> None:
        self.msg = msg


class MultiprocessingException(Exception):
    @staticmethod
    def pickle_save_factory(
        msg: str, log_filename: pathlib.Path
    ) -> MultiprocessingException:
        e = MultiprocessingException(msg)
        e.log_filename = log_filename
        return e


me = MultiprocessingException.pickle_save_factory("Hallo", pathlib.Path(__file__))
dump = pickle.dumps(me)
me1 = pickle.loads(dump)

for m in (me, me1):
    print(f"me1: {m!r}, {m.log_filename}")

if False:

    class X:
        def __init__(self, x: int):
            pass

    try:
        x = X()
        print(x)
    except Exception as e:
        print(f"{e!r}")
