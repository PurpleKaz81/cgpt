import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CGPT = REPO_ROOT / "cgpt.py"


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

        conversations = [
            _conv("conv-a", "Alpha planning", 1000.0, "Need a plan", "Draft plan"),
            _conv("conv-b", "Beta research", 2000.0, "Find sources", "Found sources"),
            _conv("conv-c", "Alpha delivery", 3000.0, "Write output", "Output done"),
            _conv("conv-d", "Gamma notes", 4000.0, "Misc", "Misc reply"),
        ]
        (self.root / "conversations.json").write_text(
            json.dumps(conversations), encoding="utf-8"
        )

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


if __name__ == "__main__":
    unittest.main()
