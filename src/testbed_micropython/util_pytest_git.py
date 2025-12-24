import pathlib
import subprocess


def assert_git_unchanged(filename: pathlib.Path) -> None:
    try:
        subprocess.run(
            args=[
                "git",
                "diff",
                "--exit-code",
                str(filename),
            ],
            text=True,
            capture_output=True,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        raise AssertionError(
            f"{filename}:\nstderr:{e.stderr}\nstdout:{e.stdout}\nExit code {e.returncode}: If this is 1, then the file has changed."
        ) from e
