from __future__ import annotations

import dataclasses
import logging

import typer

logger = logging.getLogger(__file__)


@dataclasses.dataclass
class ArgsQuery:
    only: set[str] = dataclasses.field(default_factory=set)
    skip: set[str] = dataclasses.field(default_factory=set)

    def __post_init__(self) -> None:
        for elements in (
            self.only,
            self.skip,
        ):
            assert isinstance(elements, set)
            for element in elements:
                assert isinstance(element, str)

    @staticmethod
    def factory(only: list[str] | None, skip: list[str] | None, arg: str) -> ArgsQuery:
        if (only is not None) and (skip is not None):
            logger.error(
                f"mptest --only-{arg}=... --skip-{arg}=...: Only one at a time is allowed!"
            )
            raise typer.Exit(1)
        if only is None:
            only = []
        if skip is None:
            skip = []
        return ArgsQuery(only=set(only), skip=set(skip))
