from __future__ import annotations

import pathlib

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent
DIRECTORY_TESTRESULTS = DIRECTORY_OF_THIS_FILE.parent.parent / "testresults"
DIRECTORY_TESTRESULTS.mkdir(parents=True, exist_ok=True)