import json
import subprocess
import sys
import tempfile
import time
import unittest
import zipfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CGPT = REPO_ROOT / "cgpt.py"


def _conv(cid: str, title: str, create_time, user_text: str, assistant_text: str):
    return {
        "id": cid,
        "title": title,
        "create_time": create_time,
        "mapping": {
            "u1": {
                "message": {
                    "create_time": (time.time() + 1),
                    "author": {"role": "user"},
                    "content": {"content_type": "text", "parts": [user_text]},
                }
            },
            "a1": {
                "message": {
                    "create_time": (time.time() + 2),
                    "author": {"role": "assistant"},
                    "content": {"content_type": "text", "parts": [assistant_text]},
                }
            },
        },
    }


class EdgeCaseBase(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.home = Path(self.tempdir.name)
        self.zips = self.home / "zips"
        self.extracted = self.home / "extracted"
        self.dossiers = self.home / "dossiers"
        self.zips.mkdir(parents=True)
        self.extracted.mkdir(parents=True)
        self.dossiers.mkdir(parents=True)

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
        )

    def write_conversations(self, root: Path, conversations):
        root.mkdir(parents=True, exist_ok=True)
        (root / "conversations.json").write_text(
            json.dumps(conversations), encoding="utf-8"
        )


class TestZipSafety(EdgeCaseBase):
    def _write_zip(self, path: Path, member_name: str, payload: str = "x"):
        with zipfile.ZipFile(path, "w") as zf:
            zf.writestr(member_name, payload)

    def test_extract_rejects_parent_traversal_member(self):
        zpath = self.zips / "unsafe_parent.zip"
        self._write_zip(zpath, "../escape.txt", "bad")

        result = self.run_cgpt("extract", str(zpath))

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unsafe", result.stderr.lower())
        self.assertFalse((self.extracted / "escape.txt").exists())

    def test_extract_rejects_absolute_member(self):
        zpath = self.zips / "unsafe_abs.zip"
        self._write_zip(zpath, "/tmp/cgpt_abs_escape.txt", "bad")

        result = self.run_cgpt("extract", str(zpath))

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unsafe", result.stderr.lower())

    def test_extract_rejects_windows_drive_member(self):
        zpath = self.zips / "unsafe_drive.zip"
        self._write_zip(zpath, "C:\\temp\\escape.txt", "bad")

        result = self.run_cgpt("extract", str(zpath))

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unsafe", result.stderr.lower())

    def test_extract_unsafe_zip_writes_nothing_and_does_not_update_latest(self):
        safe_root = self.extracted / "safe_export"
        safe_root.mkdir(parents=True, exist_ok=True)
        (safe_root / "conversations.json").write_text("[]\n", encoding="utf-8")
        latest = self.extracted / "latest"
        latest.symlink_to(safe_root, target_is_directory=True)

        zpath = self.zips / "unsafe_write_guard.zip"
        self._write_zip(zpath, "../escaped.txt", "bad")

        result = self.run_cgpt("extract", str(zpath))

        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(latest.exists())
        self.assertEqual(latest.resolve(), safe_root.resolve())
        unsafe_out = self.extracted / "unsafe_write_guard"
        if unsafe_out.exists():
            self.assertEqual(list(unsafe_out.rglob("*")), [])
        self.assertFalse((self.extracted / "escaped.txt").exists())


