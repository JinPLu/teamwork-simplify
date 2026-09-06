"""Installer behavior, observed by running it against a throwaway HOME."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from harness import (  # noqa: E402
    CLAUDE_POLICY_END,
    CLAUDE_POLICY_START,
    CODEX_POLICY_END,
    CODEX_POLICY_START,
    CURSOR_POLICY_END,
    CURSOR_POLICY_START,
    PROJECT_END,
    PROJECT_START,
    ROOT,
    TeamworkCase,
    snapshot,
    split_managed,
)


# A user's own Skill that happens to carry a name on the retired list. Its body
# never mentions Teamwork, so no ownership signature can claim it.
FOREIGN_GRILL = "Ask five hard questions about the change under review."
# `teamwork` is the most generic retired name of all; a squad-ritual Skill of
# that name is exactly the case a marker-only ownership check destroys.
FOREIGN_ROUTER = "Facilitate a standup: blockers, progress, next step."
# A retired Skill as a previous Teamwork release actually installed it.
OWNED_RETIRED_SKILL = "The Teamwork planning Skill, retired in a later release."


class RetiredCleanupTests(TeamworkCase):
    def test_retired_cleanup_preserves_entries_this_checkout_never_installed(self) -> None:
        """The 1.0.0 blocker: a user's own Skill was deleted by name alone."""
        self.install_ok("claude")
        skills = self.home / ".claude" / "skills"
        agents = self.home / ".claude" / "agents"

        self.write_skill(skills, "grill-me", "grill-me", FOREIGN_GRILL)
        notes = self.write(skills / "grill-me" / "notes.md", "My own notes.\n")
        self.write_skill(skills, "teamwork", "teamwork", FOREIGN_ROUTER)
        # A retired *name* whose directory holds only the user's own files.
        checklist = self.write(skills / "teamwork-review" / "CHECKLIST.md", "My checklist.\n")
        # A retired agent name that is not a Teamwork role profile.
        reviewer = self.write_agent(agents, "reviewer", "You review pull requests for my team.")

        before = {
            "grill-me": (skills / "grill-me" / "SKILL.md").read_bytes(),
            "notes": (notes).read_bytes(),
            "teamwork": (skills / "teamwork" / "SKILL.md").read_bytes(),
            "checklist": (checklist).read_bytes(),
            "reviewer": (reviewer).read_bytes(),
        }

        self.install_ok("claude")
        self.install_ok("claude")

        self.assertTrue((skills / "grill-me" / "SKILL.md").is_file())
        self.assertTrue((skills / "teamwork" / "SKILL.md").is_file())
        self.assertEqual(
            before,
            {
                "grill-me": (skills / "grill-me" / "SKILL.md").read_bytes(),
                "notes": (notes).read_bytes(),
                "teamwork": (skills / "teamwork" / "SKILL.md").read_bytes(),
                "checklist": (checklist).read_bytes(),
                "reviewer": (reviewer).read_bytes(),
            },
        )

    def test_retired_cleanup_removes_copies_a_previous_release_installed(self) -> None:
        self.install_ok("claude")
        skills = self.home / ".claude" / "skills"
        agents = self.home / ".claude" / "agents"

        retired_skill = self.write_skill(
            skills, "teamwork-plan", "teamwork-plan", OWNED_RETIRED_SKILL
        )
        retired_agent = self.write_agent(
            agents, "researcher", "You are the Teamwork Researcher."
        )
        self.assertTrue(retired_skill.is_dir())
        self.assertTrue(retired_agent.is_file())

        self.install_ok("claude")

        self.assertFalse(retired_skill.exists())
        self.assertFalse(retired_agent.exists())

    def test_retired_cleanup_removes_a_symlinked_copy_but_not_a_foreign_link(self) -> None:
        """--link installs leave symlinks; ownership follows the link target."""
        self.install_ok("--link", "claude")
        skills = self.home / ".claude" / "skills"

        owned = skills / "teamwork-goal"
        owned.symlink_to(self.workdir / "some-checkout" / "skills" / "teamwork-goal")
        foreign = skills / "teamwork-init"
        foreign.symlink_to(self.workdir)

        self.install_ok("--link", "claude")

        self.assertFalse(owned.is_symlink())
        self.assertTrue(foreign.is_symlink())
        self.assertTrue(self.workdir.is_dir())

    def test_install_refuses_to_replace_an_unowned_current_skill(self) -> None:
        """A same-named Skill without Teamwork ownership markers is not ours."""
        skills = self.home / ".claude" / "skills"
        self.write_skill(skills, "teamwork-collaborate", "teamwork-collaborate", "My own fork.")
        mine = self.write(skills / "teamwork-collaborate" / "mine.md", "My own notes.\n")
        before = snapshot(skills)

        done = self.install("claude")

        self.assertNotEqual(done.returncode, 0, done.stdout)
        self.assertEqual(before, snapshot(skills))
        self.assertTrue(mine.is_file())


