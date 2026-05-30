from __future__ import annotations

import json
import pathlib
import subprocess
import typing

from octoprobe.util_cached_git_repo import GitSpec

from ..constants import is_url

T = typing.TypeVar("T")


def subprocess_json(args: list[str]) -> dict[str, typing.Any] | list[typing.Any]:
    try:
        result = subprocess.run(args=args, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        assert isinstance(data, dict | list)
        return data
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}")
        raise
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        raise


class JsonCommitHash(dict[str, str]):
    _MARKER_BEGIN = "<!-- octoprobe-meta: "
    _MARKER_END = " -->"
    _KEY_sha = "sha"

    @property
    def sha(self) -> str:
        return self[self._KEY_sha]

    @classmethod
    def factory(cls, body: str) -> JsonCommitHash | None:
        """
        Example body: <!-- octoprobe-meta: {"report":"v1","sha":"<full_sha>","status":"ok"} -->'
        """
        pos_begin = body.find(cls._MARKER_BEGIN)
        if pos_begin < 0:
            return None
        pos_begin += len(cls._MARKER_BEGIN)
        pos_end = body.find(cls._MARKER_END, pos_begin)
        assert pos_end > pos_begin, (pos_begin, pos_end, body)
        json_text = body[pos_begin:pos_end]
        dict_commit_hash = json.loads(json_text)
        return JsonCommitHash(dict_commit_hash)


class JsonComment(dict[str, typing.Any]):
    """
    A json file (dict structure) as returned from 'gh pr view --json ...'.

    This class encapsulates the access to the internals.
    """

    _KEY_AUTHOR = "author"
    _KEY_LOGIN = "login"
    _KEY_BODY = "body"

    def _get(self, expected_type: type[T], key: str) -> T:
        value = self[key]
        assert isinstance(value, expected_type)
        return value

    @property
    def author_login(self) -> str:
        dict_author: dict[str, str] = self._get(dict, self._KEY_AUTHOR)
        return dict_author[self._KEY_LOGIN]

    @property
    def body(self) -> str:
        return self._get(str, self._KEY_BODY)

    @property
    def json_commit_hash(self) -> JsonCommitHash | None:
        return JsonCommitHash.factory(self.body)

    @property
    def commit_hash_tested(self) -> str | None:
        json_commit_hash = JsonCommitHash.factory(self.body)
        if json_commit_hash is None:
            return None
        return json_commit_hash.sha


class JsonPrPorts(dict[str, typing.Any]):
    """
    A json file with the micropython ports to be tested for a given PR.

    To ease debugging, this file has the format as retrieved from 'gh pr view --json ...'.
    """

    _KEY_MICROPYTHON_PORTS = "micropython_ports"
    _KEY_OCTOPROBE_BOT_USER = "octoprobe_bot_user"
    _KEY_PR_NUMBER = "number"
    _KEY_PR_REPO = "pr_repo"
    _KEY_COMMIT_HASH = "headRefOid"
    _KEY_COMMENTS = "comments"
    _KEY_FILES = "files"

    def _get(self, expected_type: type[T], key: str) -> T:
        value = self[key]
        assert isinstance(value, expected_type)
        return value

    @property
    def commit_hash_tested(self) -> str | None:
        bot_comment = self.bot_comment
        if bot_comment is None:
            return None
        return bot_comment.commit_hash_tested

    @property
    def files_modified(self) -> set[str]:
        return {f["path"] for f in self[self._KEY_FILES]}

    @property
    def commit_hash(self) -> str:
        return self._get(str, self._KEY_COMMIT_HASH)

    @property
    def pr(self) -> int:
        return self._get(int, JsonPrPorts._KEY_PR_NUMBER)

    @property
    def pr_repo(self) -> str:
        """
        Example: micropython/micropython
        """
        return self._get(str, JsonPrPorts._KEY_PR_REPO)

    @pr_repo.setter
    def pr_repo(self, value: str) -> None:
        self[JsonPrPorts._KEY_PR_REPO] = value

    @property
    def octoprobe_bot_user(self) -> str:
        return self._get(str, JsonPrPorts._KEY_OCTOPROBE_BOT_USER)

    @octoprobe_bot_user.setter
    def octoprobe_bot_user(self, value: str) -> None:
        self[JsonPrPorts._KEY_OCTOPROBE_BOT_USER] = value

    @property
    def ports(self) -> list[str]:
        return self._get(list, self._KEY_MICROPYTHON_PORTS)

    @ports.setter
    def ports(self, value: list[str]) -> None:
        self[self._KEY_MICROPYTHON_PORTS] = value

    @property
    def comments(self) -> list[JsonComment]:
        return [JsonComment(c) for c in self._get(list, self._KEY_COMMENTS)]

    @property
    def bot_comment(self) -> JsonComment | None:
        octoprobe_bot_user = self.octoprobe_bot_user
        for comment in self.comments:
            json_commit_hash = comment.json_commit_hash
            if json_commit_hash is None:
                continue
            if comment.author_login != octoprobe_bot_user:
                continue
            return comment
        return None

    def save_as_json(self, filename: pathlib.Path) -> None:
        with filename.open("w") as f:
            json.dump(fp=f, obj=self, indent=4)


def gh_read_pr(git_ref: str) -> JsonPrPorts:
    """
    Example git_ref: https://github.com/micropython/micropython.git~17782

    Call 'gr pr view'.
    """
    assert is_url(git_ref)
    git_spec = GitSpec.parse(git_ref=git_ref)
    assert git_spec.pr is not None

    def get_octoprobe_bot_user() -> str:
        args = [
            "gh",
            "api",
            "user",
        ]
        json_raw = subprocess_json(args=args)
        value = json_raw["login"]  # type: ignore
        assert isinstance(value, str)
        return value

    def get_json_pr_ports(octoprobe_bot_user: str) -> JsonPrPorts:
        args = [
            "gh",
            "pr",
            "view",
            f"https://github.com/{git_spec.user}/{git_spec.repo}/pull/{git_spec.pr}",
            "--json=url,number,author,title,headRefOid,state,files,comments",
        ]

        json_raw = subprocess_json(args=args)
        return JsonPrPorts(json_raw)

    octoprobe_bot_user = get_octoprobe_bot_user()
    json_pr_ports = get_json_pr_ports(octoprobe_bot_user=get_octoprobe_bot_user())

    assert json_pr_ports.pr == int(git_spec.pr)
    json_pr_ports.octoprobe_bot_user = octoprobe_bot_user
    json_pr_ports.pr_repo = f"{git_spec.user}/{git_spec.repo}"
    return json_pr_ports
