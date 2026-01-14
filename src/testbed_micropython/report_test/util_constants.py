from __future__ import annotations

FORMAT_HTTP_STARTED_AT = "%Y-%m-%d %H:%M"
"""
Used on the html-page on the report
"""

TIME_FORMAT = "%Y-%m-%d_%H-%M-%S-%Z"

FILENAME_CONTEXT_JSON = "context.json"

FILENAME_CONTEXT_TESTGROUP_JSON = "context_testgroup.json"


def seconds_to_duration(seconds: int) -> str:
    """
    Format nicely like 5h 10min

    seconds = 7975  # 2h, 12min, 55sec
    """
    assert isinstance(seconds, int)

    def split(value: int) -> list[int]:
        if value < 60:
            return [value]
        return split(value // 60) + [value % 60]

    def split2(seconds: int) -> list[int]:
        h = seconds // 3600
        seconds -= h * 3600
        m = seconds // 60
        seconds -= m * 60
        return [h, m, seconds]

    h, m, _s = split2(seconds)
    text = f"{h}h " if h > 0 else ""
    text += f"{m}min"

    return text