class IdempotenceTests(TeamworkCase):
    def test_repeated_installs_are_byte_identical_from_the_second_run(self) -> None:
        self.install_ok("all")
        self.install_ok("all")
        second = snapshot(self.home)
        self.install_ok("all")
        third = snapshot(self.home)
        self.install_ok("all")
        fourth = snapshot(self.home)

        self.assertEqual(second, third)
        self.assertEqual(third, fourth)


class ManagedBlockIsolationTests(TeamworkCase):
    #  Two sentences a 1.0.0 migration hack deleted by literal match, from
    #  *outside* the managed block. Here they are the user's own text.
    USER_FILE = (
        "# My own global rules\n"
        "\n"
        "Always greet the cat.\n"
        "\n"
        "No user needs to specify sub-agents for distribution; default assignment is used.\n"
        "All code runs on a remote server; the local environment only supports basic"
        " testing and syntax checking.\n"
        "\n"
        "<!-- MY_OWN_BLOCK_START -->\n"
        "Never touch anything between my own markers.\n"
        "<!-- MY_OWN_BLOCK_END -->\n"
        "\n"
        "A closing note of mine.\n"
    )

    def test_install_rewrites_only_between_its_own_markers(self) -> None:
        claude = self.write(self.home / ".claude" / "CLAUDE.md", self.USER_FILE)
        codex = self.write(self.home / ".codex" / "AGENTS.md", self.USER_FILE)

        self.install_ok("all")

        for path, start, end in (
            (claude, CLAUDE_POLICY_START, CLAUDE_POLICY_END),
            (codex, CODEX_POLICY_START, CODEX_POLICY_END),
        ):
            text = path.read_text(encoding="utf-8")
            before, _inside, after = split_managed(text, start, end)
            self.assertEqual(
                before.rstrip("\n"),
                self.USER_FILE.rstrip("\n"),
                f"{path} lost or altered content outside the managed block",
            )
            self.assertEqual(after.strip(), "")

    def test_repeated_installs_do_not_grow_a_file_that_already_had_user_text(self) -> None:
        claude = self.write(self.home / ".claude" / "CLAUDE.md", self.USER_FILE)
        codex = self.write(self.home / ".codex" / "AGENTS.md", self.USER_FILE)

        self.install_ok("all")
        sizes = (claude.stat().st_size, codex.stat().st_size)
        first = (claude.read_bytes(), codex.read_bytes())
        for _ in range(3):
            self.install_ok("all")
        self.assertEqual(sizes, (claude.stat().st_size, codex.stat().st_size))
        self.assertEqual(first, (claude.read_bytes(), codex.read_bytes()))


