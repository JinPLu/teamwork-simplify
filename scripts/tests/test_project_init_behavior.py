"""Project-init behavior, observed by running it against throwaway projects."""

from __future__ import annotations

import re
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from harness import (  # noqa: E402
    PROJECT_END,
    PROJECT_START,
    ROOT,
    TeamworkCase,
    snapshot,
    split_managed,
)


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

    def test_init_creates_only_the_three_instruction_files_and_is_idempotent(self) -> None:
        project = self.project()
        self.init_ok(project)
        self.assertEqual(
            sorted(entry.name for entry in project.iterdir()),
            ["AGENTS.md", "CLAUDE.md", "docs"],
        )
        self.assertTrue((project / "docs" / "teamwork" / "README.md").is_file())
        first = snapshot(project)
        self.init_ok(project)
        self.init_ok(project)
        self.assertEqual(first, snapshot(project))

    def test_init_writes_a_claude_bridge_that_imports_both_agents_and_the_project_readme(
        self,
    ) -> None:
        project = self.project()
        self.init_ok(project)
        bridge = (project / "CLAUDE.md").read_text(encoding="utf-8")
        self.assertIn("@AGENTS.md", bridge)
        self.assertIn("@docs/teamwork/README.md", bridge)

    def test_init_leaves_an_existing_project_readme_untouched(self) -> None:
        project = self.project()
        custom = "# My Own Notes\n\nDo not overwrite this.\n"
        self.write(project / "docs" / "teamwork" / "README.md", custom)
        self.init_ok(project)
        self.assertEqual(
            (project / "docs" / "teamwork" / "README.md").read_text(encoding="utf-8"),
            custom,
        )
        # Re-running init must not touch it either.
        self.init_ok(project)
        self.assertEqual(
            (project / "docs" / "teamwork" / "README.md").read_text(encoding="utf-8"),
            custom,
        )

    def test_init_does_not_precreate_kind_subdirectories(self) -> None:
        project = self.project()
        self.init_ok(project)
        docs = project / "docs" / "teamwork"
        self.assertEqual(sorted(entry.name for entry in docs.iterdir()), ["README.md"])

    def test_the_placeholder_constraints_section_is_seeded_outside_the_managed_block(
        self,
    ) -> None:
        project = self.project()
        self.init_ok(project)
        text = (project / "AGENTS.md").read_text(encoding="utf-8")
        _before, inside, after = split_managed(text, PROJECT_START, PROJECT_END)
        self.assertNotIn("Project-specific constraints", inside)
        subsection = re.search(r"^## .+$", after, re.M)
        self.assertIsNotNone(subsection, f"no project-specific section found after the block:\n{after}")
        placeholders = re.findall(r"^- .+$", after[subsection.end() :], re.M)
        self.assertGreaterEqual(
            len(placeholders), 1, f"seeded section has no placeholder line:\n{after}"
        )

    def test_a_filled_in_constraints_seed_survives_initialize_and_refresh_context(
        self,
    ) -> None:
        project = self.project()
        self.init_ok(project)
        agents_path = project / "AGENTS.md"
        seeded = agents_path.read_text(encoding="utf-8")
        placeholder = "- <add a project-specific constraint here>\n- <add another one here>\n"
        self.assertIn(placeholder, seeded)
        real_constraint = "- No commits containing a TODO marker.\n"
        filled = seeded.replace(placeholder, real_constraint)
        self.assertNotEqual(filled, seeded)
        agents_path.write_text(filled, encoding="utf-8")

        self.init_ok(project)
        self.assertEqual(agents_path.read_text(encoding="utf-8"), filled)

        # refresh-context is not exposed through install.sh; run the real
        # script directly for this leg, same as init-project.sh would.
        refreshed = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "init-project-files.py"),
                "--project-root",
                str(project),
                "refresh-context",
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(refreshed.returncode, 0, refreshed.stderr)
        self.assertEqual(agents_path.read_text(encoding="utf-8"), filled)

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
        project = self.project()
        self.write(project / "AGENTS.md", HEALTHY_AGENTS)
        original = "# Notes\n\n@AGENTS.md\n"
        bridge = self.write(project / "CLAUDE.md", original)
        self.init_ok(project)
        text = bridge.read_text(encoding="utf-8")
        # The user's own line is untouched, character for character...
        self.assertIn(original, text)
        # ...it is not duplicated by a second @AGENTS.md import...
        self.assertEqual(text.count("@AGENTS.md"), 1)
        # ...and the README import, which has no other source, still lands.
        self.assertIn("@docs/teamwork/README.md", text)
        # Repeated deciding must change nothing further, byte for byte.
        stable = bridge.read_text(encoding="utf-8")
        self.init_ok(project)
        self.init_ok(project)
        self.assertEqual(bridge.read_text(encoding="utf-8"), stable)

    def test_the_bridge_is_byte_stable_across_repeated_init_from_scratch(self) -> None:
        project = self.project()
        self.init_ok(project)
        bridge = project / "CLAUDE.md"
        first = bridge.read_text(encoding="utf-8")
        self.init_ok(project)
        self.init_ok(project)
        self.assertEqual(bridge.read_text(encoding="utf-8"), first)

    def test_a_claude_md_symlinked_to_agents_reports_the_readme_import_limitation(
        self,
    ) -> None:
        project = self.project()
        self.write(project / "AGENTS.md", HEALTHY_AGENTS)
        bridge = project / "CLAUDE.md"
        bridge.symlink_to(project / "AGENTS.md")
        done = self.init(project)
        self.assertEqual(done.returncode, 0, f"stdout:\n{done.stdout}\nstderr:\n{done.stderr}")
        self.assertIn(str(bridge), done.stdout)
        self.assertIn("docs/teamwork/README.md", done.stdout)
        # The symlink itself is left exactly as it was: nothing can be added
        # to it without breaking it.
        self.assertTrue(bridge.is_symlink())
        self.assertEqual(bridge.resolve(), (project / "AGENTS.md").resolve())

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
