from __future__ import annotations

import dataclasses
import logging

import typer

from testbed_micropython.constants import EnumFut

logger = logging.getLogger(__file__)


@dataclasses.dataclass
class ArgsQuery:
    only_test: set[str] = dataclasses.field(default_factory=set)
    skip_test: set[str] = dataclasses.field(default_factory=set)
    only_fut: set[EnumFut] = dataclasses.field(default_factory=set)
    skip_fut: set[EnumFut] = dataclasses.field(default_factory=set)
    count: int = 0
    """
    Is only relevant for '--query-test'.
    Every test should be repeated 'count' time.
    """

    def __post_init__(self) -> None:
        assert isinstance(self.count, int)
        for elements0 in (
            self.only_test,
            self.skip_test,
        ):
            assert isinstance(elements0, set)
            for element0 in elements0:
                assert isinstance(element0, str)

        for elements1 in (
            self.only_fut,
            self.skip_fut,
        ):
            assert isinstance(elements1, set)
            for element1 in elements0:
                assert isinstance(element1, EnumFut)

    @staticmethod
    def factory(
        only_test: list[str] | None,
        skip_test: list[str] | None,
        only_fut: list[str] | None,
        skip_fut: list[str] | None,
        arg: str,
        count=0,
    ) -> ArgsQuery:
        if (only_test is not None) and (skip_test is not None):
            logger.error(
                f"mptest --only-{arg}=... --skip-{arg}=...: Only one at a time is allowed!"
            )
            raise typer.Exit(1)

        if only_test is None:
            only_test = []
        if skip_test is None:
            skip_test = []
        if only_fut is None:
            only_fut = []
        if skip_fut is None:
            skip_fut = []

        return ArgsQuery(
            only_test=set(only_test),
            skip_test=set(skip_test),
            only_fut={EnumFut.factory(fut) for fut in only_fut},
            skip_fut={EnumFut.factory(fut) for fut in skip_fut},
            count=count,
        )