class AgentRetirementTests(TeamworkCase):
    """Teamwork installs no agents; every one an earlier release left is removed.

    The removal must key on what the file says, not on what it is called. A
    user may keep an agent whose name collides exactly with a retired Teamwork
    one, and that file has to survive: this is the same class of mistake as the
    skill-root cleanup that once deleted an unrelated Skill by name.
    """

    ROLES = ("challenger", "worker", "writer")

    def previous_release_agents(self) -> tuple[Path, Path, Path]:
        """The three markdown role files as the last release wrote them."""
        claude = self.home / ".claude" / "agents"
        cursor = self.home / ".cursor" / "agents"
        codex = self.home / ".codex" / "agents"
        for role in self.ROLES:
            self.write_agent(claude, role, f"You are the Teamwork {role.title()}.")
            self.write_agent(cursor, role, f"You are the Teamwork {role.title()}.")
            self.write(
                codex / f"teamwork-{role}.toml",
                f'name = "teamwork_{role}"\nmodel = "x"\n\nYou are the Teamwork {role.title()}.\n',
            )
        return claude, cursor, codex

    def test_agents_a_previous_release_installed_are_removed(self) -> None:
        claude, cursor, codex = self.previous_release_agents()

        self.install_ok("all")

        for role in self.ROLES:
            self.assertFalse((claude / f"{role}.md").exists(), role)
            self.assertFalse((cursor / f"{role}.md").exists(), role)
            self.assertFalse((codex / f"teamwork-{role}.toml").exists(), role)

    def test_an_agent_this_product_never_wrote_survives_a_name_collision(self) -> None:
        claude, _cursor, codex = self.previous_release_agents()
        mine = self.write(
            claude / "worker.md",
            "---\nname: worker\n---\nYou are my own worker. Nothing to do with Teamwork.\n",
        )
        near = self.write(codex / "deepseek-worker.toml.disabled", "name = \"deepseek\"\n")
        before = {mine: mine.read_text(encoding="utf-8"), near: near.read_text(encoding="utf-8")}

        done = self.install_ok("all")

        for path, text in before.items():
            self.assertTrue(path.is_file(), path)
            self.assertEqual(path.read_text(encoding="utf-8"), text, path)
        self.assertIn(str(mine), done.stderr)

    def test_install_creates_no_agent_directory_of_its_own(self) -> None:
        self.install_ok("all")

        for relative in (".claude/agents", ".cursor/agents", ".codex/agents"):
            self.assertNotIn(relative, snapshot(self.home))


class CrossHostParityTests(TeamworkCase):
    """The same Skill and the same shared policy body must land on every host.

    Each host has its own skill root and its own policy wrapper. What must not
    vary is the method and the standing rules: one host quietly shipping a
    different SKILL.md or a different policy body is a silent fork of the
    product, and nothing else in this suite would notice.
    """

    SKILL_ROOTS = {
        "claude": ".claude/skills",
        "codex": ".agents/skills",
        "cursor": ".cursor/skills",
    }

    def install_every_host(self) -> None:
        self.install_ok("codex")
        self.install_ok("claude")
        self.install_ok("cursor")

    def test_every_host_receives_the_same_skill_tree(self) -> None:
        self.install_every_host()

        trees = {
            host: snapshot(self.home / relative / "teamwork-collaborate")
            for host, relative in self.SKILL_ROOTS.items()
        }
        for tree in trees.values():
            self.assertIn("SKILL.md", tree, f"a host installed no SKILL.md: {trees}")
        reference = trees["claude"]
        for host, tree in trees.items():
            self.assertEqual(tree, reference, f"{host} skill tree differs from claude")

    def test_each_host_policy_block_carries_the_same_shared_body(self) -> None:
        self.install_every_host()
        source = (Path(__file__).resolve().parents[2] / "policy" / "teamwork-global.md").read_text(
            encoding="utf-8"
        )

        claude_text = (self.home / ".claude" / "CLAUDE.md").read_text(encoding="utf-8")
        _, claude_block, _ = split_managed(claude_text, CLAUDE_POLICY_START, CLAUDE_POLICY_END)
        codex_text = (self.home / ".codex" / "AGENTS.md").read_text(encoding="utf-8")
        _, codex_block, _ = split_managed(codex_text, CODEX_POLICY_START, CODEX_POLICY_END)
        cursor_stdout = self.install_ok("cursor-policy").stdout
        _, cursor_block, _ = split_managed(
            cursor_stdout, CURSOR_POLICY_START, CURSOR_POLICY_END
        )

        for host, block in (
            ("claude", claude_block),
            ("codex", codex_block),
            ("cursor", cursor_block),
        ):
            self.assertIn(source, block, f"{host} policy block does not carry the shared body")


