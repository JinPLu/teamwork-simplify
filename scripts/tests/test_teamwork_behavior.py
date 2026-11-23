"""Behavior tests for Teamwork installation, policy isolation, refresh, uninstall, and doctor."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from harness import POLICY_END, POLICY_START, ROOT, TeamworkCase, snapshot, split_managed  # noqa: E402


class InstallAndParityTests(TeamworkCase):
    SKILL_PATHS = {
        "antigravity": ".gemini/config/skills/teamwork-collaborate",
        "codex": ".agents/skills/teamwork-collaborate",
        "claude": ".claude/skills/teamwork-collaborate",
        "cursor": ".cursor/skills/teamwork-collaborate",
    }
    POLICY_PATHS = {
        "antigravity": ".gemini/GEMINI.md",
        "codex": ".codex/AGENTS.md",
        "claude": ".claude/CLAUDE.md",
    }

    def test_all_four_hosts_receive_identical_skill_and_canonical_policy(self) -> None:
        self.cli_ok("all")

        expected_skill = (ROOT / "skills" / "teamwork-collaborate" / "SKILL.md").read_bytes()
        expected_policy = self.cli_ok("policy").stdout

        for host, rel_skill in self.SKILL_PATHS.items():
            skill_dir = self.home / rel_skill
            self.assertEqual((skill_dir / "SKILL.md").read_bytes(), expected_skill, host)
            self.assertTrue((skill_dir / ".teamwork-version").is_file(), host)

        for host, rel_policy in self.POLICY_PATHS.items():
            text = (self.home / rel_policy).read_text(encoding="utf-8")
            self.assertEqual(text, expected_policy, host)

    def test_agy_alias_and_multi_host_selection_only_touch_requested_hosts(self) -> None:
        self.cli_ok("agy", "codex")

        self.assertTrue((self.home / self.SKILL_PATHS["antigravity"] / "SKILL.md").is_file())
        self.assertTrue((self.home / self.SKILL_PATHS["codex"] / "SKILL.md").is_file())
        self.assertFalse((self.home / self.SKILL_PATHS["claude"]).exists())
        self.assertFalse((self.home / self.SKILL_PATHS["cursor"]).exists())

    def test_link_mode_symlinks_skill_without_writing_into_checkout(self) -> None:
        checkout_before = snapshot(ROOT / "skills")
        self.cli_ok("--link", "agy", "cursor")

        for host in ("antigravity", "cursor"):
            dest = self.home / self.SKILL_PATHS[host]
            self.assertTrue(dest.is_symlink(), host)
            self.assertEqual(dest.resolve(), (ROOT / "skills" / "teamwork-collaborate").resolve())
        self.assertEqual(checkout_before, snapshot(ROOT / "skills"))


class IdempotenceAndIsolationTests(TeamworkCase):
    USER_RULES = (
        "# Personal Rules\n\n"
        "Keep answers direct.\n\n"
        "<!-- SERVERPILOT_GLOBAL_START -->\n"
        "Use the local serverpilot MCP.\n"
        "<!-- SERVERPILOT_GLOBAL_END -->\n"
    )

    def test_repeated_installs_are_byte_identical_from_first_run(self) -> None:
        gemini = self.write(self.home / ".gemini" / "GEMINI.md", self.USER_RULES)
        codex = self.write(self.home / ".codex" / "AGENTS.md", self.USER_RULES)

        self.cli_ok("all")
        first = snapshot(self.home)
        self.cli_ok("all")
        second = snapshot(self.home)
        self.cli_ok("all")
        third = snapshot(self.home)

        self.assertEqual(first, second)
        self.assertEqual(second, third)

        for path in (gemini, codex):
            before, _inside, after = split_managed(path.read_text(encoding="utf-8"))
            self.assertEqual(before.rstrip("\n"), self.USER_RULES.rstrip("\n"))
            self.assertEqual(after.strip(), "")

    def test_middle_and_top_block_placements_stay_idempotent_and_preserve_neighbors(self) -> None:
        policy_block = self.cli_ok("policy").stdout
        sandwiched = "# Header\n\n" + policy_block + "\n# Footer\nStay intact.\n"
        path = self.write(self.home / ".gemini" / "GEMINI.md", sandwiched)

        self.cli_ok("agy")
        once = path.read_text(encoding="utf-8")
        self.cli_ok("agy")
        twice = path.read_text(encoding="utf-8")

        self.assertEqual(once, twice)
        before, _inside, after = split_managed(once)
        self.assertEqual(before.strip(), "# Header")
        self.assertEqual(after.strip(), "# Footer\nStay intact.")


class OwnershipAndPreflightTests(TeamworkCase):
    def test_refuses_unmarked_or_modified_skill_dir_unless_forced(self) -> None:
        custom = self.home / ".gemini" / "config" / "skills" / "teamwork-collaborate"
        self.write(
            custom / "SKILL.md",
            "---\nname: teamwork-collaborate\ndescription: Use when testing.\n---\nCustom fork.\n",
        )
        self.write(custom / "notes.md", "Do not delete automatically.\n")
        before = snapshot(self.home)

        failed = self.cli("agy")
        self.assertEqual(failed.returncode, 1)
        self.assertEqual(before, snapshot(self.home))

        self.cli_ok("--force", "agy")
        self.assertFalse((custom / "notes.md").exists())
        self.assertTrue((custom / ".teamwork-version").is_file())

    def test_multi_host_preflight_aborts_before_any_partial_write(self) -> None:
        # Corrupt Claude's policy markers and confirm `all` writes nothing to Antigravity or Codex.
        self.write(self.home / ".claude" / "CLAUDE.md", f"{POLICY_START}\nunclosed\n")
        before = snapshot(self.home)

        failed = self.cli("all")
        self.assertEqual(failed.returncode, 1)
        self.assertEqual(before, snapshot(self.home))


class RefreshAndUninstallTests(TeamworkCase):
    def test_refresh_updates_only_installed_hosts_and_preserves_install_modes(self) -> None:
        empty_refresh = self.cli("refresh")
        self.assertEqual(empty_refresh.returncode, 1)

        older = self.checkout_copy("3.9.0")
        self.cli_ok("--link", "agy", checkout=older)
        self.cli_ok("--copy", "codex", checkout=older)

        # Refresh from the current checkout (4.0.0): agy stays a symlink (retargeted to ROOT),
        # codex stays a copy updated to 4.0.0, claude & cursor remain uninstalled.
        self.cli_ok("refresh")

        agy_skill = self.home / ".gemini" / "config" / "skills" / "teamwork-collaborate"
        codex_skill = self.home / ".agents" / "skills" / "teamwork-collaborate"
        self.assertTrue(agy_skill.is_symlink())
        self.assertEqual(agy_skill.resolve(), (ROOT / "skills" / "teamwork-collaborate").resolve())
        self.assertFalse(codex_skill.is_symlink())
        self.assertEqual(
            (codex_skill / ".teamwork-version").read_text(encoding="utf-8").strip(),
            (ROOT / "VERSION").read_text(encoding="utf-8").strip(),
        )
        self.assertFalse((self.home / ".claude").exists())
        self.assertFalse((self.home / ".cursor").exists())

    def test_uninstall_restores_user_rules_and_deletes_empty_policy_files(self) -> None:
        user_text = "# Keep me\n\nAlways test edge cases.\n"
        gemini = self.write(self.home / ".gemini" / "GEMINI.md", user_text)

        self.cli_ok("agy", "codex")
        self.assertTrue((self.home / ".codex" / "AGENTS.md").is_file())

        self.cli_ok("uninstall", "agy", "codex")

        self.assertEqual(gemini.read_text(encoding="utf-8"), user_text)
        self.assertFalse((self.home / ".gemini" / "config" / "skills" / "teamwork-collaborate").exists())
        self.assertFalse((self.home / ".codex" / "AGENTS.md").exists())
        self.assertFalse((self.home / ".agents" / "skills" / "teamwork-collaborate").exists())


class DoctorTests(TeamworkCase):
    def test_clean_environment_and_fresh_install_report_zero_errors(self) -> None:
        project = self.temp_dir("project")
        code, report = self.doctor_json("--project", str(project))
        self.assertEqual(code, 0)
        self.assertEqual(report["summary"]["error"], 0)
        self.assertEqual(
            sum(1 for x in report["global"] if x["check"] == "host-disabled"), 4
        )

        self.cli_ok("agy", "codex")
        code, report = self.doctor_json("--project", str(project))
        self.assertEqual(code, 0)
        self.assertEqual(report["summary"]["error"], 0)

    def test_doctor_detects_global_policy_and_skill_drift(self) -> None:
        project = self.temp_dir("project")
        self.cli_ok("agy")
        policy_file = self.home / ".gemini" / "GEMINI.md"
        skill_file = self.home / ".gemini" / "config" / "skills" / "teamwork-collaborate" / "SKILL.md"

        original_policy = policy_file.read_text(encoding="utf-8")
        for broken_text, expected_check in (
            ("# Only user rules\n", "policy-missing"),
            (f"{POLICY_START}\nbroken\n", "policy-malformed"),
            (original_policy.replace("Chinese", "French"), "policy-drift"),
        ):
            with self.subTest(expected_check=expected_check):
                policy_file.write_text(broken_text, encoding="utf-8")
                code, report = self.doctor_json("--project", str(project))
                self.assertEqual(code, 1)
                checks = [x["check"] for x in report["global"] if x["severity"] == "error"]
                self.assertEqual(checks, [expected_check])
        policy_file.write_text(original_policy, encoding="utf-8")

        skill_file.write_text(skill_file.read_text(encoding="utf-8") + "\nDrift.\n", encoding="utf-8")
        code, report = self.doctor_json("--project", str(project))
        self.assertEqual(code, 1)
        self.assertEqual(
            [x["check"] for x in report["global"] if x["severity"] == "error"],
            ["skill-drift"],
        )

    def test_project_checks_require_zero_init_and_grade_links_accurately(self) -> None:
        project = self.temp_dir("project")
        # Plain project with no docs/teamwork is completely clean without any init step.
        code, report = self.doctor_json("--project", str(project))
        self.assertEqual(code, 0)
        self.assertEqual(report["projects"][0]["findings"], [])

        # Orphan document without README.md is an error.
        self.write(project / "docs" / "teamwork" / "discussions" / "topic.md", "# Topic\n")
        code, report = self.doctor_json("--project", str(project))
        self.assertEqual(code, 1)
        self.assertEqual(
            [f["check"] for f in report["projects"][0]["findings"]], ["entry-missing"]
        )

        # Valid links, anchors, URLs, code examples, and missing runtime outputs (warn only).
        self.write(
            project / "docs" / "teamwork" / "README.md",
            "# State\n\n"
            "- [Topic](discussions/topic.md#top)\n"
            "- [Repo relative](docs/teamwork/discussions/topic.md)\n"
            "- [Cleaned run](../../outputs/exp-01/README.md)\n"
            "- [Web](https://example.com/doc.md)\n"
            "- `[Inline](missing.md)`\n"
            "```md\n[Fenced](missing.md)\n```\n",
        )
        code, report = self.doctor_json("--project", str(project))
        self.assertEqual(code, 0)
        findings = report["projects"][0]["findings"]
        self.assertEqual([f["check"] for f in findings], ["missing-artifact-link"])
        self.assertEqual(findings[0]["severity"], "warn")

        # Broken tracked document link is an error, and doctor mutates nothing.
        self.write(
            project / "docs" / "teamwork" / "README.md",
            "- [Broken](plans/missing-plan.md)\n",
        )
        before_project = snapshot(project)
        code, report = self.doctor_json("--project", str(project))
        self.assertEqual(code, 1)
        self.assertEqual(
            [f["check"] for f in report["projects"][0]["findings"]], ["dead-link"]
        )
        self.assertEqual(before_project, snapshot(project))

    def test_auto_discovery_prunes_artifacts_backups_and_archives(self) -> None:
        docs = self.home / "Documents"
        active = docs / "ActiveProject"
        self.write(active / "docs" / "teamwork" / "README.md", "# Active\n")
        for ignored in (
            docs / "ActiveProject" / "artifacts" / "snap" / "docs" / "teamwork" / "orphan.md",
            docs / "ActiveProject" / "build" / "backups" / "docs" / "teamwork" / "orphan.md",
            docs / "_Archive" / "OldRepo" / "docs" / "teamwork" / "orphan.md",
        ):
            self.write(ignored, "# Snapshot\n")

        code, report = self.doctor_json()
        self.assertEqual(code, 0)
        scanned = {p["path"] for p in report["projects"]}
        self.assertIn(str(active.resolve()), scanned)
        self.assertEqual(len(scanned), 2)  # ActiveProject + REPO_ROOT


class CommandLineValidationTests(TeamworkCase):
    def assert_usage_error(self, *args: str) -> None:
        done = self.cli(*args)
        self.assertEqual(done.returncode, 2, f"args={args}\nstdout={done.stdout}\nstderr={done.stderr}")
        self.assertEqual(snapshot(self.home), {})

    def test_invalid_or_removed_arguments_exit_two_without_side_effects(self) -> None:
        self.assert_usage_error()
        self.assert_usage_error("unknown-host")
        self.assert_usage_error("all", "codex")
        self.assert_usage_error("refresh", "agy")
        self.assert_usage_error("--copy", "--link", "agy")
        self.assert_usage_error("init-project")
        self.assert_usage_error("--project-root", str(self.workdir), "init-project")
        self.assert_usage_error("doctor", "--unknown")
        self.assert_usage_error("doctor", "--project", str(self.workdir / "absent"))
        self.assert_usage_error("policy", "--unknown")
        self.assert_usage_error("uninstall")


if __name__ == "__main__":
    unittest.main()
