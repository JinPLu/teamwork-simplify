from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]


class DocsMaintenanceTests(unittest.TestCase):
    def test_facts_yaml_matches_closed_kind_set(self) -> None:
        sys.path.insert(0, str(ROOT / "scripts"))
        from teamwork_tooling.simple_yaml import load_simple_yaml

        facts = load_simple_yaml(ROOT / "config/teamwork-facts.yaml")
        self.assertEqual(
            facts["kinds"],
            ["discussions", "plans", "records", "experiments"],
        )
        self.assertEqual(facts["checkpoint_path"], "docs/teamwork/<kind>/<slug>.md")
        self.assertEqual(facts["kind_root"], "docs/teamwork/<kind>/")
        for host in ("codex", "cursor", "claude"):
            self.assertEqual(facts["hosts"][host]["skills"], 1)
            self.assertEqual(facts["hosts"][host]["roles"], 3)
        self.assertEqual(set(facts["kind_meanings"]), set(facts["kinds"]))

    def test_generated_fact_blocks_are_fresh(self) -> None:
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts/render-teamwork-facts.py"), "--check"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)

    def test_index_script_builds_index_without_ledger(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            docs = Path(raw) / "docs" / "teamwork"
            discussions = docs / "discussions"
            experiments = docs / "experiments"
            discussions.mkdir(parents=True)
            experiments.mkdir(parents=True)
            (discussions / "alpha.md").write_text(
                "---\n"
                "status: active\n"
                "superseded-by:\n"
                "created: 2026-08-20\n"
                "updated: 2026-08-20\n"
                "---\n\n"
                "# Alpha\n\n"
                "## Current synthesis\n\n"
                "Keep the same slug.\n",
                encoding="utf-8",
            )
            (discussions / "2026-07-01-old-topic.md").write_text(
                "---\n"
                "status: archived\n"
                "superseded-by:\n"
                "created: 2026-07-01\n"
                "updated: 2026-07-01\n"
                "---\n\n"
                "# Old topic\n\n"
                "Historical note.\n",
                encoding="utf-8",
            )
            (experiments / "probe.md").write_text(
                "---\n"
                "status: active\n"
                "superseded-by:\n"
                "created: 2026-08-20\n"
                "updated: 2026-08-20\n"
                "---\n\n"
                "# Probe\n\n"
                "## Claim to verify\n\n"
                "Exploratory probe.\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/teamwork-index.py"),
                    "--docs-root",
                    str(docs),
                    "--repo-root",
                    str(ROOT),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            index = (docs / "INDEX.md").read_text(encoding="utf-8")
            self.assertIn("## discussions", index)
            self.assertIn("## experiments", index)
            self.assertIn("## Optional", index)
            self.assertIn("alpha.md", index)
            self.assertIn("2026-07-01-old-topic.md", index)
            self.assertIn("Derived from checkpoint files", index)
            self.assertFalse((experiments / "LEDGER.md").exists())
            self.assertNotIn("LEDGER", index)

            check = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/teamwork-index.py"),
                    "--check",
                    "--docs-root",
                    str(docs),
                    "--repo-root",
                    str(ROOT),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(check.returncode, 0, check.stderr)

    def test_append_history_is_append_only(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            path = Path(raw) / "note.md"
            path.write_text(
                "---\nstatus: active\nupdated: 2026-01-01\n---\n\n"
                "# Note\n\n"
                "## History\n\n"
                "### 2026-01-01 — first\n\n"
                "Keep me.\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/teamwork-index.py"),
                    "--append-history",
                    str(path),
                    "### 2026-08-20 — second\n\nNew entry.\n",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            text = path.read_text(encoding="utf-8")
            self.assertIn("Keep me.", text)
            self.assertIn("New entry.", text)
            self.assertLess(text.find("Keep me."), text.find("New entry."))
            self.assertRegex(text, r"updated: 20\d{2}-\d{2}-\d{2}")

    def test_backfill_adds_archived_frontmatter(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            docs = Path(raw) / "docs" / "teamwork"
            plans = docs / "plans"
            plans.mkdir(parents=True)
            target = plans / "2026-08-01-legacy.md"
            target.write_text("# Legacy\n\nBody.\n", encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/teamwork-index.py"),
                    "--backfill",
                    "--docs-root",
                    str(docs),
                    "--repo-root",
                    str(ROOT),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            text = target.read_text(encoding="utf-8")
            self.assertTrue(text.startswith("---\n"))
            self.assertIn("status: archived", text)
            self.assertIn("created: 2026-08-01", text)
            self.assertIn("# Legacy", text)
            self.assertEqual(target.name, "2026-08-01-legacy.md")

    def test_backfill_skips_slug_only_without_force(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            docs = Path(raw) / "docs" / "teamwork"
            plans = docs / "plans"
            plans.mkdir(parents=True)
            slug = plans / "new-identity.md"
            slug.write_text("# New identity\n\nBody.\n", encoding="utf-8")
            dated = plans / "2026-08-01-legacy.md"
            dated.write_text("# Legacy\n\nBody.\n", encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/teamwork-index.py"),
                    "--backfill",
                    "--docs-root",
                    str(docs),
                    "--repo-root",
                    str(ROOT),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("skipped slug-only files without status: 1", result.stdout)
            self.assertTrue(dated.read_text(encoding="utf-8").startswith("---\n"))
            self.assertIn("status: archived", dated.read_text(encoding="utf-8"))
            self.assertEqual(slug.read_text(encoding="utf-8"), "# New identity\n\nBody.\n")

            forced = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/teamwork-index.py"),
                    "--backfill",
                    "--force",
                    "--docs-root",
                    str(docs),
                    "--repo-root",
                    str(ROOT),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(forced.returncode, 0, forced.stderr)
            self.assertIn("status: archived", slug.read_text(encoding="utf-8"))

    def test_doctor_reports_only(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            docs = Path(raw) / "docs" / "teamwork"
            records = docs / "records"
            records.mkdir(parents=True)
            (records / "dup-a.md").write_text(
                "---\nstatus: active\nsuperseded-by: missing.md\n---\n\n# Dup\n",
                encoding="utf-8",
            )
            (records / "2026-01-01-dup-a.md").write_text(
                "---\nstatus: archived\n---\n\n# Also dup\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/teamwork-index.py"),
                    "--doctor",
                    "--docs-root",
                    str(docs),
                    "--repo-root",
                    str(ROOT),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            combined = result.stdout + result.stderr
            self.assertIn("duplicate slug", combined)
            self.assertIn("broken superseded-by", combined)
            self.assertIn("Report only", combined)

    def test_public_docs_name_source_pointer_and_omit_plugin_install(self) -> None:
        checked = {
            "README.md": (ROOT / "README.md").read_text(encoding="utf-8"),
            "README.en.md": (ROOT / "README.en.md").read_text(encoding="utf-8"),
            "CONTRIBUTING.md": (ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8"),
            "AGENTS.md": (ROOT / "AGENTS.md").read_text(encoding="utf-8"),
            "CODEX.md": (ROOT / "CODEX.md").read_text(encoding="utf-8"),
            "CLAUDE.md": (ROOT / "CLAUDE.md").read_text(encoding="utf-8"),
            "CURSOR.md": (ROOT / "CURSOR.md").read_text(encoding="utf-8"),
            "docs/architecture.md": (ROOT / "docs/architecture.md").read_text(encoding="utf-8"),
        }
        for name, text in checked.items():
            self.assertNotIn("plugin", text.lower(), name)

        architecture = checked["docs/architecture.md"]
        codex = checked["CODEX.md"]
        self.assertIn("~/.teamwork/install.json", architecture)
        self.assertIn("~/.teamwork/install.json", codex)
        self.assertIn("./install.sh codex", checked["README.md"])
        self.assertIn("./install.sh codex", checked["README.en.md"])

        check = subprocess.run(
            [sys.executable, str(ROOT / "scripts/write-source-pointer.py"), "check"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(check.returncode, 0, check.stderr)


if __name__ == "__main__":
    unittest.main()
