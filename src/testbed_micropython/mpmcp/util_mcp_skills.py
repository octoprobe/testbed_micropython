from __future__ import annotations

import hashlib
import mimetypes
import pathlib
import re
import typing
import urllib.parse

import yaml
from mcp.server.context import ServerRequestContext
from mcp.server.extension import Extension, MethodBinding, ResourceBinding
from mcp.server.mcpserver.resources import BinaryResource, Resource, TextResource
from mcp.shared.exceptions import MCPError
from mcp_types import (
    CacheableResult,
    INVALID_PARAMS,
    PaginatedRequestParams,
    PaginatedResult,
    RequestParams,
    ResultType,
)
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

_SKILL_NAME_PATTERN = re.compile(r"^[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$")


class _Model(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class SkillResource(_Model):
    uri: str
    digest: str
    size: int


class Skill(_Model):
    uri: str
    frontmatter: dict[str, typing.Any]
    resources: list[SkillResource] | typing.Literal["dynamic"]
    meta: dict[str, typing.Any] | None = Field(alias="_meta", default=None)


class ListSkillsParams(PaginatedRequestParams):
    pass


class ListSkillsResult(PaginatedResult, CacheableResult):
    skills: list[Skill]
    result_type: ResultType = "complete"


class GetSkillParams(RequestParams):
    uri: str


class GetSkillResult(CacheableResult):
    skill: Skill
    result_type: ResultType = "complete"


def _parse_frontmatter(path: pathlib.Path) -> dict[str, typing.Any]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    if not lines or lines[0] != "---":
        raise ValueError(f"{path} does not start with YAML frontmatter")

    try:
        closing_delimiter = lines.index("---", 1)
    except ValueError as error:
        raise ValueError(f"{path} has unterminated YAML frontmatter") from error

    frontmatter = yaml.safe_load("\n".join(lines[1:closing_delimiter]))
    if not isinstance(frontmatter, dict):
        raise ValueError(f"{path} frontmatter must be a mapping")

    for key in ("name", "description"):
        if not isinstance(frontmatter.get(key), str) or not frontmatter[key].strip():
            raise ValueError(f"{path} frontmatter must contain a non-empty {key!r}")
    if not _SKILL_NAME_PATTERN.fullmatch(frontmatter["name"]):
        raise ValueError(f"{path} has invalid skill name {frontmatter['name']!r}")
    return typing.cast(dict[str, typing.Any], frontmatter)


def _resource_uri(skill_name: str, relative_path: pathlib.Path) -> str:
    quoted_name = urllib.parse.quote(skill_name, safe="")
    quoted_path = "/".join(
        urllib.parse.quote(part, safe="") for part in relative_path.parts
    )
    return f"skill://{quoted_name}/{quoted_path}"


def _load_skill(
    directory: pathlib.Path,
) -> tuple[Skill, list[ResourceBinding]]:
    skill_markdown = directory / "SKILL.md"
    if not skill_markdown.is_file():
        raise ValueError(f"Skill directory is missing SKILL.md: {directory}")

    frontmatter = _parse_frontmatter(skill_markdown)
    skill_name = typing.cast(str, frontmatter["name"])
    skill_uri = _resource_uri(skill_name, pathlib.Path("SKILL.md"))
    manifest: list[SkillResource] = []
    resource_bindings: list[ResourceBinding] = []

    for path in sorted(file for file in directory.rglob("*") if file.is_file()):
        relative_path = path.relative_to(directory)
        content = path.read_bytes()
        uri = _resource_uri(skill_name, relative_path)
        mime_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        if path.suffix.lower() in (".md", ".markdown"):
            mime_type = "text/markdown"

        resource: Resource
        if mime_type.startswith("text/") or mime_type in (
            "application/json",
            "application/xml",
        ):
            try:
                resource = TextResource(
                    uri=uri,
                    name=relative_path.as_posix(),
                    mime_type=mime_type,
                    text=content.decode("utf-8"),
                )
            except UnicodeDecodeError:
                mime_type = "application/octet-stream"
                resource = BinaryResource(
                    uri=uri,
                    name=relative_path.as_posix(),
                    mime_type=mime_type,
                    data=content,
                )
        else:
            resource = BinaryResource(
                uri=uri,
                name=relative_path.as_posix(),
                mime_type=mime_type,
                data=content,
            )

        manifest.append(
            SkillResource(
                uri=uri,
                digest=f"sha256:{hashlib.sha256(content).hexdigest()}",
                size=len(content),
            )
        )
        resource_bindings.append(ResourceBinding(resource=resource))

    return (
        Skill(uri=skill_uri, frontmatter=frontmatter, resources=manifest),
        resource_bindings,
    )


class Skills(Extension):
    identifier = "io.modelcontextprotocol/skills"

    def __init__(self, directory: pathlib.Path):
        self._skills: dict[str, Skill] = {}
        self._resources: list[ResourceBinding] = []

        for skill_directory in sorted(
            path for path in directory.iterdir() if path.is_dir()
        ):
            skill, resources = _load_skill(skill_directory)
            if skill.uri in self._skills:
                raise ValueError(f"Duplicate skill URI: {skill.uri}")
            self._skills[skill.uri] = skill
            self._resources.extend(resources)

    def methods(self) -> tuple[MethodBinding, ...]:
        return (
            MethodBinding(
                method="skills/list",
                params_type=ListSkillsParams,
                handler=self._list_skills,
            ),
            MethodBinding(
                method="skills/get",
                params_type=GetSkillParams,
                handler=self._get_skill,
            ),
        )

    def resources(self) -> tuple[ResourceBinding, ...]:
        return tuple(self._resources)

    async def _list_skills(
        self,
        ctx: ServerRequestContext[typing.Any, typing.Any],
        params: ListSkillsParams,
    ) -> ListSkillsResult:
        del ctx, params
        return ListSkillsResult(
            skills=list(self._skills.values()),
            cache_scope="public",
        )

    async def _get_skill(
        self,
        ctx: ServerRequestContext[typing.Any, typing.Any],
        params: GetSkillParams,
    ) -> GetSkillResult:
        del ctx
        try:
            skill = self._skills[params.uri]
        except KeyError as error:
            raise MCPError(
                code=INVALID_PARAMS,
                message=f"unknown skill: {params.uri}",
            ) from error
        return GetSkillResult(skill=skill, cache_scope="public")
