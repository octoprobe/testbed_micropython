"""
Where to take the tests from
--micropython-tests-giturl=https://github.com/dpgeorge/micropython.git@tests-full-test-runner

Where to take the firmware from
--firmware-build-giturl=https://github.com/micropython/micropython.git@v1.24.1
--firmware-build-gitdir=~/micropython
--firmware-gitdir=~/micropython
"""

from __future__ import annotations

from typing import Optional

import typer
import typing_extensions

# 'typer' does not work correctly with typing.Annotated
# Required is: typing_extensions.Annotated
TyperAnnotated = typing_extensions.Annotated

# mypy: disable-error-code="valid-type"
# This will disable this warning:
#   op.py:58: error: Variable "octoprobe.scripts.op.TyperAnnotated" is not valid as a type  [valid-type]
#   op.py:58: note: See https://mypy.readthedocs.io/en/stable/common_issues.html#variables-vs-type-aliases

app = typer.Typer()


@app.command()
def run(
    micropython_tests_giturl: TyperAnnotated[
        Optional[str],
        typer.Option(),  # noqa: UP007
        typer.Argument(help="Board name", autocompletion=_complete_board),
    ] = None,
    firmware_build_giturl: TyperAnnotated[
        Optional[str], typer.Option()  # noqa: UP007
    ] = None,
    serial: TyperAnnotated[Optional[list[str]], typer.Option()] = None,  # noqa: UP007
) -> None:
    print(f"{micropython_tests_giturl=} {firmware_build_giturl=}")


if __name__ == "__main__":
    app()
