from __future__ import annotations

import dataclasses
import json
import pathlib

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent


class XFailGroup(dict[str, set[str]]):
    def add(self, board_variant: str, test_name: str) -> None:
        names = self.get(test_name, set())
        names.add(board_variant)
        self[test_name] = names

    @property
    def to_dict(self) -> dict[str, list[str]]:
        return {k: sorted(v) for k, v in self.items()}

    @staticmethod
    def from_dict(dict_group: dict[str, list[str]]) -> XFailGroup:
        return XFailGroup({k: set(v) for k, v in dict_group.items()})


class XFailList(dict[str, XFailGroup]):
    def get_group(self, testgroup: str) -> XFailGroup:
        g = self.get(testgroup, None)
        if g is None:
            g = XFailGroup()
        self[testgroup] = g
        return g

    @property
    def to_dict(self) -> dict[str, dict[str, list[str]]]:
        return {k: v.to_dict for k, v in self.items()}

    def write(self, filename: pathlib.Path) -> None:
        with filename.open("w") as f:
            json.dump(obj=self.to_dict, fp=f, sort_keys=True, indent=4)

    def match(self, testgroup: str, test_name: str, board_variant: str) -> bool:
        try:
            return board_variant in self[testgroup][test_name]
        except KeyError:
            return False

    @staticmethod
    def from_dict(dict_report: dict[str, dict[str, list[str]]]) -> XFailList:
        return XFailList({k: XFailGroup.from_dict(v) for k, v in dict_report.items()})

    @staticmethod
    def factory(filename: pathlib.Path) -> XFailList:
        with filename.open("r") as f:
            dict_report = json.load(fp=f)
            return XFailList.from_dict(dict_report)


@dataclasses.dataclass(slots=True)
class XFailFile:
    filename: pathlib.Path
    xfail_list: XFailList

    @staticmethod
    def factory(filename: pathlib.Path) -> XFailFile:
        return XFailFile(
            filename=filename,
            xfail_list=XFailList.factory(filename=filename),
        )

    @staticmethod
    def factory_template(filename: str | None) -> XFailFile | None:
        if filename is None:
            return None
        return XFailFile.factory(DIRECTORY_OF_THIS_FILE / filename)


class XFailFiles(list[XFailFile]):
    @staticmethod
    def factory_from_filesystem() -> XFailFiles:
        return XFailFiles(
            [
                XFailFile.factory(filename=filename)
                for filename in DIRECTORY_OF_THIS_FILE.glob("*.json")
            ]
        )

    def get_filelist(
        self,
        testgroup: str,
        test_name: str,
        board_variant: str,
    ) -> list[str]:
        list_files: list[str] = []
        for xfail_file in self:
            if xfail_file.xfail_list.match(
                testgroup=testgroup,
                test_name=test_name,
                board_variant=board_variant,
            ):
                list_files.append(xfail_file.filename.name)
        return list_files
