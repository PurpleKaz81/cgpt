import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CGPT = REPO_ROOT / "cgpt.py"


def _conv(
    cid: str,
    title: str,
    create_time: float,
    user_text: str,
    assistant_text: str,
):
    return {
        "id": cid,
        "title": title,
        "create_time": create_time,
        "mapping": {
            "u1": {
                "message": {
                    "create_time": create_time + 1,
                    "author": {"role": "user"},
                    "content": {"content_type": "text", "parts": [user_text]},
                }
            },
            "a1": {
                "message": {
                    "create_time": create_time + 2,
                    "author": {"role": "assistant"},
                    "content": {"content_type": "text", "parts": [assistant_text]},
                }
            },
        },
    }


class TestRedactionIncremental(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.home = Path(self.tempdir.name)
        self.zips = self.home / "zips"
        self.extracted = self.home / "extracted"
        self.dossiers = self.home / "dossiers"
        self.zips.mkdir(parents=True)
        self.extracted.mkdir(parents=True)
        self.dossiers.mkdir(parents=True)
        self.root = self.extracted / "sample_export"
        self.root.mkdir(parents=True)

    def tearDown(self):
        self.tempdir.cleanup()

    def run_cgpt(self, *args, input_text=None):
        cmd = [sys.executable, str(CGPT), "--home", str(self.home), *args]
        return subprocess.run(
            cmd,
            input=input_text,
            text=True,
            capture_output=True,
            cwd=REPO_ROOT,
            check=False,
            env=os.environ.copy(),
        )

    def write_conversations(self, conversations):
        (self.root / "conversations.json").write_text(
            json.dumps(conversations), encoding="utf-8"
        )

    def latest_dossier_txt(self) -> Path:
        files = sorted(self.dossiers.glob("dossier__*.txt"), key=lambda p: p.stat().st_mtime)
        self.assertTrue(files, "expected at least one dossier txt")
        return files[-1]

    def latest_report(self) -> Path:
        files = sorted(
            self.dossiers.glob("*__redaction_report.json"),
            key=lambda p: p.stat().st_mtime,
        )
        self.assertTrue(files, "expected redaction report")
        return files[-1]

    def state_path(self) -> Path:
        return self.dossiers / ".redaction" / "state.v1.json"

    def test_default_redaction_enabled_and_state_created(self):
        now = time.time()
        self.write_conversations(
            [
                _conv(
                    "conv-a",
                    "Alpha",
                    now,
                    "Contact me at jane@example.com or +1 415-555-1234.",
                    "Noted.",
                )
            ]
        )

        result = self.run_cgpt(
            "build-dossier",
            "--root",
            str(self.root),
            "--ids",
            "conv-a",
            "--mode",
            "full",
            "--format",
            "txt",
            "--no-split",
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)

        txt = self.latest_dossier_txt().read_text(encoding="utf-8")
        self.assertIn("[REDACTED_EMAIL_", txt)
        self.assertIn("[REDACTED_PHONE_", txt)
        self.assertNotIn("jane@example.com", txt)
        self.assertTrue(self.state_path().exists())
        report = json.loads(self.latest_report().read_text(encoding="utf-8"))
        self.assertIn("summary", report)
        self.assertGreaterEqual(report["summary"]["redacted"], 1)

    def test_no_redact_preserves_raw_text(self):
        now = time.time()
        self.write_conversations(
            [
                _conv(
                    "conv-a",
                    "Alpha",
                    now,
                    "Email jane@example.com should remain if no redact.",
                    "ack",
                )
            ]
        )
        result = self.run_cgpt(
            "build-dossier",
            "--root",
            str(self.root),
            "--ids",
            "conv-a",
            "--mode",
            "full",
            "--format",
            "txt",
            "--no-split",
            "--no-redact",
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        txt = self.latest_dossier_txt().read_text(encoding="utf-8")
        self.assertIn("jane@example.com", txt)
        self.assertFalse(self.state_path().exists())

    def test_ui_phrase_not_classified_as_person_name(self):
        now = time.time()
        self.write_conversations(
            [
                _conv(
                    "conv-a",
                    "Alpha",
                    now,
                    "Data Controls -> Export Data (or via the Privacy Portal).",
                    "ok",
                )
            ]
        )
        result = self.run_cgpt(
            "build-dossier",
            "--root",
            str(self.root),
            "--ids",
            "conv-a",
            "--mode",
            "full",
            "--format",
            "txt",
            "--no-split",
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        txt = self.latest_dossier_txt().read_text(encoding="utf-8")
        self.assertIn("Privacy Portal", txt)
        report = json.loads(self.latest_report().read_text(encoding="utf-8"))
        categories = {
            item.get("category")
            for state_name in ("resolved", "new_pending", "auto_high_conf", "kept")
            for item in report.get("states", {}).get(state_name, [])
        }
        self.assertNotIn("person_name", categories)

    def test_second_run_same_input_adds_no_new_pending(self):
        now = time.time()
        self.write_conversations(
            [
                _conv(
                    "conv-a",
                    "Alpha",
                    now,
                    "My sister Ana Maria called me.",
                    "Thanks.",
                )
            ]
        )
        first = self.run_cgpt(
            "build-dossier",
            "--root",
            str(self.root),
            "--ids",
            "conv-a",
            "--mode",
            "full",
            "--format",
            "txt",
            "--no-split",
        )
        self.assertEqual(first.returncode, 0, msg=first.stderr)
        first_state = json.loads(self.state_path().read_text(encoding="utf-8"))
        first_pending_len = len(first_state["pending"])
        self.assertGreaterEqual(first_pending_len, 1)

        second = self.run_cgpt(
            "build-dossier",
            "--root",
            str(self.root),
            "--ids",
            "conv-a",
            "--mode",
            "full",
            "--format",
            "txt",
            "--no-split",
        )
        self.assertEqual(second.returncode, 0, msg=second.stderr)
        second_state = json.loads(self.state_path().read_text(encoding="utf-8"))
        self.assertEqual(len(second_state["pending"]), first_pending_len)
        second_report = json.loads(self.latest_report().read_text(encoding="utf-8"))
        self.assertEqual(second_report["states"]["new_pending"], [])

    def test_second_run_with_new_text_adds_new_pending(self):
        now = time.time()
        self.write_conversations(
            [
                _conv(
                    "conv-a",
                    "Alpha",
                    now - 10,
                    "My sister Ana Maria called me.",
                    "ok",
                )
            ]
        )
        first = self.run_cgpt(
            "build-dossier",
            "--root",
            str(self.root),
            "--ids",
            "conv-a",
            "--mode",
            "full",
            "--format",
            "txt",
            "--no-split",
        )
        self.assertEqual(first.returncode, 0, msg=first.stderr)
        first_state = json.loads(self.state_path().read_text(encoding="utf-8"))
        first_pending_len = len(first_state["pending"])

        self.write_conversations(
            [
                _conv(
                    "conv-a",
                    "Alpha",
                    now - 10,
                    "My sister Ana Maria called me.",
                    "ok",
                ),
                _conv(
                    "conv-b",
                    "Beta",
                    now,
                    "My brother John Carter joined the project.",
                    "ack",
                ),
            ]
        )
        second = self.run_cgpt(
            "build-dossier",
            "--root",
            str(self.root),
            "--ids",
            "conv-a",
            "conv-b",
            "--mode",
            "full",
            "--format",
            "txt",
            "--no-split",
        )
        self.assertEqual(second.returncode, 0, msg=second.stderr)
        second_state = json.loads(self.state_path().read_text(encoding="utf-8"))
        self.assertGreater(len(second_state["pending"]), first_pending_len)
        report = json.loads(self.latest_report().read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(report["states"]["new_pending"]), 1)

    def test_redact_review_fails_non_interactive(self):
        now = time.time()
        self.write_conversations(
            [
                _conv(
                    "conv-a",
                    "Alpha",
                    now,
                    "My sister Ana Maria called me.",
                    "ok",
                )
            ]
        )
        result = self.run_cgpt(
            "build-dossier",
            "--root",
            str(self.root),
            "--ids",
            "conv-a",
            "--mode",
            "full",
            "--format",
            "txt",
            "--no-split",
            "--redact-review",
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("requires an interactive terminal", result.stderr.lower())

    def test_make_dossiers_reuses_same_placeholder_across_conversations(self):
        now = time.time()
        email = "shared@example.com"
        self.write_conversations(
            [
                _conv("conv-a", "Alpha", now - 1, f"contact {email}", "ok"),
                _conv("conv-b", "Beta", now, f"also contact {email}", "ok"),
            ]
        )
        result = self.run_cgpt(
            "make-dossiers",
            "--root",
            str(self.root),
            "--ids",
            "conv-a",
            "conv-b",
            "--format",
            "txt",
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)

        txt_files = sorted(self.dossiers.glob("conv-*__*.txt"))
        self.assertEqual(len(txt_files), 2)
        contents = [p.read_text(encoding="utf-8") for p in txt_files]
        for content in contents:
            self.assertNotIn(email, content)
            self.assertIn("[REDACTED_EMAIL_001]", content)


if __name__ == "__main__":
    unittest.main()
