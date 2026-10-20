import os
from pathlib import Path
import subprocess
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "editor-in-chief.sh"


class EditorRoutingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.bin = self.root / "bin"
        self.bin.mkdir()
        commands = {
            "osascript": '#!/bin/bash\nprintf "%s\\n" "$TEST_PROJECTS"\n',
            "xed": '#!/bin/bash\nprintf "xed\\n"; printf "%s\\n" "$@"; exit "${TEST_EXIT:-0}"\n',
            "code": '#!/bin/bash\nprintf "code\\n"; printf "%s\\n" "$@"; exit "${TEST_EXIT:-0}"\n',
        }
        for name, contents in commands.items():
            command = self.bin / name
            command.write_text(contents)
            command.chmod(0o755)

    def check_route(self, projects, target, editor, exit_code=0, suffix="", expected_args=None, wait=False, prefix_args=()):
        project_paths = [self.root / project for project in projects]
        for project in project_paths:
            project.mkdir(parents=True, exist_ok=True)
        target_path = self.root / target
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.touch()
        env = dict(
            os.environ,
            PATH=str(self.bin) + os.pathsep + os.environ["PATH"],
            TEST_PROJECTS="\n".join(map(str, project_paths)),
            TEST_EXIT=str(exit_code),
        )
        result = subprocess.run(
            ["/bin/bash", str(SCRIPT), *(["--wait"] if wait else []), *prefix_args, str(target_path) + suffix],
            env=env, text=True, capture_output=True,
        )
        self.assertEqual(result.returncode, exit_code, result.stderr)
        if expected_args is None:
            expected_args = [str(target_path.resolve())]
        else:
            expected_args = [arg.replace("{path}", str(target_path.resolve())) for arg in expected_args]
        self.assertEqual(result.stdout.splitlines(), [editor, *(["--wait"] if wait else []), *expected_args])

    def test_optional_wait(self):
        for editor, projects in [("xed", ["App/App.xcodeproj"]), ("code", [])]:
            for suffix in ["", ":42", ":42:5"]:
                with self.subTest(editor=editor, suffix=suffix):
                    if not suffix:
                        expected = ["{path}"]
                    elif editor == "xed":
                        expected = ["--line", "42", "{path}"]
                    else:
                        expected = ["--goto", "{path}" + suffix]
                    self.check_route(
                        projects, "App/main.cpp", editor, suffix=suffix,
                        expected_args=expected, wait=True,
                    )

    def test_editor_command_line_and_column(self):
        for editor, projects, expected in [
            ("xed", ["My Project/App.xcodeproj"], ["--line", "42", "{path}"]),
            ("code", [], ["--goto", "{path}:42:5"]),
        ]:
            with self.subTest(editor=editor):
                self.check_route(
                    projects, "My Project/Source/main.cpp", editor,
                    suffix=":42:5", expected_args=expected,
                )

    def test_line_without_column(self):
        for editor, projects, expected in [
            ("xed", ["App/App.xcodeproj"], ["--line", "12", "{path}"]),
            ("code", [], ["--goto", "{path}:12"]),
        ]:
            with self.subTest(editor=editor):
                self.check_route(projects, "App/main.cpp", editor, suffix=":12", expected_args=expected)

    def test_plus_line_argument(self):
        for editor, projects, prefix, expected in [
            ("xed", ["App/App.xcodeproj"], "+91", ["--line", "91", "{path}"]),
            ("xed", ["App/App.xcodeproj"], "+91:5", ["--line", "91", "{path}"]),
            ("code", [], "+91", ["--goto", "{path}:91"]),
            ("code", [], "+91:5", ["--goto", "{path}:91:5"]),
        ]:
            for wait in [False, True]:
                with self.subTest(editor=editor, prefix=prefix, wait=wait):
                    self.check_route(
                        projects, "App/main.cpp", editor, prefix_args=[prefix],
                        expected_args=expected, wait=wait,
                    )

    def test_plus_line_with_numeric_suffix_filename_is_literal(self):
        self.check_route(
            [], "App/name:42", "code", prefix_args=["+7"],
            expected_args=["--goto", "{path}:7"],
        )

    def test_colon_in_filename_with_position(self):
        self.check_route(
            [], "App/name:part.cpp", "code", suffix=":42:5",
            expected_args=["--goto", "{path}:42:5"],
        )

    def test_existing_filename_with_numeric_suffix_is_literal(self):
        self.check_route([], "App/name:42:5", "code")

    def test_nonnumeric_suffix_is_literal(self):
        self.check_route([], "App/name:part", "code")

    def test_spaces_in_project_path_do_not_match_unrelated_files(self):
        self.check_route(["My Project/App.xcodeproj"], "Other/main.cpp", "code")

    def test_spaces_and_commas_in_multiple_project_paths(self):
        self.check_route(
            ["First/App.xcodeproj", "My Project, Two/App.xcodeproj"],
            "My Project, Two/Source/main.cpp", "xed",
        )

    def test_sibling_with_shared_prefix(self):
        self.check_route(["App/App.xcodeproj"], "AppOther/main.cpp", "code")

    def test_juce_project(self):
        self.check_route(["App/Builds/MacOSX/App.xcodeproj"], "App/Source/main.cpp", "xed")

    def test_cmake_project(self):
        self.check_route(["App/build/App.xcodeproj"], "App/src/main.cpp", "xed")

    def test_no_projects(self):
        self.check_route([], "App/main.cpp", "code")

    def test_project_paths_are_resolved_like_file_paths(self):
        (self.root / "Actual").mkdir()
        (self.root / "Linked").symlink_to(self.root / "Actual", target_is_directory=True)
        self.check_route(["Linked/App.xcodeproj"], "Actual/main.cpp", "xed")

    def test_editor_failure_is_preserved(self):
        for projects, editor in [(["App/App.xcodeproj"], "xed"), ([], "code")]:
            with self.subTest(editor=editor):
                self.check_route(projects, "App/main.cpp", editor, exit_code=7)


if __name__ == "__main__":
    unittest.main()
