import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
CGPT = REPO_ROOT / "cgpt.py"
HAS_DOCX = importlib.util.find_spec("docx") is not None


def _conv(cid: str, title: str, create_time: float, user_text: str, assistant_text: str):
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
                    "content": {
                        "content_type": "text",
                        "parts": [assistant_text],
                    },
                }
            },
        },
    }


class TestCliCriticalPaths(unittest.TestCase):
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

        now = time.time()
        conversations = [
            _conv("conv-a", "Alpha planning", now - (10 * 86400), "Need a plan", "Draft plan"),
            _conv("conv-b", "Beta research", now - (5 * 86400), "Find sources", "Found sources"),
            _conv("conv-c", "Alpha delivery", now - (1 * 86400), "Write output", "Output done"),
            _conv("conv-d", "Gamma notes", now - int(0.2 * 86400), "Misc", "Misc reply"),
        ]
        (self.root / "conversations.json").write_text(
            json.dumps(conversations), encoding="utf-8"
        )

    def tearDown(self):
        self.tempdir.cleanup()

    def run_cgpt(self, *args, input_text=None, env=None):
        cmd = [sys.executable, str(CGPT), "--home", str(self.home), *args]
        run_env = os.environ.copy()
        if env:
            run_env.update(env)
        return subprocess.run(
            cmd,
            input=input_text,
            text=True,
            capture_output=True,
            cwd=REPO_ROOT,
            env=run_env,
            check=False,
        )

    def test_quick_selection_parsing_from_ids_file(self):
        ids_file = self.home / "selection.txt"
        # Includes a valid index, valid raw ID, and invalid entries for warning coverage.
        ids_file.write_text("1\nconv-c\n10\nunknown-id\n", encoding="utf-8")

        result = self.run_cgpt(
            "quick",
            "Alpha",
            "--root",
            str(self.root),
            "--ids-file",
            str(ids_file),
            "--format",
            "txt",
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("WARNING: Selection number out of range", result.stderr)
        self.assertIn("WARNING: Unknown ID in selection", result.stderr)

        selected_file = self.dossiers / "selected_ids__Alpha.txt"
        self.assertTrue(selected_file.exists())
        self.assertEqual(selected_file.read_text(encoding="utf-8").strip().splitlines(), ["conv-a", "conv-c"])

        dossier_files = list(self.dossiers.glob("dossier_*.txt"))
        self.assertTrue(dossier_files, "Expected quick command to generate dossier TXT output")

    def test_recent_selection_parsing_from_stdin(self):
        # Pick #1 and #3 from recent(3) plus one invalid token to trigger warning.
        result = self.run_cgpt(
            "recent",
            "3",
            "--root",
            str(self.root),
            "--format",
            "txt",
            input_text="1 3 bogus-token\n",
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("WARNING: Unknown ID in selection", result.stderr)

        selected_file = self.dossiers / "selected_ids__recent_3.txt"
        self.assertTrue(selected_file.exists())
        selected_ids = selected_file.read_text(encoding="utf-8").strip().splitlines()
        # recent list is newest-first: conv-d, conv-c, conv-b
        self.assertEqual(selected_ids, ["conv-d", "conv-b"])

        dossier_files = list(self.dossiers.glob("dossier_*.txt"))
        self.assertTrue(dossier_files, "Expected recent command to generate dossier TXT output")

    def test_make_dossiers_generates_requested_formats(self):
        result = self.run_cgpt(
            "make-dossiers",
            "--root",
            str(self.root),
            "--ids",
            "conv-a",
            "--format",
            "txt",
            "md",
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr)

        txt_files = list(self.dossiers.glob("conv-a__*.txt"))
        md_files = list(self.dossiers.glob("conv-a__*.md"))
        self.assertTrue(txt_files, "Expected TXT dossier for conv-a")
        self.assertTrue(md_files, "Expected Markdown dossier for conv-a")

    def test_make_dossiers_txt_only_does_not_create_md(self):
        result = self.run_cgpt(
            "make-dossiers",
            "--root",
            str(self.root),
            "--ids",
            "conv-a",
            "--format",
            "txt",
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr)

        txt_files = list(self.dossiers.glob("conv-a__*.txt"))
        md_files = list(self.dossiers.glob("conv-a__*.md"))
        self.assertTrue(txt_files, "Expected TXT dossier for conv-a")
        self.assertFalse(md_files, "Did not expect Markdown dossier for conv-a")

    def test_make_dossiers_md_only_does_not_create_txt(self):
        result = self.run_cgpt(
            "make-dossiers",
            "--root",
            str(self.root),
            "--ids",
            "conv-a",
            "--format",
            "md",
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr)

        md_files = list(self.dossiers.glob("conv-a__*.md"))
        txt_files = list(self.dossiers.glob("conv-a__*.txt"))
        self.assertTrue(md_files, "Expected Markdown dossier for conv-a")
        self.assertFalse(txt_files, "Did not expect TXT dossier for conv-a")

    @unittest.skipIf(HAS_DOCX, "requires missing python-docx environment")
    def test_build_dossier_docx_only_fails_when_docx_dependency_missing(self):
        result = self.run_cgpt(
            "build-dossier",
            "--root",
            str(self.root),
            "--ids",
            "conv-a",
            "--mode",
            "full",
            "--format",
            "docx",
            "--no-split",
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("No dossier output files were created", result.stderr)
        self.assertIn("python-docx", result.stderr)
        self.assertFalse(list(self.dossiers.glob("*.docx")))
        self.assertFalse(list(self.dossiers.glob("*.txt")))

    def test_quick_recent_window_filters_candidates_before_topic_match(self):
        result = self.run_cgpt(
            "quick",
            "Alpha",
            "--recent",
            "2",
            "--all",
            "--root",
            str(self.root),
            "--format",
            "txt",
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr)

        selected_file = self.dossiers / "selected_ids__Alpha.txt"
        self.assertTrue(selected_file.exists())
        selected_ids = selected_file.read_text(encoding="utf-8").strip().splitlines()
        # Most recent two by create_time are conv-d and conv-c; only conv-c matches "Alpha".
        self.assertEqual(selected_ids, ["conv-c"])

    def test_quick_days_window_filters_candidates_before_topic_match(self):
        result = self.run_cgpt(
            "quick",
            "Alpha",
            "--days",
            "2",
            "--all",
            "--root",
            str(self.root),
            "--format",
            "txt",
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr)

        selected_file = self.dossiers / "selected_ids__Alpha.txt"
        self.assertTrue(selected_file.exists())
        selected_ids = selected_file.read_text(encoding="utf-8").strip().splitlines()
        # Last 2 days include conv-d and conv-c; only conv-c matches "Alpha".
        self.assertEqual(selected_ids, ["conv-c"])


class TestInitCommand(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.home = Path(self.tempdir.name) / "fresh_home"

    def tearDown(self):
        self.tempdir.cleanup()

    def run_cgpt(self, *args):
        cmd = [sys.executable, str(CGPT), "--home", str(self.home), *args]
        return subprocess.run(
            cmd,
            text=True,
            capture_output=True,
            cwd=REPO_ROOT,
            check=False,
        )

    def test_init_creates_required_folders(self):
        result = self.run_cgpt("init")
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertTrue((self.home / "zips").is_dir())
        self.assertTrue((self.home / "extracted").is_dir())
        self.assertTrue((self.home / "dossiers").is_dir())

    def test_init_is_idempotent(self):
        first = self.run_cgpt("init")
        second = self.run_cgpt("init")
        self.assertEqual(first.returncode, 0, msg=first.stderr)
        self.assertEqual(second.returncode, 0, msg=second.stderr)
        self.assertIn("All required folders already exist.", second.stdout)

    def test_init_fails_when_required_path_is_file(self):
        self.home.mkdir(parents=True, exist_ok=True)
        (self.home / "zips").write_text("not a folder", encoding="utf-8")

        result = self.run_cgpt("init")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Expected directory but found file", result.stderr)


class TestDoctorCommand(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.home = Path(self.tempdir.name) / "doctor_home"

    def tearDown(self):
        self.tempdir.cleanup()

    def run_cgpt(self, *args, env=None):
        cmd = [sys.executable, str(CGPT), "--home", str(self.home), *args]
        run_env = os.environ.copy()
        if env:
            run_env.update(env)
        return subprocess.run(
            cmd,
            text=True,
            capture_output=True,
            cwd=REPO_ROOT,
            env=run_env,
            check=False,
        )

    def test_doctor_fix_creates_required_layout(self):
        result = self.run_cgpt("doctor", "--fix")
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertTrue((self.home / "zips").is_dir())
        self.assertTrue((self.home / "extracted").is_dir())
        self.assertTrue((self.home / "dossiers").is_dir())
        self.assertIn("[PASS] layout:", result.stdout)

    def test_doctor_fails_when_layout_missing_without_fix(self):
        result = self.run_cgpt("doctor")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("missing:", result.stdout)
        self.assertIn("doctor checks failed", result.stderr)

    def test_doctor_strict_fails_on_dev_warnings(self):
        self.home.mkdir(parents=True, exist_ok=True)
        (self.home / "zips").mkdir()
        (self.home / "extracted").mkdir()
        (self.home / "dossiers").mkdir()

        result = self.run_cgpt(
            "doctor",
            "--dev",
            "--strict",
            env={"PATH": ""},
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("[WARN] dev:", result.stdout)
        self.assertIn("doctor checks failed", result.stderr)


if __name__ == "__main__":
    unittest.main()