class TestQuickAndSemantics(EdgeCaseBase):
    def setUp(self):
        super().setUp()
        self.root = self.extracted / "sample_export"
        now = time.time()
        conversations = [
            _conv(
                "conv-all-messages",
                "Neutral title",
                now - 3000,
                "alpha appears here",
                "beta appears here",
            ),
            _conv(
                "conv-one-message",
                "Neutral title",
                now - 2000,
                "alpha appears here",
                "no beta here",
            ),
            _conv(
                "conv-title-plus-message",
                "alpha only in title",
                now - 1000,
                "contains beta only in messages",
                "filler",
            ),
        ]
        self.write_conversations(self.root, conversations)

    def _selected_ids(self, slug: str):
        path = self.dossiers / f"selected_ids__{slug}.txt"
        self.assertTrue(path.exists(), f"Expected selected IDs file: {path}")
        return path.read_text(encoding="utf-8").strip().splitlines()

    def test_quick_where_messages_and_requires_all_terms(self):
        result = self.run_cgpt(
            "quick",
            "--where",
            "messages",
            "--and",
            "--all",
            "--root",
            str(self.root),
            "alpha",
            "beta",
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        selected = self._selected_ids("alpha_beta")
        self.assertEqual(selected, ["conv-all-messages"])

    def test_quick_where_all_and_uses_union_scope_for_all_terms(self):
        result = self.run_cgpt(
            "quick",
            "--where",
            "all",
            "--and",
            "--all",
            "--root",
            str(self.root),
            "alpha",
            "beta",
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        selected = self._selected_ids("alpha_beta")
        self.assertEqual(selected, ["conv-all-messages", "conv-title-plus-message"])

    def test_quick_where_messages_without_and_keeps_or_behavior(self):
        result = self.run_cgpt(
            "quick",
            "--where",
            "messages",
            "--all",
            "--root",
            str(self.root),
            "alpha",
            "beta",
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        selected = self._selected_ids("alpha_beta")
        self.assertEqual(selected, ["conv-all-messages", "conv-one-message", "conv-title-plus-message"])


class TestTimestampRobustness(EdgeCaseBase):
    def setUp(self):
        super().setUp()
        self.root = self.extracted / "timestamp_export"
        now = time.time()
        conversations = [
            _conv("conv-invalid-ts", "Alpha invalid ts", "not-a-number", "alpha text", "beta"),
            _conv("conv-recent", "Alpha recent", now - 3600, "alpha text", "beta"),
            _conv("conv-old", "Alpha old", now - (12 * 86400), "alpha text", "beta"),
        ]
        self.write_conversations(self.root, conversations)

    def test_recent_invalid_create_time_coerces_to_zero_and_warns(self):
        result = self.run_cgpt(
            "recent",
            "3",
            "--all",
            "--root",
            str(self.root),
            "--format",
            "txt",
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("warning", result.stderr.lower())
        self.assertIn("create_time", result.stderr.lower())

    def test_quick_recent_invalid_create_time_does_not_crash(self):
        result = self.run_cgpt(
            "quick",
            "--recent",
            "3",
            "--all",
            "--root",
            str(self.root),
            "alpha",
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertNotIn("traceback", result.stderr.lower())

    def test_quick_days_invalid_create_time_excluded_by_cutoff(self):
        result = self.run_cgpt(
            "quick",
            "--days",
            "2",
            "--all",
            "--root",
            str(self.root),
            "alpha",
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        selected_file = self.dossiers / "selected_ids__alpha.txt"
        selected = selected_file.read_text(encoding="utf-8").strip().splitlines()
        self.assertEqual(selected, ["conv-recent"])


class TestConfigErrorPolicy(EdgeCaseBase):
    def setUp(self):
        super().setUp()
        self.root = self.extracted / "config_export"
        now = time.time()
        conversations = [
            _conv("conv-a", "Alpha", now - 1000, "alpha text", "beta"),
        ]
        self.write_conversations(self.root, conversations)

    def test_quick_fails_on_missing_config_file(self):
        missing = self.home / "missing.json"
        result = self.run_cgpt(
            "quick",
            "--config",
            str(missing),
            "--all",
            "--root",
            str(self.root),
            "alpha",
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("config", result.stderr.lower())
        self.assertIn("not found", result.stderr.lower())

    def test_build_dossier_fails_on_invalid_config_json(self):
        bad = self.home / "bad_config.json"
        bad.write_text("{not-json", encoding="utf-8")
        result = self.run_cgpt(
            "build-dossier",
            "--config",
            str(bad),
            "--root",
            str(self.root),
            "--ids",
            "conv-a",
            "--mode",
            "full",
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("config", result.stderr.lower())
        self.assertIn("error", result.stderr.lower())

    def test_recent_fails_on_invalid_config_json(self):
        bad = self.home / "bad_config.json"
        bad.write_text("{not-json", encoding="utf-8")
        result = self.run_cgpt(
            "recent",
            "1",
            "--all",
            "--config",
            str(bad),
            "--root",
            str(self.root),
            "--split",
            "--format",
            "txt",
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("config", result.stderr.lower())
        self.assertIn("error", result.stderr.lower())


class TestInputEncodingPolicy(EdgeCaseBase):
    def setUp(self):
        super().setUp()
        self.root = self.extracted / "encoding_export"
        now = time.time()
        conversations = [
            _conv("conv-a", "Alpha", now - 1000, "alpha text", "beta"),
            _conv("conv-b", "Beta", now - 900, "beta text", "alpha"),
        ]
        self.write_conversations(self.root, conversations)

    def test_quick_ids_file_utf8_bom_is_supported(self):
        ids_file = self.home / "selection_bom.txt"
        ids_file.write_text("\ufeff1\n", encoding="utf-8")
        result = self.run_cgpt(
            "quick",
            "--ids-file",
            str(ids_file),
            "--root",
            str(self.root),
            "alpha",
            "beta",
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        selected = (self.dossiers / "selected_ids__alpha_beta.txt").read_text(
            encoding="utf-8"
        )
        self.assertIn("conv-a", selected)

    def test_build_dossier_ids_file_invalid_encoding_fails_cleanly(self):
        ids_file = self.home / "ids_bad_encoding.txt"
        ids_file.write_bytes(b"\xff\xfe\x00\x00")
        result = self.run_cgpt(
            "build-dossier",
            "--root",
            str(self.root),
            "--ids-file",
            str(ids_file),
            "--mode",
            "full",
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("utf-8", result.stderr.lower())

    def test_quick_patterns_file_invalid_encoding_fails_cleanly(self):
        patterns = self.home / "patterns_bad.txt"
        patterns.write_bytes(b"\xff\xfe\x00\x00")
        result = self.run_cgpt(
            "quick",
            "--all",
            "--root",
            str(self.root),
            "--patterns-file",
            str(patterns),
            "alpha",
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("utf-8", result.stderr.lower())

    def test_quick_used_links_file_invalid_encoding_fails_cleanly(self):
        used_links = self.home / "used_links_bad.txt"
        used_links.write_bytes(b"\xff\xfe\x00\x00")
        result = self.run_cgpt(
            "quick",
            "--all",
            "--split",
            "--root",
            str(self.root),
            "--used-links-file",
            str(used_links),
            "alpha",
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("utf-8", result.stderr.lower())


if __name__ == "__main__":
    unittest.main()
