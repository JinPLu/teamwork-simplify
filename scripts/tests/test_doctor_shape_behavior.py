"""Behavior tests for doctor's document-shape check.

Every case builds a real project tree under a throwaway HOME, runs the real
`scripts/doctor.py --json` against it, and reads the findings back. The
compliant fixture is generated from the contract doctor itself parses out of
`policy/teamwork-global.md`, so a contract edit moves the fixture with it
instead of stranding a hand-written copy of the field names here.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from harness import (  # noqa: E402
    DOCTOR,
    TeamworkCase,
    contract_document,
    load_doctor,
)


class DoctorShapeCase(TeamworkCase):
    def setUp(self) -> None:
        super().setUp()
        doctor = load_doctor()
        self.contract = doctor.document_shape_contract()
        self.kind = sorted(doctor.closed_kind_set())[0]

    # ---- fixture construction ----------------------------------------------

    def document(self, **overrides: object) -> str:
        return contract_document(self.contract, **overrides)  # type: ignore[arg-type]

    def project(self, documents: dict[str, str]) -> Path:
        root = self.temp_dir("project")
        for name, text in documents.items():
            self.write(root / "docs" / "teamwork" / self.kind / name, text)
        return root

    # ---- running the real doctor -------------------------------------------

    def shape_findings(self, project: Path) -> list[dict]:
        done = subprocess.run(
            [sys.executable, str(DOCTOR), "--project", str(project), "--json"],
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
        self.assertTrue(done.stdout, f"doctor produced no report\nstderr:\n{done.stderr}")
        report = json.loads(done.stdout)
        self.assertEqual(len(report["projects"]), 1, done.stdout)
        return [
            item
            for item in report["projects"][0]["findings"]
            if item["check"].startswith("shape-")
        ]

    def assert_reports(self, documents: dict[str, str], check: str, severity: str) -> None:
        findings = self.shape_findings(self.project(documents))
        matched = [item for item in findings if item["check"] == check]
        self.assertTrue(matched, f"expected {check}, got {[i['check'] for i in findings]}")
        self.assertEqual(
            {item["severity"] for item in matched},
            {severity},
            [item for item in matched if item["severity"] != severity],
        )

    # ---- cases --------------------------------------------------------------

    def test_document_built_to_the_contract_reports_nothing(self) -> None:
        findings = self.shape_findings(self.project({"fixture-subject.md": self.document()}))
        self.assertEqual(findings, [])

    def test_missing_frontmatter_field_is_an_error(self) -> None:
        dropped = self.contract["fields"][0]
        text = "\n".join(
            line
            for line in self.document().splitlines()
            if not line.startswith(f"{dropped}:")
        )
        self.assert_reports({"fixture-subject.md": text}, "shape-frontmatter", "error")

    def test_frontmatter_field_outside_the_contract_is_an_error(self) -> None:
        text = self.document().replace("---\n", "---\nunnamed-slot: fixture\n", 1)
        self.assert_reports({"fixture-subject.md": text}, "shape-frontmatter", "error")

    def test_absent_history_section_is_an_error(self) -> None:
        heading = "#" * self.contract["history_level"] + " " + self.contract["history_title"]
        text = self.document().replace(heading, heading + " — earlier same-day block")
        self.assert_reports({"fixture-subject.md": text}, "shape-history-section", "error")

    def test_section_after_history_is_an_error(self) -> None:
        text = self.document() + "\n## Files changed by this completion\n\ntrailing.\n"
        self.assert_reports({"fixture-subject.md": text}, "shape-history-section", "error")

    def test_bulleted_history_entries_are_a_warning(self) -> None:
        marker = "#" * self.contract["entry_level"] + " "
        text = self.document().replace(marker, "- ")
        self.assert_reports({"fixture-subject.md": text}, "shape-history-entry", "warn")

    def test_updated_behind_the_newest_entry_is_an_error(self) -> None:
        text = self.document(updated="2026-08-01", entry_dates=("2026-08-01", "2026-08-05"))
        self.assert_reports({"fixture-subject.md": text}, "shape-updated-stale", "error")

    def test_updated_ahead_of_the_newest_entry_is_a_warning(self) -> None:
        text = self.document(updated="2026-08-09", entry_dates=("2026-08-01", "2026-08-02"))
        self.assert_reports({"fixture-subject.md": text}, "shape-updated-ahead", "warn")

    def test_date_prefixed_file_name_is_an_error(self) -> None:
        self.assert_reports(
            {"2026-08-02-fixture-subject.md": self.document()},
            "shape-filename-date",
            "error",
        )

    def test_non_markdown_file_under_a_kind_is_a_warning(self) -> None:
        self.assert_reports(
            {"fixture-subject.md": self.document(), "inventory.json": "{}\n"},
            "shape-non-document",
            "warn",
        )

    def test_unverifiable_history_claim_is_a_warning(self) -> None:
        text = self.document() + "\nRelinked the display text only; 正文内容未改动。\n"
        self.assert_reports({"fixture-subject.md": text}, "shape-unverifiable-claim", "warn")
