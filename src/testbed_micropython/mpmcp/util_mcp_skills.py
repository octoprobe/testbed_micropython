from __future__ import annotations

import hashlib
import mimetypes
import pathlib
import typing
import urllib.parse

import yaml
from mcp.server.context import ServerRequestContext
from mcp.server.mcpserver.resources import BinaryResource, Resource, TextResource
from mcp.server.skills import Skills
from mcp.shared.exceptions import MCPError
from mcp.shared.skills import (
    GetSkillParams,
    GetSkillResult,
    ListSkillsParams,
    ListSkillsResult,
    Skill,
    SkillResource,
)
from mcp_types import INVALID_PARAMS


def _parse_frontmatter(path: pathlib.Path) -> dict[str, typing.Any]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0] != "---":
        raise ValueError(f"{path} does not start with YAML frontmatter")
    try:
        closing_delimiter = lines.index("---", 1)
    except ValueError as error:
        raise ValueError(f"{path} has unterminated YAML frontmatter") from error

    frontmatter = yaml.safe_load("\n".join(lines[1:closing_delimiter]))
    if not isinstance(frontmatter, dict):
        raise ValueError(f"{path} frontmatter must be a mapping")
    return typing.cast(dict[str, typing.Any], frontmatter)


def _resource_uri(skill_name: str, relative_path: pathlib.Path) -> str:
    quoted_name = urllib.parse.quote(skill_name, safe="")
    quoted_path = "/".join(
        urllib.parse.quote(part, safe="") for part in relative_path.parts
    )
    return f"skill://{quoted_name}/{quoted_path}"


class SkillCatalog:
    def __init__(self, directory: pathlib.Path):
        self._skills: dict[str, Skill] = {}
        self._resources: list[Resource] = []

        for skill_directory in sorted(
            path for path in directory.iterdir() if path.is_dir()
        ):
            skill, resources = self._load_skill(skill_directory)
            if skill.uri in self._skills:
                raise ValueError(f"Duplicate skill URI: {skill.uri}")
            self._skills[skill.uri] = skill
            self._resources.extend(resources)

    @staticmethod
    def _load_skill(directory: pathlib.Path) -> tuple[Skill, list[Resource]]:
        skill_markdown = directory / "SKILL.md"
        if not skill_markdown.is_file():
            raise ValueError(f"Skill directory is missing SKILL.md: {directory}")

        frontmatter = _parse_frontmatter(skill_markdown)
        skill_name = frontmatter.get("name")
        if not isinstance(skill_name, str):
            raise ValueError(f"{skill_markdown} frontmatter must contain a name")
        skill_uri = _resource_uri(skill_name, pathlib.Path("SKILL.md"))
        manifest: list[SkillResource] = []
        resources: list[Resource] = []

        for path in sorted(file for file in directory.rglob("*") if file.is_file()):
            relative_path = path.relative_to(directory)
            content = path.read_bytes()
            uri = _resource_uri(skill_name, relative_path)
            mime_type = mimetypes.guess_type(path.name)[0]
            if path.suffix.lower() in (".md", ".markdown"):
                mime_type = "text/markdown"

            resource: Resource
            if mime_type and (
                mime_type.startswith("text/")
                or mime_type in ("application/json", "application/xml")
            ):
                resource = TextResource(
                    uri=uri,
                    name=relative_path.as_posix(),
                    mime_type=mime_type,
                    text=content.decode("utf-8"),
                )
            else:
                resource = BinaryResource(
                    uri=uri,
                    name=relative_path.as_posix(),
                    mime_type=mime_type or "application/octet-stream",
                    data=content,
                )
            resources.append(resource)
            manifest.append(
                SkillResource(
                    uri=uri,
                    digest=f"sha256:{hashlib.sha256(content).hexdigest()}",
                    size=len(content),
                )
            )

        return (
            Skill(uri=skill_uri, frontmatter=frontmatter, resources=manifest),
            resources,
        )

    def resources(self) -> tuple[Resource, ...]:
        return tuple(self._resources)

    def extension(self) -> Skills:
        return Skills(list_skills=self.list_skills, get_skill=self.get_skill)

    async def list_skills(
        self,
        ctx: ServerRequestContext[typing.Any, typing.Any],
        params: ListSkillsParams,
    ) -> ListSkillsResult:
        del ctx, params
        return ListSkillsResult(skills=list(self._skills.values()))

    async def get_skill(
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
        return GetSkillResult(skill=skill)
