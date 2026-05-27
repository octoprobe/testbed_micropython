from __future__ import annotations

import dataclasses
import logging
import pathlib
import re

import yaml

logger = logging.getLogger(__file__)
YAML_ON = True
"""
This corresponds to the yaml key "on:"
"""

RE_WORKFLOW_YML = re.compile(r"ports_(?P<port>.*?)\.yml")
"""
Examples:
* ports_renesas-ra.yml
* ports_qemu.yml
"""


@dataclasses.dataclass(slots=True, frozen=True)
class YamlFile:
    filename: pathlib.Path
    port: str
    paths: list[str]

    def __post_init__(self) -> None:
        assert isinstance(self.filename, pathlib.Path)
        assert isinstance(self.port, str)
        assert isinstance(self.paths, list)

    def hit_file(self, file_modified: str) -> bool:
        for path in self.paths:
            # GitHub-style paths use forward slashes
            file_posix = pathlib.PurePosixPath(file_modified.lstrip("./"))
            pat = path.lstrip("./")
            if file_posix.match(pat):
                logger.error(
                    f"matched: file={file_modified} pattern={path} yaml_file={self.filename.name}"
                )
                return True

        return False

    @staticmethod
    def factory(filename: pathlib.Path) -> YamlFile | None:
        match = RE_WORKFLOW_YML.match(filename.name)
        if match is None:
            return None
        port = match.group("port")

        yaml_content = filename.read_text()
        data = yaml.safe_load(yaml_content)
        if data is None:
            return None

        # Navigate to on.pull_request.paths
        current = data
        for key in (YAML_ON, "pull_request", "paths"):
            current = current[key]

        assert isinstance(current, list)
        return YamlFile(filename=filename, port=port, paths=current)


class YamlFiles(list[YamlFile]):
    def micropython_ports(self, files_modified: set[str]) -> list[str]:
        set_ports: set[str] = set()
        for yaml_file in self:
            for file_modified in files_modified:
                if yaml_file.hit_file(file_modified=file_modified):
                    set_ports.add(yaml_file.port)
        return sorted(set_ports)

    @staticmethod
    def factory(directory: pathlib.Path) -> YamlFiles:
        files = YamlFiles()
        for filename_yml in directory.glob("*.yml"):
            yaml_file = YamlFile.factory(filename_yml)
            if yaml_file is None:
                continue
            files.append(yaml_file)
        return files
