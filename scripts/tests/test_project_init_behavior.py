"""Project-init behavior, observed by running it against throwaway projects."""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from harness import PROJECT_END, PROJECT_START, TeamworkCase, snapshot  # noqa: E402


HEALTHY_AGENTS = "# Repository Guidelines\n\nMy own project rules.\n"


class ProjectInitTests(TeamworkCase):
    def project(self, name: str = "sample-project") -> Path:
        path = self.workdir / name
        path.mkdir(parents=True)
        return path

    def init(self, project: Path) -> subprocess.CompletedProcess[str]:
        return self.install("--project-root", str(project), "init-project")

    def init_ok(self, project: Path) -> None:
        done = self.init(project)
        self.assertEqual(done.returncode, 0, f"stdout:\n{done.stdout}\nstderr:\n{done.stderr}")

    def test_init_creates_only_the_two_instruction_files_and_is_idempotent(self) -> None:
        project = self.project()
        self.init_ok(project)
        self.assertEqual(
            sorted(entry.name for entry in project.iterdir()),
            ["AGENTS.md", "CLAUDE.md"],
        )
        first = snapshot(project)
        self.init_ok(project)
        self.init_ok(project)
        self.assertEqual(first, snapshot(project))

    def test_init_keeps_the_managed_block_single_and_leaves_the_rest_alone(self) -> None:
        project = self.project()
        self.write(project / "AGENTS.md", HEALTHY_AGENTS)
        self.init_ok(project)
        self.init_ok(project)
        text = (project / "AGENTS.md").read_text(encoding="utf-8")
        self.assertEqual(text.count(PROJECT_START), 1)
        self.assertEqual(text.count(PROJECT_END), 1)
        self.assertEqual(
            text.split(PROJECT_START, 1)[0].rstrip("\n"), HEALTHY_AGENTS.rstrip("\n")
        )

    # ---- bridge detection --------------------------------------------------

    def assert_bridge_decision(self, claude_md: str, expect_rewritten: bool) -> None:
        project = self.project()
        self.write(project / "AGENTS.md", HEALTHY_AGENTS)
        bridge = self.write(project / "CLAUDE.md", claude_md)
        self.init_ok(project)
        rewritten = bridge.read_text(encoding="utf-8") != claude_md
        self.assertEqual(rewritten, expect_rewritten)
        # Whatever it decided, deciding again must change nothing.
        after = snapshot(project)
        self.init_ok(project)
        self.assertEqual(after, snapshot(project))

    def test_an_active_agents_import_is_left_as_the_user_wrote_it(self) -> None:
        self.assert_bridge_decision("# Notes\n\n@AGENTS.md\n", expect_rewritten=False)

    def test_an_import_only_shown_inside_a_fenced_block_is_not_active(self) -> None:
        self.assert_bridge_decision(
            "# Notes\n\nExample of what to write:\n\n```markdown\n@AGENTS.md\n```\n",
            expect_rewritten=True,
        )

    def test_an_import_only_shown_inside_inline_code_is_not_active(self) -> None:
        self.assert_bridge_decision(
            "# Notes\n\nAdd `@AGENTS.md` yourself one day.\n", expect_rewritten=True
        )

    # ---- destructive inputs -------------------------------------------------

    def assert_clean_refusal(self, project: Path) -> None:
        before = snapshot(project)
        done = self.init(project)
        self.assertNotEqual(done.returncode, 0, f"stdout:\n{done.stdout}")
        self.assertEqual(before, snapshot(project), "a refused init still changed the project")
        # A refusal is a reported decision, not a crash: an uncaught exception
        # would put a multi-line traceback here.
        self.assertEqual(
            len(done.stderr.strip().splitlines()),
            1,
            f"refusal did not report a single clean reason:\n{done.stderr}",
        )

    def test_two_managed_blocks_are_refused(self) -> None:
        project = self.project()
        self.write(
            project / "AGENTS.md",
            f"{HEALTHY_AGENTS}\n{PROJECT_START}\none\n{PROJECT_END}\n"
            f"\n{PROJECT_START}\ntwo\n{PROJECT_END}\n",
        )
        self.assert_clean_refusal(project)

    def test_a_start_marker_without_its_end_is_refused(self) -> None:
        project = self.project()
        self.write(project / "AGENTS.md", f"{HEALTHY_AGENTS}\n{PROJECT_START}\nhalf a block\n")
        self.assert_clean_refusal(project)

    def test_an_end_marker_before_its_start_is_refused(self) -> None:
        project = self.project()
        self.write(
            project / "AGENTS.md",
            f"{HEALTHY_AGENTS}\n{PROJECT_END}\ninverted\n{PROJECT_START}\n",
        )
        self.assert_clean_refusal(project)

    def test_a_claude_md_symlinked_outside_the_project_is_refused(self) -> None:
        project = self.project()
        self.write(project / "AGENTS.md", HEALTHY_AGENTS)
        elsewhere = self.write(self.workdir / "elsewhere.md", "Someone else's file.\n")
        (project / "CLAUDE.md").symlink_to(elsewhere)
        before_target = elsewhere.read_bytes()
        self.assert_clean_refusal(project)
        self.assertTrue((project / "CLAUDE.md").is_symlink())
        self.assertEqual(elsewhere.read_bytes(), before_target)

    def test_a_project_name_that_would_break_the_block_is_refused(self) -> None:
        project = self.project("weird`name")
        self.write(project / "AGENTS.md", HEALTHY_AGENTS)
        self.assert_clean_refusal(project)
        # Nothing partially written, either.
        self.assertEqual(sorted(entry.name for entry in project.iterdir()), ["AGENTS.md"])


if __name__ == "__main__":
    unittest.main()
