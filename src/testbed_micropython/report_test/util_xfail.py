"""
Example XFailFile:

{
    // Test "*" on testgroup
    "*": {
        "testgroup.py": [
            "TESTGROUP"
        ]
    },
    "RUN-TESTS_STANDARD": {
        // Test "*" on test_name
        "*": [
            "PYBV11"
        ],
        "extmod/socket_udp_nonblock.py": [
            "ESP32_C3_DEVKIT",
            "ESP32_S3_DEVKIT",
            "LOLIN_C3_MINI",
        ],
        "test_name.py": [
            // Test "*" on board_variant
            "*"
        ]
    },
}

Note that there may be comment (//).
Note the CATCHALL ('*')

"""

from __future__ import annotations

import dataclasses
import json
import pathlib
import re

DIRECTORY_OF_THIS_FILE = pathlib.Path(__file__).parent

CATCHALL = "*"


class XFailBoardVariant(set[str]):
    def match(self, board_variant: str) -> bool:
        """
        Test on level 'board_variant' (ESP32_C3_DEVKIT, ESP32_S3_DEVKIT)
        """
        for pattern in (board_variant, CATCHALL):
            if pattern in self:
                return True
        return False


class XFailGroup(dict[str, XFailBoardVariant]):
    def add(self, board_variant: str, test_name: str) -> None:
        names = self.get(test_name)
        if names is None:
            names = XFailBoardVariant()
        names.add(board_variant)
        self[test_name] = XFailBoardVariant(names)

    def match(self, test_name: str, board_variant: str) -> bool:
        """
        Test on level 'test_name' (extmod/socket_udp_nonblock.py, )
        """
        for pattern in (test_name, CATCHALL):
            xfail_boardvariant = self.get(pattern)
            if xfail_boardvariant is not None:
                matched = xfail_boardvariant.match(board_variant=board_variant)
                if matched:
                    return True
        return False

    @property
    def to_dict(self) -> dict[str, list[str]]:
        return {k: sorted(v) for k, v in self.items()}

    @staticmethod
    def from_dict(dict_group: dict[str, list[str]]) -> XFailGroup:
        return XFailGroup({k: XFailBoardVariant(v) for k, v in dict_group.items()})


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
        """
        Finds an entry matching 'testgroup', 'test_name' and 'board_variant' in the json file.
        return True if found.
        Also considers CATCHALL ('*').
        """

        def match() -> bool:
            """
            Test on level 'testgroup' (RUN-TESTS_STANDARD, RUN-TESTS_STANDARD_NATIVE)
            """
            for pattern in (testgroup, CATCHALL):
                xfailgroup = self.get(pattern)
                if xfailgroup is not None:
                    matched = xfailgroup.match(
                        test_name=test_name,
                        board_variant=board_variant,
                    )
                    if matched:
                        return True
            return False

        return match()

    @staticmethod
    def from_dict(dict_report: dict[str, dict[str, list[str]]]) -> XFailList:
        return XFailList({k: XFailGroup.from_dict(v) for k, v in dict_report.items()})

    @staticmethod
    def factory(filename: pathlib.Path) -> XFailList:
        re_comment = re.compile(r"^(.*?)//")

        def remove_comment(line: str) -> str:
            line = line.strip()
            match = re_comment.match(line)
            if match:
                return match.groups()[0]
            return line

        with filename.open("r") as f:
            lines = [remove_comment(line) for line in f.readlines()]
        json_text = "\n".join(lines)
        dict_report = json.loads(json_text)
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