class DoctorContractDriftTests(TeamworkCase):
    """The doctor runs against a real initialized project and reports drift.

    Every fixture here is built by the real `init-project` target and then read
    back through the real `scripts/doctor.py`; the assertions are on which
    drift the doctor names and on which file it names, never on how it words it.
    """

    def initialized_project(self) -> Path:
        project = self.temp_dir("project")
        self.install_ok("--project-root", str(project), "init-project")
        return project

    def write_documents(self, project: Path, *relatives: str) -> None:
        for relative in relatives:
            self.write(project / "docs" / "teamwork" / relative, "A useful result.\n")

    def write_index(self, project: Path, *relatives: str) -> None:
        lines = ["# Project Teamwork Documents\n", "\n## Document index\n\n"]
        lines += [f"- [{name}]({name}) - what it holds.\n" for name in relatives]
        self.write(project / "docs" / "teamwork" / "README.md", "".join(lines))

    def doctor(self, project: Path) -> list[dict]:
        done = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts" / "doctor.py"),
                "--project",
                str(project),
                "--json",
            ],
            capture_output=True,
            text=True,
            cwd=str(self.workdir),
            env={
                "HOME": str(self.home),
                "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
                "TMPDIR": os.environ.get("TMPDIR", "/tmp"),
                "LANG": "C",
                "PYTHONDONTWRITEBYTECODE": "1",
            },
        )
        self.assertIn(
            done.returncode,
            (0, 1),
            f"doctor could not run\nstdout:\n{done.stdout}\nstderr:\n{done.stderr}",
        )
        report = json.loads(done.stdout)
        self.assertEqual(len(report["projects"]), 1, done.stdout)
        return report["projects"][0]["findings"]

    def test_a_freshly_initialized_project_carries_no_drift(self) -> None:
        project = self.initialized_project()

        self.assertEqual(self.doctor(project), [])

    def test_an_index_entry_with_no_document_on_disk_is_reported_dead(self) -> None:
        project = self.initialized_project()
        self.write_documents(project, "records/kept.md")
        self.write_index(project, "records/kept.md", "records/gone.md")

        findings = self.doctor(project)

        self.assertEqual([item["check"] for item in findings], ["index-dead-entry"])
        self.assertEqual(findings[0]["severity"], "error")
        self.assertIn("records/gone.md", findings[0]["message"])
        self.assertNotIn("records/kept.md", findings[0]["message"])


    def test_an_index_that_matches_disk_reports_nothing(self) -> None:
        project = self.initialized_project()
        self.write_documents(project, "records/kept.md", "plans/listed.md")
        self.write_index(project, "records/kept.md", "docs/teamwork/plans/listed.md")

        self.assertEqual(self.doctor(project), [])

    def test_custom_directories_and_unlisted_records_are_allowed(self) -> None:
        project = self.initialized_project()
        self.write_documents(project, "notes/idea.md", "records/kept.md")
        self.write_index(project, "records/kept.md")

        findings = self.doctor(project)

        self.assertEqual(findings, [])

    def test_a_project_with_no_readme_index_is_reported_missing(self) -> None:
        # The reading side has one entry point. Without it nothing points a
        # session at what the project already decided, and the documents on
        # disk are unreachable in practice.
        project = self.initialized_project()
        self.write_documents(project, "records/kept.md")
        (project / "docs" / "teamwork" / "README.md").unlink()

        findings = self.doctor(project)

        self.assertEqual([item["check"] for item in findings], ["index-missing"])
        self.assertEqual(findings[0]["severity"], "error")

        # Reinitializing restores the entry without imposing index completeness.
        self.install_ok("--project-root", str(project), "init-project")
        self.assertEqual(self.doctor(project), [])

    def test_a_managed_block_from_an_older_release_is_reported_stale(self) -> None:
        project = self.initialized_project()
        agents = project / "AGENTS.md"
        before, inside, after = split_managed(
            agents.read_text(encoding="utf-8"), PROJECT_START, PROJECT_END
        )
        label = [line for line in inside.splitlines() if "Project label:" in line]
        self.assertEqual(len(label), 1, inside)
        # An older release's block: the same markers and label, a body this
        # version no longer writes.
        aged = f"\n## Teamwork Project Instructions\n\n{label[0]}\n- Some earlier wording.\n"
        agents.write_text(
            before + PROJECT_START + aged + PROJECT_END + after, encoding="utf-8"
        )

        findings = self.doctor(project)

        self.assertEqual([item["check"] for item in findings], ["block-stale"])
        self.assertEqual(findings[0]["severity"], "error")

        self.install_ok("--project-root", str(project), "init-project")
        self.assertEqual(self.doctor(project), [])

    def test_a_project_label_of_its_own_choosing_is_not_reported_stale(self) -> None:
        # The criterion is the block this version writes for the label the
        # block already carries -- not for the directory name, which would
        # report every project that named itself something else.
        project = self.initialized_project()
        agents = project / "AGENTS.md"
        text = agents.read_text(encoding="utf-8")
        _before, inside, _after = split_managed(text, PROJECT_START, PROJECT_END)
        label = [line for line in inside.splitlines() if "Project label:" in line][0]
        agents.write_text(
            text.replace(label, "- Project label: `a-name-of-its-own`."), encoding="utf-8"
        )

        self.assertEqual(self.doctor(project), [])

    def test_a_bridge_without_agents_import_is_reported_unreachable(self) -> None:
        project = self.initialized_project()
        self.write(project / "CLAUDE.md", "# Notes\n")

        findings = self.doctor(project)

        self.assertEqual([item["check"] for item in findings], ["host-unreachable"])
        self.assertEqual(findings[0]["severity"], "error")

        self.install_ok("--project-root", str(project), "init-project")
        self.assertEqual(self.doctor(project), [])



    def test_the_doctor_writes_nothing_while_reporting_drift(self) -> None:
        project = self.initialized_project()
        self.write_documents(project, "records/kept.md")
        self.write_index(project, "records/kept.md", "records/gone.md")
        before_home = snapshot(self.home)
        before_project = snapshot(project)

        self.assertNotEqual(self.doctor(project), [])

        self.assertEqual(before_home, snapshot(self.home))
        self.assertEqual(before_project, snapshot(project))

    def test_no_records_need_no_index(self) -> None:
        project = self.initialized_project()
        (project / "docs/teamwork/README.md").unlink()
        self.assertEqual(self.doctor(project), [])

    def test_document_content_and_root_placement_do_not_impose_a_schema(self) -> None:
        project = self.initialized_project()
        self.write(project / "docs/teamwork/2026-09-07-result.md",
                   "---\nstatus: finished\ncustom: kept\n---\nA result without History.\n")
        self.write_index(project, "2026-09-07-result.md")
        self.assertEqual(self.doctor(project), [])

    def test_index_checks_local_links_not_code_or_remote_urls(self) -> None:
        project = self.initialized_project()
        self.write_documents(project, "notes/a b.md")
        self.write(project / "docs/teamwork/README.md",
                   '[kept](<notes/a b.md#result>)\n'
                   '[web](https://example.com/missing.md)\n'
                   '[anchor](#section)\n`[example](missing.md)`\n'
                   '```md\n[example](missing.md)\n```\n'
                   '[broken](notes/absent.md#result)\n')
        found = self.doctor(project)
        self.assertEqual([x["check"] for x in found], ["index-dead-entry"])
        self.assertIn("notes/absent.md", found[0]["message"])

    def test_malformed_project_and_bridge_markers_are_reported(self) -> None:
        project = self.initialized_project()
        agents = project / "AGENTS.md"
        agents.write_text(agents.read_text().replace(PROJECT_END, ""))
        self.assertEqual([x["check"] for x in self.doctor(project)], ["block-malformed"])
        self.write(project / "CLAUDE.md", "@AGENTS.md\n<!-- TEAMWORK_CLAUDE_BRIDGE_END -->\n")
        self.assertEqual({x["check"] for x in self.doctor(project)}, {"block-malformed", "bridge-malformed"})

    def global_report(self, project: Path) -> list[dict]:
        done = self.install("doctor", "--project", str(project), "--json")
        self.assertIn(done.returncode, (0, 1), done.stderr)
        report = json.loads(done.stdout)
        self.assertEqual(set(report), {"version", "checkout", "closed_kinds", "document_fields", "global", "projects", "summary"})
        self.assertEqual(report["closed_kinds"], [])
        self.assertEqual(report["document_fields"], [])
        return report["global"]

    def test_uninstalled_hosts_do_not_need_policy_blocks(self) -> None:
        project = self.initialized_project()
        self.assertFalse(any(x["severity"] == "error" for x in self.global_report(project)))
        self.assertEqual(sum(x["check"] == "host-disabled" for x in self.global_report(project)), 2)

    def test_global_missing_malformed_and_stale_blocks_are_distinct(self) -> None:
        project = self.initialized_project()
        self.install_ok("codex")
        path = self.home / ".codex/AGENTS.md"
        original = path.read_text()
        cases = [
            ("# User rules only\n", "policy-missing"),
            (original.replace(CODEX_POLICY_END, ""), "policy-malformed"),
            (CODEX_POLICY_END + "\n" + CODEX_POLICY_START + "\n", "policy-malformed"),
            (original.replace("# Teamwork Global Policy", "# Earlier policy"), "policy-block"),
        ]
        for content, expected in cases:
            with self.subTest(expected=expected):
                path.write_text(content)
                errors = [x for x in self.global_report(project) if x["severity"] == "error"]
                self.assertEqual([x["check"] for x in errors], [expected])
        path.write_text(original)
        self.assertFalse(any(x["severity"] == "error" for x in self.global_report(project)))

    def test_same_version_skill_content_drift_is_detected(self) -> None:
        project = self.initialized_project()
        self.install_ok("codex")
        target = self.home / ".agents/skills/teamwork-collaborate/SKILL.md"
        target.write_text(target.read_text() + "\nChanged local instruction.\n")
        errors = [x for x in self.global_report(project) if x["severity"] == "error"]
        self.assertEqual([x["check"] for x in errors], ["skill-content-drift"])
        self.assertIn("SKILL.md", errors[0]["message"])

