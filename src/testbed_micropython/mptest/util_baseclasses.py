from __future__ import annotations

import dataclasses
import logging
import typing

import typer

from testbed_micropython.constants import EnumFut

logger = logging.getLogger(__file__)


@dataclasses.dataclass
class ArgsQuery:
    only_test: set[str] = dataclasses.field(default_factory=set)
    skip_test: set[str] = dataclasses.field(default_factory=set)
    only_fut: set[EnumFut] = dataclasses.field(default_factory=set)
    skip_fut: set[EnumFut] = dataclasses.field(default_factory=set)
    only_tag: set[str] = dataclasses.field(default_factory=set)

    def __post_init__(self) -> None:
        def assert_set_type(elements: set[typing.Any], expected_type: type) -> None:
            for elements0 in (
                self.only_test,
                self.skip_test,
                self.only_tag,
            ):
                assert isinstance(elements0, set)
                for element0 in elements0:
                    assert isinstance(element0, str)

        assert_set_type(self.only_test, str)
        assert_set_type(self.skip_test, str)
        assert_set_type(self.only_fut, EnumFut)
        assert_set_type(self.skip_fut, EnumFut)
        assert_set_type(self.only_tag, str)

    @staticmethod
    def factory(
        only_test: list[str] | None,
        skip_test: list[str] | None,
        only_fut: list[str] | None,
        skip_fut: list[str] | None,
        only_tag: list[str] | None,
        arg: str,
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
        if only_tag is None:
            only_tag = []

        return ArgsQuery(
            only_test=set(only_test),
            skip_test=set(skip_test),
            only_fut={EnumFut.factory(fut) for fut in only_fut},
            skip_fut={EnumFut.factory(fut) for fut in skip_fut},
            only_tag=set(only_tag),
        )
