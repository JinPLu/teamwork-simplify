from __future__ import annotations

import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]

sys.path.insert(0, str(ROOT / "scripts"))
from teamwork_tooling import topology as teamwork_topology  # noqa: E402
from teamwork_tooling.simple_yaml import load_simple_yaml  # noqa: E402

KINDS = frozenset({"discussions", "plans", "records", "experiments"})
CURRENT_ROLES = ("challenger", "worker", "writer")

# Retired Skills that must stay in scripts/install/common.sh's RETIRED_SKILLS
# so the installer keeps cleaning up copies left by a pre-simplify checkout.
RETIRED_SKILL_NAMES = (
    "teamwork-plan",
    "teamwork-review",
    "teamwork-research",
    "teamwork-debug",
    "teamwork-goal",
    "teamwork-init",
    "teamwork-update",
)

# Roles present in the pre-simplify checkout's templates/claude-agents (and
# the matching Cursor/Codex sets) that this checkout no longer installs.
RETIRED_ROLE_NAMES = ("researcher", "planner", "reviewer", "debugger")


class CoreFlowTests(unittest.TestCase):
    # ---- small text helpers, mirrored from the retired replay-era file's
    # non-replay helpers because they are still the right tool for reading
    # frontmatter/sections; they assert nothing about behavior by themselves.

    @staticmethod
    def _folded(text: str) -> str:
        return " ".join(text.split())

    def _skill_text(self, name: str) -> str:
        return (ROOT / "skills" / name / "SKILL.md").read_text(encoding="utf-8")

    def _section_after(self, text: str, marker: str) -> str:
        start = text.find(marker)
        self.assertGreaterEqual(start, 0, f"missing {marker!r} section")
        rest = text[start + len(marker) :]
        nxt = rest.find("\n## ")
        return rest if nxt < 0 else rest[:nxt]

    @staticmethod
    def _parse_bash_array(text: str, name: str) -> list[str]:
        """Read a `NAME=(...)` bash array literal, single- or multi-line."""
        match = re.search(rf"^{re.escape(name)}=\(", text, re.M)
        assert match is not None, f"{name} array not found"
        start = match.end()
        end = text.find(")", start)
        assert end >= 0, f"{name} array is not closed"
        body = text[start:end]
        return [item for item in body.split() if item]

    # ---- 1. document kind closed set ----

    def test_document_kind_set_is_closed(self) -> None:
        facts = load_simple_yaml(ROOT / "config/teamwork-facts.yaml")
        self.assertEqual(set(facts["kinds"]), KINDS)
        self.assertEqual(len(facts["kinds"]), 4, "facts.yaml must name exactly four kinds")

        architecture = (ROOT / "docs/architecture.md").read_text(encoding="utf-8")
        folded_architecture = self._folded(architecture)
        self.assertIn(
            "The set is closed: nothing invents a fifth kind, and nothing "
            "writes a checkpoint at the `docs/teamwork/` root.",
            folded_architecture,
        )
        self.assertIn("docs/teamwork/<kind>/<slug>.md", architecture)

        agents_text = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        block_start = agents_text.find("<!-- TEAMWORK_PROJECT_START -->")
        self.assertGreaterEqual(block_start, 0, "AGENTS.md has no Teamwork project block")
        block = agents_text[block_start:]
        listed = re.search(r"one of ((?:`[a-z]+`,?\s*(?:or\s*)?)+)", block)
        self.assertIsNotNone(listed, "AGENTS.md project block does not enumerate kinds")
        found_in_agents = set(re.findall(r"`([a-z]+)`", listed.group(1)))
        self.assertEqual(found_in_agents, KINDS)

    # ---- 2. templates complete ----

    def test_document_templates_are_complete(self) -> None:
        topology = json.loads((ROOT / "config/teamwork-topology.json").read_text(encoding="utf-8"))
        documents = {row["name"]: row["path"] for row in topology["document_templates"]}
        self.assertEqual(set(documents), {"discussion", "experiment", "plan", "record"})
        for name, path in documents.items():
            full = ROOT / path
            self.assertTrue(full.is_file(), path)
            template = full.read_text(encoding="utf-8")
            self.assertTrue(template.startswith("---\n"), path)
            end = template.find("\n---\n", 4)
            self.assertGreater(end, 0, path)
            frontmatter = template[4:end]
            for key in ("status", "superseded-by", "created", "updated"):
                self.assertIn(f"{key}:", frontmatter, f"{path} missing {key}")
            self.assertIn("## History", template, path)
            self.assertIn("Append only", template, path)

    # ---- 3. skill metadata minimal and unique ----

    def test_skill_metadata_is_minimal_and_unique(self) -> None:
        skill_files = sorted((ROOT / "skills").glob("*/SKILL.md"))
        self.assertEqual(len(skill_files), 1, skill_files)
        skill_path = skill_files[0]
        self.assertEqual(skill_path.parent.name, "teamwork-collaborate")

        text = skill_path.read_text(encoding="utf-8")
        self.assertTrue(text.startswith("---\n"))
        end = text.find("\n---\n", 4)
        self.assertGreater(end, 0)
        frontmatter_lines = [line for line in text[4:end].splitlines() if line.strip()]
        keys = [line.split(":", 1)[0] for line in frontmatter_lines]
        self.assertEqual(set(keys), {"name", "description"})

        meta = {}
        for line in frontmatter_lines:
            key, _, value = line.partition(":")
            meta[key.strip()] = value.strip()
        self.assertEqual(meta["name"], "teamwork-collaborate")
        self.assertTrue(meta["description"].startswith("Use when"), meta["description"])

    # ---- 4. persistence section covers the four kinds ----

    def test_skill_persistence_section_covers_four_kinds(self) -> None:
        skill = self._skill_text("teamwork-collaborate")
        section = self._section_after(skill, "## Persistence")
        folded = self._folded(section)
        for kind, template_name in (
            ("discussions", "discussion"),
            ("plans", "plan"),
            ("records", "record"),
            ("experiments", "experiment"),
        ):
            with self.subTest(kind=kind):
                self.assertIn(f"docs/teamwork/{kind}/<slug>.md", folded)
                self.assertIn(f"references/{template_name}.md", folded)
        self.assertEqual(section.count("Identity:"), 4)
        self.assertEqual(section.count("Checkpoint:"), 4)

    # ---- 5. rule ownership is single-sourced (the one required gate) ----

    def test_rule_ownership_is_single_sourced(self) -> None:
        policy = ROOT / "policy/teamwork-global.md"
        adapters = (ROOT / "CURSOR.md", ROOT / "CLAUDE.md", ROOT / "CODEX.md")
        skills = tuple(sorted((ROOT / "skills").glob("*/SKILL.md")))
        templates = tuple(sorted((ROOT / "templates").glob("*/*.md")))
        architecture = ROOT / "docs/architecture.md"
        others = adapters + skills + templates + (architecture,)

        owned = (
            "read the affected produce-transform-consume path",
            "One behavior, one path",
            "Report stage results in natural Chinese",
            "not a reason to add or keep it",
        )
        owner_text = self._folded(policy.read_text(encoding="utf-8"))
        for fragment in owned:
            self.assertIn(fragment.lower(), owner_text.lower(), fragment)
            for path in others:
                leaked = self._folded(path.read_text(encoding="utf-8"))
                self.assertNotIn(fragment.lower(), leaked.lower(), f"{fragment!r} leaked into {path}")

    # ---- 6. policy names the code prohibitions (word-list coverage only) ----

    def test_policy_names_code_prohibitions(self) -> None:
        """Checks that the code-prohibition word list is present in the
        policy text. This measures vocabulary coverage only; it does not
        measure, and must never be read as measuring, whether any of these
        words actually changes an agent's behavior."""
        policy = (ROOT / "policy/teamwork-global.md").read_text(encoding="utf-8")
        lowered = policy.lower()
        for word in (
            "sha-256",
            "checksum",
            "hash",
            "preemptive",
            "fallback",
            "_v2",
            "toggle",
            "pass-through",
        ):
            self.assertIn(word, lowered, word)
        self.assertIn(
            "is not a reason to add or keep it",
            self._folded(policy),
        )

    # ---- 7. retired inventory is complete ----

    def test_retired_inventory_is_complete(self) -> None:
        common_sh = (ROOT / "scripts/install/common.sh").read_text(encoding="utf-8")
        retired_skills = self._parse_bash_array(common_sh, "RETIRED_SKILLS")
        for name in RETIRED_SKILL_NAMES:
            self.assertIn(name, retired_skills, name)

        retired_claude = self._parse_bash_array(common_sh, "RETIRED_CLAUDE_AGENTS")
        retired_cursor = self._parse_bash_array(common_sh, "RETIRED_CURSOR_AGENTS")
        retired_codex = self._parse_bash_array(common_sh, "RETIRED_CODEX_AGENTS")
        for name in RETIRED_ROLE_NAMES:
            self.assertIn(name, retired_claude, name)
            self.assertIn(name, retired_cursor, name)
            self.assertIn(f"teamwork-{name}", retired_codex, name)

        topology = json.loads((ROOT / "config/teamwork-topology.json").read_text(encoding="utf-8"))
        current_roles = {row["name"] for row in topology["agents"]}
        self.assertEqual(current_roles, set(CURRENT_ROLES))
        for role in CURRENT_ROLES:
            self.assertNotIn(role, retired_claude, role)
            self.assertNotIn(role, retired_cursor, role)
            self.assertNotIn(f"teamwork-{role}", retired_codex, role)

    # ---- 8. topology and installer inventories agree ----

    def test_topology_and_installers_agree(self) -> None:
        topology = json.loads((ROOT / "config/teamwork-topology.json").read_text(encoding="utf-8"))
        for row in topology["public_skills"]:
            self.assertTrue((ROOT / row["path"]).is_file(), row["path"])

        template_paths = []
        for row in topology["agents"]:
            self.assertEqual(set(row["templates"]), {"codex", "cursor", "claude"})
            template_paths.extend(row["templates"].values())
        self.assertEqual(len(template_paths), 9, template_paths)
        for path in template_paths:
            self.assertTrue((ROOT / path).is_file(), path)

        for host in ("codex", "cursor", "claude"):
            roles = set(teamwork_topology.host_role_paths(ROOT)[host])
            self.assertEqual(roles, set(CURRENT_ROLES), host)

    # ---- 9. real install + marker readback, temp HOME only ----

    def test_host_policy_wrappers_and_init_readback_use_temp_home(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            home = Path(raw)
            (home / ".claude").mkdir()
            (home / ".codex").mkdir()
            fake_block = (
                "<!-- USER_GIT_WORKFLOW_START -->\n"
                "## My Own Git Rules\n\n"
                "Do not force push.\n"
                "<!-- USER_GIT_WORKFLOW_END -->\n"
            )
            (home / ".claude/CLAUDE.md").write_text(fake_block, encoding="utf-8")
            (home / ".codex/AGENTS.md").write_text(fake_block, encoding="utf-8")

            env = os.environ.copy()
            env["HOME"] = str(home)
            env["CODEX_HOME"] = str(home / ".codex")

            needles = {
                "cursor-policy": (
                    "CreatePlan and host Plan drafts are editable candidates",
                    "AskQuestion batches collect input",
                    "minimum shared bridge",
                    "CreatePlan is not Writer",
                ),
                "claude-policy": (
                    "Plan mode is a read-only permission boundary",
                    "AskUserQuestion batches collect input",
                    "acceptance of a reusable plan",
                    "apply the matching Persistence contract",
                    "`~/.claude/plans/` is a machine-local",
                    "not Teamwork persistence",
                ),
                "codex-policy": (
                    "candidates until the user approves them",
                    "native execution approval",
                    "`$name`",
                ),
            }
            for target, expected in needles.items():
                result = subprocess.run(
                    [str(ROOT / "install.sh"), target],
                    env=env,
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                folded = self._folded(result.stdout)
                for needle in expected:
                    self.assertIn(needle, folded, f"{target}: {needle}")

            script = (
                "set -euo pipefail\n"
                f"ROOT={str(ROOT)!r}\n"
                'source "$ROOT/scripts/install/common.sh"\n'
                'source "$ROOT/scripts/install/policy.sh"\n'
                "install_claude_global_policy\n"
                "install_codex_global_policy\n"
            )
            written = subprocess.run(
                ["bash", "-c", script],
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(written.returncode, 0, written.stderr)

            claude_md = (home / ".claude/CLAUDE.md").read_text(encoding="utf-8")
            codex_md = (home / ".codex/AGENTS.md").read_text(encoding="utf-8")

            for text in (claude_md, codex_md):
                self.assertIn("## My Own Git Rules", text)
                self.assertIn("Do not force push.", text)
                self.assertEqual(text.count("<!-- USER_GIT_WORKFLOW_START -->"), 1)
                self.assertEqual(text.count("<!-- USER_GIT_WORKFLOW_END -->"), 1)

            for text, start_marker, end_marker in (
                (claude_md, "<!-- TEAMWORK_CLAUDE_GLOBAL_START -->", "<!-- TEAMWORK_CLAUDE_GLOBAL_END -->"),
                (codex_md, "<!-- TEAMWORK_CODEX_GLOBAL_START -->", "<!-- TEAMWORK_CODEX_GLOBAL_END -->"),
            ):
                self.assertEqual(text.count(start_marker), 1)
                self.assertEqual(text.count(end_marker), 1)
                start = text.find(start_marker) + len(start_marker)
                end = text.find(end_marker)
                body = text[start:end].strip("\n")
                policy_source = (ROOT / "policy/teamwork-global.md").read_text(encoding="utf-8").rstrip("\n")
                # The managed block is the host header, the canonical policy
                # body verbatim, then a host tail note; the policy text must
                # appear unmodified inside it.
                self.assertIn(policy_source, body)

            project = home / "proj"
            project.mkdir()
            init = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/init-project-files.py"),
                    "--project-root",
                    str(project),
                    "initialize",
                ],
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(init.returncode, 0, init.stderr)
            agents = (project / "AGENTS.md").read_text(encoding="utf-8")
            self.assertIn(
                "User-accepted reusable results live under `docs/teamwork/<kind>/`",
                agents,
            )
            bridge = (project / "CLAUDE.md").read_text(encoding="utf-8")
            self.assertEqual(bridge.count("<!-- TEAMWORK_CLAUDE_BRIDGE_START -->"), 1)
            self.assertIn("@AGENTS.md", bridge)
            self.assertFalse((project / "docs/teamwork").exists())
            self.assertFalse((home / "docs/teamwork").exists())

    # ---- 10. retired copies are actually deleted on install ----

    def test_install_removes_retired_skill_and_agent_copies(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            home = Path(raw)
            env = os.environ.copy()
            env["HOME"] = str(home)
            env["CODEX_HOME"] = str(home / ".codex")

            first = subprocess.run(
                [str(ROOT / "install.sh"), "--copy", "claude"],
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(first.returncode, 0, first.stderr)

            skill_root = home / ".claude/skills"
            agent_root = home / ".claude/agents"

            retired_skill_dir = skill_root / "teamwork-plan"
            retired_skill_dir.mkdir()
            (retired_skill_dir / "SKILL.md").write_text(
                "---\nname: teamwork-plan\ndescription: Use when retired.\n---\n\n"
                "Teamwork retired skill body.\n",
                encoding="utf-8",
            )
            (agent_root / "researcher.md").write_text(
                "---\nname: researcher\ndescription: retired\ntools: Read\n"
                "model: opus\neffort: xhigh\n---\n\nYou are the Teamwork Researcher.\n"
                "Retired body.\n",
                encoding="utf-8",
            )
            self.assertTrue(retired_skill_dir.is_dir())
            self.assertTrue((agent_root / "researcher.md").is_file())

            second = subprocess.run(
                [str(ROOT / "install.sh"), "--copy", "claude"],
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(second.returncode, 0, second.stderr)

            self.assertFalse(retired_skill_dir.exists(), "retired Skill copy was not removed")
            self.assertFalse((agent_root / "researcher.md").exists(), "retired agent copy was not removed")
            self.assertTrue((skill_root / "teamwork-collaborate").is_dir())
            for role in CURRENT_ROLES:
                self.assertTrue((agent_root / f"{role}.md").is_file(), role)

    # ---- 11. project init is idempotent, stateless, and bridges AGENTS.md ----

    def test_project_init_is_idempotent_and_stateless(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            project = Path(raw)
            command = [
                sys.executable,
                str(ROOT / "scripts/init-project-files.py"),
                "--project-root",
                str(project),
                "initialize",
            ]
            subprocess.run(command, check=True)
            first_agents = (project / "AGENTS.md").read_text(encoding="utf-8")
            subprocess.run(command, check=True)
            second_agents = (project / "AGENTS.md").read_text(encoding="utf-8")

            self.assertEqual(first_agents, second_agents)
            self.assertEqual(second_agents.count("<!-- TEAMWORK_PROJECT_START -->"), 1)
            self.assertIn("no required project-local workflow or state", second_agents)
            self.assertIn(
                "User-accepted reusable results live under `docs/teamwork/<kind>/`",
                second_agents,
            )
            bridge = (project / "CLAUDE.md").read_text(encoding="utf-8")
            self.assertEqual(bridge.count("<!-- TEAMWORK_CLAUDE_BRIDGE_START -->"), 1)
            self.assertEqual(bridge.count("<!-- TEAMWORK_CLAUDE_BRIDGE_END -->"), 1)
            self.assertIn("@AGENTS.md", bridge)
            self.assertFalse((project / "docs/teamwork").exists())

    def test_project_init_bridges_agents_into_claude_md(self) -> None:
        script = str(ROOT / "scripts/init-project-files.py")

        def initialize(project: Path) -> None:
            subprocess.run(
                [sys.executable, script, "--project-root", str(project), "initialize"],
                check=True,
            )

        with tempfile.TemporaryDirectory() as raw:
            base = Path(raw)

            keeps = base / "keeps-user-content"
            keeps.mkdir()
            (keeps / "CLAUDE.md").write_text("# Mine\n\nUse pnpm.\n", encoding="utf-8")
            initialize(keeps)
            bridge = (keeps / "CLAUDE.md").read_text(encoding="utf-8")
            self.assertIn("# Mine", bridge)
            self.assertIn("Use pnpm.", bridge)
            self.assertEqual(bridge.count("@AGENTS.md"), 1)

            existing = base / "already-imports"
            existing.mkdir()
            (existing / "CLAUDE.md").write_text("@AGENTS.md\n", encoding="utf-8")
            initialize(existing)
            self.assertEqual(
                (existing / "CLAUDE.md").read_text(encoding="utf-8"), "@AGENTS.md\n"
            )

            linked = base / "symlinked"
            linked.mkdir()
            (linked / "AGENTS.md").write_text("# Shared\n", encoding="utf-8")
            (linked / "CLAUDE.md").symlink_to("AGENTS.md")
            initialize(linked)
            self.assertTrue((linked / "CLAUDE.md").is_symlink())
            subprocess.run(
                [sys.executable, script, "--project-root", str(linked), "validate"],
                check=True,
            )

    # ---- 12. source pointer schema and host merge ----

    def _load_pointer_module(self):
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "write_source_pointer",
            ROOT / "scripts/write-source-pointer.py",
        )
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_source_pointer_schema_and_host_merge(self) -> None:
        module = self._load_pointer_module()
        check = subprocess.run(
            [sys.executable, str(ROOT / "scripts/write-source-pointer.py"), "check"],
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(check.returncode, 0, check.stderr)

        with tempfile.TemporaryDirectory() as raw:
            home = Path(raw)
            env = os.environ.copy()
            env["HOME"] = raw
            env["CODEX_HOME"] = str(home / ".codex")

            first = subprocess.run(
                [str(ROOT / "install.sh"), "--copy", "codex"],
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(first.returncode, 0, first.stderr)
            pointer = home / ".teamwork/install.json"
            first_value = json.loads(pointer.read_text(encoding="utf-8"))
            module.validate_pointer_object(first_value)
            self.assertEqual(first_value["root"], str(ROOT))
            self.assertEqual(first_value["hosts"], ["codex"])
            self.assertTrue((home / ".agents/skills/teamwork-collaborate").is_dir())

            second = subprocess.run(
                [str(ROOT / "install.sh"), "--copy", "cursor"],
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(second.returncode, 0, second.stderr)
            merged = json.loads(pointer.read_text(encoding="utf-8"))
            module.validate_pointer_object(merged)
            self.assertEqual(merged["root"], str(ROOT))
            self.assertEqual(merged["hosts"], ["codex", "cursor"])

            status = subprocess.run(
                [sys.executable, str(ROOT / "scripts/write-source-pointer.py"), "status", "--home", raw],
                env=env,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(status.returncode, 0, status.stderr)
            self.assertEqual(status.stdout.strip(), "valid")

    # ---- 13. schema/index/migration/notification runtime remain absent ----

    def test_schema_index_and_migration_runtime_remain_absent(self) -> None:
        retired_paths = (
            "scripts/migrate-teamwork-documents.py",
            "scripts/teamwork_index_v4.py",
            "scripts/teamwork-documents-schema.json",
            "scripts/check-update.sh",
            "docs/teamwork/experiments/LEDGER.md",
        )
        for path in retired_paths:
            self.assertFalse((ROOT / path).exists(), path)

        # Scan the mechanism surfaces only: code, config, skills, templates,
        # policy, and the top-level adapter docs. docs/teamwork/ holds
        # accepted discussion/plan/record/experiment documents, which may
        # legitimately discuss a retired concept historically (for example
        # the record of the decision to drop the LEDGER); that is not a live
        # mechanism and is out of scope for this check.
        mechanism_roots = (
            ROOT / "scripts",
            ROOT / "config",
            ROOT / "skills",
            ROOT / "templates",
            ROOT / "policy",
            ROOT / "install.sh",
            ROOT / "docs/architecture.md",
            ROOT / "README.md",
            ROOT / "README.en.md",
            ROOT / "CODEX.md",
            ROOT / "CLAUDE.md",
            ROOT / "CURSOR.md",
            ROOT / "AGENTS.md",
        )
        all_text = ""
        for root in mechanism_roots:
            candidates = [root] if root.is_file() else root.rglob("*")
            for path in candidates:
                if "scripts/tests" in path.as_posix() or "__pycache__" in path.parts:
                    continue
                if path.is_file() and path.suffix in {".py", ".sh", ".json", ".md"}:
                    try:
                        all_text += path.read_text(encoding="utf-8")
                    except UnicodeDecodeError:
                        continue
        self.assertNotIn("LEDGER", all_text)
        self.assertNotIn("cursor_skills", all_text)
        self.assertNotIn("codex_routing", all_text.lower().replace("-", "_"))
        self.assertNotIn("check-update.sh", all_text)


if __name__ == "__main__":
    unittest.main()