class CommandLineTests(TeamworkCase):
    def rejected(self, *args: str) -> None:
        done = self.install(*args)
        self.assertEqual(
            done.returncode,
            2,
            f"install.sh {' '.join(args)}\nstdout:\n{done.stdout}\nstderr:\n{done.stderr}",
        )
        self.assertEqual(
            snapshot(self.home), {}, f"install.sh {' '.join(args)} wrote to HOME anyway"
        )

    def test_invalid_invocations_exit_two_and_write_nothing(self) -> None:
        missing = self.workdir / "no-such-directory"
        a_file = self.workdir / "a-file"
        a_file.write_text("x\n", encoding="utf-8")

        self.rejected("bogus-target")
        self.rejected("doctor", "--verbose")
        self.rejected("codex", "claude")
        # Flags and targets this release removed. They must not silently become
        # "unknown argument that happens to still work".
        self.rejected("--profile", "cost-first", "codex")
        self.rejected("--performance-first", "codex")
        self.rejected("--cost-first", "codex")
        self.rejected("update")
        self.rejected("codex-agents")
        self.rejected("cursor-agents")
        self.rejected("claude-agents")
        self.rejected("--project-root", str(missing), "init-project")
        self.rejected("--project-root", str(a_file), "init-project")
        self.rejected("--project-root")
        self.rejected("--project-root", str(self.workdir), "codex")


if __name__ == "__main__":
    unittest.main()
