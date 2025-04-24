from __future__ import annotations

import dataclasses


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
    def factory(only: list[str] | None, skip: list[str] | None) -> ArgsQuery:
        if only is None:
            only = []
        if skip is None:
            skip = []
        return ArgsQuery(only=set(only), skip=set(skip))
