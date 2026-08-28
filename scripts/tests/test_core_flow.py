from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]

KINDS = frozenset({"discussions", "plans", "records", "experiments"})
# Plural checkpoint directory -> singular reference template stem.
KIND_TEMPLATES = {
    "discussions": "discussion",
    "plans": "plan",
    "records": "record",
    "experiments": "experiment",
}
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

CODE_SPAN_RE = re.compile(r"`[^`]*`")


class CoreFlowTests(unittest.TestCase):
    # ---- small text helpers; they assert nothing by themselves ----

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

    def _load_script_module(self, name: str, relative: str):
        spec = importlib.util.spec_from_file_location(name, ROOT / relative)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def _managed_block(self, label: str = "sample") -> str:
        """The project AGENTS.md Teamwork block: the persistence contract's
        single owner, read straight from the generator that writes it."""
        module = self._load_script_module(
            "init_project_files", "scripts/init-project-files.py"
        )
        return module.managed_block(label)

    def _reference_templates(self) -> dict[str, Path]:
        root = ROOT / "skills/teamwork-collaborate/references"
        return {path.stem: path for path in sorted(root.glob("*.md"))}

    # ---- 1. document kind closed set, owned by the project block ----

    def test_document_kind_set_is_closed(self) -> None:
        block = self._managed_block()

        # Every backticked `<name>/` span in the block is a checkpoint kind;
        # the set must be exactly the four, with no fifth invented anywhere.
        named = re.findall(r"`([a-z]+)/`", block)
        self.assertEqual(set(named), KINDS, named)
        self.assertEqual(len(named), 4, named)

        self.assertIn("docs/teamwork/<kind>/<slug>.md", block)
        self.assertIn("The kind set is closed.", block)

        # Cross-check: one reference template per kind, and nothing else.
        self.assertEqual(
            set(self._reference_templates()), set(KIND_TEMPLATES.values())
        )

    # ---- 2. reference templates complete ----

    def test_document_templates_are_complete(self) -> None:
        templates = self._reference_templates()
        self.assertEqual(len(templates), 4, sorted(templates))
        self.assertEqual(set(templates), set(KIND_TEMPLATES.values()))

        for kind, stem in KIND_TEMPLATES.items():
            with self.subTest(kind=kind):
                path = templates[stem]
                template = path.read_text(encoding="utf-8")
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

    # ---- 4. the persistence contract lives in the project block ----

    def test_persistence_contract_is_owned_by_the_project_block(self) -> None:
        block = self._managed_block()
        folded_block = self._folded(block)

        # (a) The block carries the whole contract: when a checkpoint fires,
        # which kind it is, how identity is judged, and the document shape.
        self.assertIn("docs/teamwork/<kind>/<slug>.md", folded_block)
        self.assertIn("same response cycle", folded_block)
        self.assertIn("An ordinary next action is not a checkpoint.", folded_block)

        # Each kind carries its own identity criterion in its own clause.
        clauses = re.split(r"(?=Write `[a-z]+/`)", block)
        seen = set()
        for clause in clauses:
            match = re.match(r"Write `([a-z]+)/`", clause)
            if match is None:
                continue
            kind = match.group(1)
            seen.add(kind)
            with self.subTest(kind=kind):
                self.assertIn("its identity is", clause, kind)
        self.assertEqual(seen, KINDS)

        # Path reuse, current synthesis on top, append-only History below,
        # and the user's own wording kept apart from the model's reading.
        self.assertIn("The same identity reuses the same path.", folded_block)
        self.assertIn("current synthesis at the top", folded_block)
        self.assertIn("append-only dated History at the bottom", folded_block)
        self.assertIn("original wording", folded_block)
        self.assertIn("working understanding", folded_block)

        # Cross-check the separation against the template that carries it.
        discussion = self._reference_templates()["discussion"].read_text(encoding="utf-8")
        self.assertIn("## User quotes", discussion)
        self.assertIn("## Working understanding", discussion)

        # (b) The Skill no longer defines any of it. Its Persistence section
        # is a pointer: the project block plus the four template paths, with
        # no kind directory, no path shape, and no identity rule of its own.
        skill = self._skill_text("teamwork-collaborate")
        self.assertNotIn("docs/teamwork/", skill)
        for kind in KINDS:
            self.assertNotIn(f"`{kind}/`", skill, kind)
        section = self._folded(self._section_after(skill, "## Persistence"))
        self.assertIn("`AGENTS.md`", section)
        for stem in KIND_TEMPLATES.values():
            self.assertIn(f"`references/{stem}.md`", section, stem)

    # ---- 5. policy rules are not restated anywhere else ----

    @staticmethod
    def _prose_words(text: str) -> list[str]:
        """Fold to a lowercase, punctuation-free word sequence. Inline code
        spans are dropped first: `AGENTS.md` or `docs/teamwork/<kind>/` are
        identifiers every file must be able to name, and naming the same
        artifact is not restating a rule about it."""
        return re.sub(r"[^a-z0-9]+", " ", CODE_SPAN_RE.sub(" ", text).lower()).split()

    def test_policy_rules_are_not_restated_elsewhere(self) -> None:
        # 8 words is the shortest window that separates "restates a policy
        # rule" from "shares a few words". With code spans dropped, the
        # longest legitimate prose overlap in this tree is 6 words ("after
        # the user accepts a reusable" / "the project s own teamwork block"),
        # both of which are shared subjects, not rules; the shortest actual
        # rule sentence in the policy is far longer than 8 words, so a real
        # restatement still trips this.
        window = 8

        policy_words = self._prose_words(
            (ROOT / "policy/teamwork-global.md").read_text(encoding="utf-8")
        )
        self.assertGreater(len(policy_words), window)
        grams = {
            tuple(policy_words[i : i + window])
            for i in range(len(policy_words) - window + 1)
        }

        others = (
            tuple(sorted((ROOT / "skills").glob("*/SKILL.md")))
            + tuple(sorted(p for p in (ROOT / "templates").glob("*/*") if p.is_file()))
            + (ROOT / "CODEX.md", ROOT / "CURSOR.md", ROOT / "CLAUDE.md")
        )
        self.assertEqual(
            len([p for p in others if p.parent.name.endswith("-agents")]), 9, others
        )

        for path in others:
            words = self._prose_words(path.read_text(encoding="utf-8"))
            echoes = sorted(
                {
                    " ".join(words[i : i + window])
                    for i in range(len(words) - window + 1)
                    if tuple(words[i : i + window]) in grams
                }
            )
            self.assertEqual(
                echoes, [], f"{path.relative_to(ROOT)} restates policy prose: {echoes}"
            )

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

        for role in CURRENT_ROLES:
            self.assertNotIn(role, retired_claude, role)
            self.assertNotIn(role, retired_cursor, role)
            self.assertNotIn(f"teamwork-{role}", retired_codex, role)

    # ---- 8. installer inventories match what the checkout actually ships ----

    def test_installer_inventories_match_the_checkout(self) -> None:
        common_sh = (ROOT / "scripts/install/common.sh").read_text(encoding="utf-8")

        shipped_skills = {path.parent.name for path in (ROOT / "skills").glob("*/SKILL.md")}
        self.assertEqual(shipped_skills, {"teamwork-collaborate"})
        for name in ("SKILLS", "CURSOR_SKILLS", "CLAUDE_SKILLS", "CODEX_SKILLS"):
            with self.subTest(array=name):
                self.assertEqual(set(self._parse_bash_array(common_sh, name)), shipped_skills)

        role_templates = {
            "claude": sorted((ROOT / "templates/claude-agents").glob("*.md")),
            "cursor": sorted((ROOT / "templates/cursor-agents").glob("*.md")),
            "codex": sorted((ROOT / "templates/codex-agents").glob("*.toml")),
        }
        self.assertEqual(sum(len(paths) for paths in role_templates.values()), 9, role_templates)
        for host, paths in role_templates.items():
            with self.subTest(host=host):
                self.assertEqual(len(paths), 3, paths)
                for path in paths:
                    self.assertTrue(path.is_file(), path)

        self.assertEqual(
            {path.stem for path in role_templates["claude"]}, set(CURRENT_ROLES)
        )
        self.assertEqual(
            {path.stem for path in role_templates["cursor"]}, set(CURRENT_ROLES)
        )
        self.assertEqual(
            {path.stem for path in role_templates["codex"]},
            {f"teamwork-{role}" for role in CURRENT_ROLES},
        )

        self.assertEqual(
            set(self._parse_bash_array(common_sh, "CLAUDE_AGENTS")),
            {path.stem for path in role_templates["claude"]},
        )
        self.assertEqual(
            set(self._parse_bash_array(common_sh, "CURSOR_AGENTS")),
            {path.stem for path in role_templates["cursor"]},
        )
        self.assertEqual(
            set(self._parse_bash_array(common_sh, "CODEX_AGENTS")),
            {path.stem for path in role_templates["codex"]},
        )

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
                    "the project's own AGENTS.md Teamwork block specifies",
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
            self.assertIn(self._managed_block("proj"), agents)
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
            self.assertIn(self._managed_block(project.name), second_agents)
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

    def test_source_pointer_schema_and_host_merge(self) -> None:
        module = self._load_script_module(
            "write_source_pointer", "scripts/write-source-pointer.py"
        )
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

    # ---- 13. public docs name the source pointer and omit plugin install ----

    def test_public_docs_name_source_pointer_and_omit_plugin_install(self) -> None:
        checked = {
            name: (ROOT / name).read_text(encoding="utf-8")
            for name in ("README.md", "CODEX.md", "CURSOR.md", "CLAUDE.md")
        }
        for name, text in checked.items():
            self.assertNotIn("plugin", text.lower(), name)

        self.assertIn("~/.teamwork/install.json", checked["README.md"])
        self.assertIn("~/.teamwork/install.json", checked["CODEX.md"])
        self.assertIn("./install.sh codex", checked["README.md"])

        check = subprocess.run(
            [sys.executable, str(ROOT / "scripts/write-source-pointer.py"), "check"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(check.returncode, 0, check.stderr)

    # ---- 14. schema/index/migration/notification runtime remain absent ----

    def test_schema_index_and_migration_runtime_remain_absent(self) -> None:
        retired_paths = (
            "scripts/migrate-teamwork-documents.py",
            "scripts/teamwork_index_v4.py",
            "scripts/teamwork-documents-schema.json",
            "scripts/check-update.sh",
            "docs/teamwork/experiments/LEDGER.md",
            # Removed with the derived-inventory scaffolding; must not return.
            "scripts/teamwork-index.py",
            "scripts/render-teamwork-facts.py",
            "scripts/teamwork_tooling",
            "config/teamwork-topology.json",
            "config/teamwork-facts.yaml",
        )
        for path in retired_paths:
            self.assertFalse((ROOT / path).exists(), path)

        # Scan the mechanism surfaces only: code, skills, templates, policy,
        # and the top-level public docs. docs/teamwork/ holds accepted
        # discussion/plan/record/experiment documents, which may legitimately
        # discuss a retired concept historically (for example the record of
        # the decision to drop the LEDGER, or the plan that removed the
        # derived-inventory scripts); that is not a live mechanism and is out
        # of scope for this check.
        mechanism_roots = (
            ROOT / "scripts",
            ROOT / "skills",
            ROOT / "templates",
            ROOT / "policy",
            ROOT / "install.sh",
            ROOT / "README.md",
            ROOT / "CODEX.md",
            ROOT / "CLAUDE.md",
            ROOT / "CURSOR.md",
            ROOT / "CONTRIBUTING.md",
            ROOT / "AGENTS.md",
        )
        all_text = ""
        for root in mechanism_roots:
            candidates = [root] if root.is_file() else root.rglob("*")
            for path in candidates:
                if "scripts/tests" in path.as_posix() or "__pycache__" in path.parts:
                    continue
                if path.is_file() and path.suffix in {".py", ".sh", ".json", ".md", ".yaml", ".toml"}:
                    try:
                        all_text += path.read_text(encoding="utf-8")
                    except UnicodeDecodeError:
                        continue
        self.assertNotIn("LEDGER", all_text)
        self.assertNotIn("cursor_skills", all_text)
        self.assertNotIn("codex_routing", all_text.lower().replace("-", "_"))
        self.assertNotIn("check-update.sh", all_text)
        for gone in (
            "teamwork-index",
            "render-teamwork-facts",
            "teamwork-topology",
            "teamwork-facts",
            "teamwork_tooling",
        ):
            self.assertNotIn(gone, all_text, gone)


if __name__ == "__main__":
    unittest.main()
