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
    POINTER_RELATIVE,
    ROOT,
    TeamworkCase,
    contract_document,
    digest,
    load_doctor,
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
            "grill-me": digest(skills / "grill-me" / "SKILL.md"),
            "notes": digest(notes),
            "teamwork": digest(skills / "teamwork" / "SKILL.md"),
            "checklist": digest(checklist),
            "reviewer": digest(reviewer),
        }

        self.install_ok("claude")
        self.install_ok("claude")

        self.assertTrue((skills / "grill-me" / "SKILL.md").is_file())
        self.assertTrue((skills / "teamwork" / "SKILL.md").is_file())
        self.assertEqual(
            before,
            {
                "grill-me": digest(skills / "grill-me" / "SKILL.md"),
                "notes": digest(notes),
                "teamwork": digest(skills / "teamwork" / "SKILL.md"),
                "checklist": digest(checklist),
                "reviewer": digest(reviewer),
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
        second = snapshot(self.home, skip=(POINTER_RELATIVE,))
        self.install_ok("all")
        third = snapshot(self.home, skip=(POINTER_RELATIVE,))
        self.install_ok("all")
        fourth = snapshot(self.home, skip=(POINTER_RELATIVE,))

        self.assertEqual(second, third)
        self.assertEqual(third, fourth)
        self.assertTrue((self.home / POINTER_RELATIVE).is_file())


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


class UpdateTests(TeamworkCase):
    def stamp(self, host_root: str) -> str:
        return (self.home / host_root / ".teamwork-version").read_text(encoding="utf-8").strip()

    def test_update_refreshes_every_recorded_host_from_the_recorded_checkout(self) -> None:
        recorded = self.checkout_copy("recorded", "9.9.9-recorded")
        other = self.checkout_copy("other", "0.0.1-other")

        self.install_ok("claude", checkout=recorded)
        self.install_ok("codex", checkout=recorded)

        pointer = self.home / POINTER_RELATIVE
        self.assertEqual(
            sorted(json.loads(pointer.read_text(encoding="utf-8"))["hosts"]),
            ["claude", "codex"],
        )

        # Overwrite both installed roots so a no-op update cannot pass.
        for root in (".claude/skills", ".agents/skills"):
            (self.home / root / ".teamwork-version").write_text("stale\n", encoding="utf-8")

        done = self.install_ok("update", checkout=other)

        self.assertEqual(self.stamp(".claude/skills"), "9.9.9-recorded", done.stdout)
        self.assertEqual(self.stamp(".agents/skills"), "9.9.9-recorded", done.stdout)
        self.assertEqual(
            json.loads(pointer.read_text(encoding="utf-8"))["root"], str(recorded)
        )

    def test_update_fails_without_touching_anything_when_the_pointer_is_unusable(self) -> None:
        recorded = self.checkout_copy("recorded", "9.9.9-recorded")
        other = self.checkout_copy("other", "0.0.1-other")
        self.install_ok("claude", checkout=recorded)
        pointer = self.home / POINTER_RELATIVE
        healthy = pointer.read_text(encoding="utf-8")

        broken = {
            "not-json": "{ this is not json",
            "missing-root": json.dumps(
                {
                    "root": str(self.workdir / "gone"),
                    "version": "1.0.0",
                    "hosts": ["claude"],
                    "installed_at": "2026-08-29T00:00:00Z",
                }
            ),
            "not-a-checkout": json.dumps(
                {
                    "root": str(self.workdir),
                    "version": "1.0.0",
                    "hosts": ["claude"],
                    "installed_at": "2026-08-29T00:00:00Z",
                }
            ),
            "no-hosts": json.dumps(
                {
                    "root": str(recorded),
                    "version": "1.0.0",
                    "hosts": [],
                    "installed_at": "2026-08-29T00:00:00Z",
                }
            ),
        }

        for label, content in broken.items():
            with self.subTest(pointer=label):
                pointer.write_text(content, encoding="utf-8")
                before = snapshot(self.home)
                done = self.install("update", checkout=other)
                self.assertNotEqual(done.returncode, 0, done.stdout)
                self.assertEqual(before, snapshot(self.home))

        pointer.write_text(healthy, encoding="utf-8")
        self.install_ok("update", checkout=other)

    def test_update_fails_when_no_pointer_was_ever_written(self) -> None:
        done = self.install("update")
        self.assertNotEqual(done.returncode, 0, done.stdout)
        self.assertEqual(snapshot(self.home), {})


class CrossHostParityTests(TeamworkCase):
    """The same Skill and the same role contracts must land on every host.

    Each host has its own skill root, its own agent format, and its own policy
    wrapper. What must not vary is the method itself: one host quietly shipping
    a different SKILL.md or a differently-worded role contract is a silent
    fork of the product, and nothing else in this suite would notice.
    """

    SKILL_ROOTS = {
        "claude": ".claude/skills",
        "codex": ".agents/skills",
        "cursor": ".cursor/skills",
    }
    MARKDOWN_AGENT_ROOTS = {"claude": ".claude/agents", "cursor": ".cursor/agents"}
    ROLES = ("challenger", "worker", "writer")

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

    def test_markdown_hosts_share_one_body_per_role(self) -> None:
        self.install_every_host()

        for role in self.ROLES:
            bodies = {}
            for host, relative in self.MARKDOWN_AGENT_ROOTS.items():
                path = self.home / relative / f"{role}.md"
                self.assertTrue(path.is_file(), f"{host} installed no {role}")
                _, _, body = path.read_text(encoding="utf-8").split("---\n", 2)
                bodies[host] = body
            self.assertEqual(
                bodies["cursor"],
                bodies["claude"],
                f"{role} carries a different contract on cursor than on claude",
            )

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
        """Contract-shaped documents, so only index drift can report here."""
        contract = load_doctor().document_shape_contract()
        for relative in relatives:
            self.write(
                project / "docs" / "teamwork" / relative,
                contract_document(contract, subject=relative),
            )

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

    def test_a_document_the_index_never_registered_is_reported(self) -> None:
        project = self.initialized_project()
        self.write_documents(project, "records/kept.md", "plans/unlisted.md")
        self.write_index(project, "records/kept.md")

        findings = self.doctor(project)

        self.assertEqual([item["check"] for item in findings], ["index-unregistered"])
        self.assertIn("plans/unlisted.md", findings[0]["message"])
        self.assertNotIn("records/kept.md", findings[0]["message"])
        # Severity is behavior, not labelling: the session-start hook prints
        # errors only, so a pre-contract document staying a warning is what
        # keeps an unmigrated project from shouting on every start.
        self.assertEqual(findings[0]["severity"], "warn")

    def test_an_index_that_matches_disk_reports_nothing(self) -> None:
        project = self.initialized_project()
        self.write_documents(project, "records/kept.md", "plans/listed.md")
        self.write_index(project, "records/kept.md", "docs/teamwork/plans/listed.md")

        self.assertEqual(self.doctor(project), [])

    def test_a_directory_outside_the_closed_kind_set_is_reported(self) -> None:
        project = self.initialized_project()
        self.write_documents(project, "notes/idea.md", "records/kept.md")
        self.write_index(project, "records/kept.md")

        findings = self.doctor(project)

        self.assertEqual([item["check"] for item in findings], ["kind-outside-contract"])
        self.assertIn("notes", findings[0]["message"])

    def test_a_project_with_no_readme_index_reports_no_drift(self) -> None:
        # docs/teamwork/README.md is init-project's own navigation convenience,
        # not a contract requirement (see policy/teamwork-global.md): a project
        # that never had one, or dropped it, is not in drift for that alone.
        project = self.initialized_project()
        self.write_documents(project, "records/kept.md")
        (project / "docs" / "teamwork" / "README.md").unlink()

        self.assertEqual(self.doctor(project), [])

    def test_doctor_never_exits_2_from_contract_parsing_on_a_real_project(self) -> None:
        # scripts/doctor.py reads policy/teamwork-global.md's kind table
        # through this checkout's real path, not a fixture copy. A format
        # change to that table (bullets -> table, as actually happened once)
        # must degrade to a wrong finding, never crash the whole run with
        # exit 2 -- that blind spot let validate.sh stay green while
        # doctor.py was completely unable to run.
        project = self.initialized_project()
        done = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "doctor.py"), "--project", str(project)],
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
            f"doctor exited {done.returncode} (contract parsing likely failed)\n"
            f"stdout:\n{done.stdout}\nstderr:\n{done.stderr}",
        )

    def test_the_doctor_writes_nothing_while_reporting_drift(self) -> None:
        project = self.initialized_project()
        self.write_documents(project, "records/kept.md")
        self.write_index(project, "records/kept.md", "records/gone.md")
        before_home = snapshot(self.home)
        before_project = snapshot(project)

        self.assertNotEqual(self.doctor(project), [])

        self.assertEqual(before_home, snapshot(self.home))
        self.assertEqual(before_project, snapshot(project))


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
        self.rejected("codex", "claude")
        self.rejected("--profile", "bogus", "codex")
        self.rejected("--profile")
        self.rejected("--profile", "cost-first", "claude")
        self.rejected("--project-root", str(missing), "init-project")
        self.rejected("--project-root", str(a_file), "init-project")
        self.rejected("--project-root")
        self.rejected("--project-root", str(self.workdir), "codex")


if __name__ == "__main__":
    unittest.main()
