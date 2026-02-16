import json
import os
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

    def test_extract_rejects_symlink_member(self):
        zpath = self.zips / "unsafe_symlink.zip"
        with zipfile.ZipFile(zpath, "w") as zf:
            info = zipfile.ZipInfo("link_to_payload")
            info.create_system = 3  # unix
            info.external_attr = (0o120777 << 16)
            zf.writestr(info, "conversations.json")

        result = self.run_cgpt("extract", str(zpath))

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("special", result.stderr.lower())

    def test_extract_rejects_zip_member_count_over_limit(self):
        zpath = self.zips / "unsafe_member_count.zip"
        with zipfile.ZipFile(zpath, "w") as zf:
            for i in range(3):
                zf.writestr(f"file_{i}.txt", "x")

        result = self.run_cgpt(
            "extract",
            str(zpath),
            env={"CGPT_MAX_ZIP_MEMBERS": "2"},
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("member", result.stderr.lower())
        self.assertIn("limit", result.stderr.lower())

    def test_extract_rejects_zip_uncompressed_size_over_limit(self):
        zpath = self.zips / "unsafe_uncompressed_size.zip"
        payload = "x" * 24
        with zipfile.ZipFile(zpath, "w") as zf:
            zf.writestr("a.txt", payload)
            zf.writestr("b.txt", payload)

        result = self.run_cgpt(
            "extract",
            str(zpath),
            env={"CGPT_MAX_ZIP_UNCOMPRESSED_BYTES": "32"},
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("uncompressed", result.stderr.lower())
        self.assertIn("limit", result.stderr.lower())

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
                "no second term here",
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

    def test_quick_fails_on_unknown_config_key(self):
        bad = self.home / "unknown_key_config.json"
        bad.write_text(
            json.dumps({"search_terms": ["alpha"], "unknown_key": True}),
            encoding="utf-8",
        )
        result = self.run_cgpt(
            "quick",
            "--config",
            str(bad),
            "--all",
            "--root",
            str(self.root),
            "alpha",
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unknown", result.stderr.lower())
        self.assertIn("config", result.stderr.lower())

    def test_build_dossier_fails_on_wrong_typed_config_key(self):
        bad = self.home / "wrong_type_config.json"
        bad.write_text(
            json.dumps({"thread_filters": "not-a-dict"}),
            encoding="utf-8",
        )
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
        self.assertIn("thread_filters", result.stderr.lower())
        self.assertIn("config", result.stderr.lower())


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


class TestRemainingEdgeCases(EdgeCaseBase):
    def setUp(self):
        super().setUp()
        self.root = self.extracted / "remaining_edge_export"
        now = time.time()
        conversations = [
            _conv("conv-a", "Alpha title", now - 1000, "alpha content", "assistant alpha"),
        ]
        self.write_conversations(self.root, conversations)

    def _write_zip(self, path: Path, members):
        with zipfile.ZipFile(path, "w") as zf:
            for member_name, payload in members.items():
                zf.writestr(member_name, payload)

    def test_extract_same_zip_stem_replaces_stale_files(self):
        zpath = self.zips / "same_stem.zip"
        out_dir = self.extracted / "same_stem"

        self._write_zip(
            zpath,
            {
                "conversations.json": "[]",
                "stale_only.txt": "first payload",
            },
        )
        first = self.run_cgpt("extract", str(zpath))
        self.assertEqual(first.returncode, 0, msg=first.stderr)
        self.assertTrue((out_dir / "stale_only.txt").exists())

        self._write_zip(
            zpath,
            {
                "conversations.json": "[]",
                "fresh_only.txt": "second payload",
            },
        )
        second = self.run_cgpt("extract", str(zpath))
        self.assertEqual(second.returncode, 0, msg=second.stderr)
        self.assertFalse((out_dir / "stale_only.txt").exists())
        self.assertTrue((out_dir / "fresh_only.txt").exists())

    def test_quick_where_messages_tolerates_invalid_message_create_time(self):
        bad_conv = {
            "id": "conv-bad-msg-ts",
            "title": "Bad message timestamp",
            "create_time": time.time(),
            "mapping": {
                "u1": {
                    "message": {
                        "create_time": "not-a-float",
                        "author": {"role": "user"},
                        "content": {"content_type": "text", "parts": ["alpha in message"]},
                    }
                }
            },
        }
        self.write_conversations(self.root, [bad_conv])

        result = self.run_cgpt(
            "quick",
            "--where",
            "messages",
            "--all",
            "--root",
            str(self.root),
            "alpha",
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        selected = (self.dossiers / "selected_ids__alpha.txt").read_text(encoding="utf-8")
        self.assertIn("conv-bad-msg-ts", selected)

    def test_find_prefers_conversation_like_json_when_largest_is_unrelated(self):
        root = self.extracted / "json_discovery_mix"
        root.mkdir(parents=True, exist_ok=True)
        (root / "huge.json").write_text(
            json.dumps({"payload": "x" * 200000}), encoding="utf-8"
        )
        (root / "archive.json").write_text(
            json.dumps(
                [
                    _conv(
                        "conv-json-choice",
                        "Discovery pick",
                        time.time(),
                        "alpha",
                        "beta",
                    )
                ]
            ),
            encoding="utf-8",
        )

        result = self.run_cgpt("ids", "--root", str(root))
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("conv-json-choice", result.stdout)

    def test_ids_fails_when_no_conversation_like_json_exists(self):
        root = self.extracted / "json_discovery_none"
        root.mkdir(parents=True, exist_ok=True)
        (root / "data.json").write_text(
            json.dumps({"payload": "not conversation export"}), encoding="utf-8"
        )

        result = self.run_cgpt("ids", "--root", str(root))
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("conversation", result.stderr.lower())
        self.assertIn("json", result.stderr.lower())

    def test_build_dossier_rejects_negative_context(self):
        result = self.run_cgpt(
            "build-dossier",
            "--root",
            str(self.root),
            "--ids",
            "conv-a",
            "--mode",
            "excerpts",
            "--topic",
            "alpha",
            "--context",
            "-1",
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("context", result.stderr.lower())

    def test_quick_rejects_excessive_context(self):
        result = self.run_cgpt(
            "quick",
            "--root",
            str(self.root),
            "--context",
            "99999",
            "--all",
            "alpha",
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("context", result.stderr.lower())

    def test_build_dossier_rejects_name_that_normalizes_empty(self):
        result = self.run_cgpt(
            "build-dossier",
            "--root",
            str(self.root),
            "--ids",
            "conv-a",
            "--mode",
            "full",
            "--name",
            "!!!",
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--name", result.stderr)

    def test_build_dossier_fails_on_missing_patterns_file(self):
        missing_patterns = self.home / "missing_patterns.txt"
        result = self.run_cgpt(
            "build-dossier",
            "--root",
            str(self.root),
            "--ids",
            "conv-a",
            "--mode",
            "full",
            "--patterns-file",
            str(missing_patterns),
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("patterns", result.stderr.lower())
        self.assertIn("not found", result.stderr.lower())

    def test_quick_fails_on_missing_patterns_file(self):
        missing_patterns = self.home / "missing_patterns.txt"
        result = self.run_cgpt(
            "quick",
            "--all",
            "--root",
            str(self.root),
            "--patterns-file",
            str(missing_patterns),
            "alpha",
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("patterns", result.stderr.lower())
        self.assertIn("not found", result.stderr.lower())

    def test_recent_fails_on_missing_patterns_file(self):
        missing_patterns = self.home / "missing_patterns.txt"
        result = self.run_cgpt(
            "recent",
            "1",
            "--all",
            "--root",
            str(self.root),
            "--patterns-file",
            str(missing_patterns),
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("patterns", result.stderr.lower())
        self.assertIn("not found", result.stderr.lower())

    def test_build_dossier_split_fails_on_missing_used_links_file(self):
        missing_used_links = self.home / "missing_used_links.txt"
        result = self.run_cgpt(
            "build-dossier",
            "--root",
            str(self.root),
            "--ids",
            "conv-a",
            "--mode",
            "full",
            "--split",
            "--used-links-file",
            str(missing_used_links),
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("used-links", result.stderr.lower())
        self.assertIn("not found", result.stderr.lower())

    def test_build_dossier_split_tolerates_string_create_time_in_working_index(self):
        self.write_conversations(
            self.root,
            [
                _conv(
                    "conv-string-ts",
                    "Alpha title",
                    "not-a-number",
                    "alpha content",
                    "assistant alpha",
                )
            ],
        )
        result = self.run_cgpt(
            "build-dossier",
            "--root",
            str(self.root),
            "--ids",
            "conv-string-ts",
            "--mode",
            "full",
            "--split",
            "--format",
            "txt",
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertNotIn("traceback", result.stderr.lower())

    def test_build_dossier_fails_on_duplicate_conversation_ids(self):
        now = time.time()
        dup = [
            _conv("dup-1", "Alpha first", now - 1000, "alpha", "beta"),
            _conv("dup-1", "Alpha second", now - 900, "alpha", "beta"),
        ]
        self.write_conversations(self.root, dup)
        result = self.run_cgpt(
            "build-dossier",
            "--root",
            str(self.root),
            "--ids",
            "dup-1",
            "--mode",
            "full",
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("duplicate", result.stderr.lower())
        self.assertIn("dup-1", result.stderr)

    def test_make_dossiers_fails_on_duplicate_conversation_ids(self):
        now = time.time()
        dup = [
            _conv("dup-2", "Alpha first", now - 1000, "alpha", "beta"),
            _conv("dup-2", "Alpha second", now - 900, "alpha", "beta"),
        ]
        self.write_conversations(self.root, dup)
        result = self.run_cgpt(
            "make-dossiers",
            "--root",
            str(self.root),
            "--ids",
            "dup-2",
            "--format",
            "txt",
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("duplicate", result.stderr.lower())
        self.assertIn("dup-2", result.stderr)


class TestJsonDiscoveryScaling(unittest.TestCase):
    def test_find_conversations_json_limits_candidate_parsing_per_priority_bucket(self):
        import cgpt as cgpt_module

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            nested = root / "nested"
            nested.mkdir(parents=True, exist_ok=True)

            for i in range(12):
                (nested / f"conversations_noise_{i}.json").write_text(
                    json.dumps({"payload": f"bad-{i}"}),
                    encoding="utf-8",
                )
                (nested / f"data_noise_{i}.json").write_text(
                    json.dumps({"payload": f"fallback-bad-{i}"}),
                    encoding="utf-8",
                )

            valid_path = nested / "archive.json"
            valid_path.write_text(
                json.dumps(
                    [
                        {
                            "id": "conv-scale-valid",
                            "title": "Scaled discovery",
                            "create_time": time.time(),
                            "mapping": {},
                            "padding": ("x" * 5000),
                        }
                    ]
                ),
                encoding="utf-8",
            )

            bucket_limit = 4
            original_limit = cgpt_module.JSON_DISCOVERY_BUCKET_LIMIT
            original_loader = cgpt_module.load_json_loose
            calls = [0]

            def counting_loader(path: Path):
                calls[0] += 1
                return original_loader(path)

            try:
                cgpt_module.JSON_DISCOVERY_BUCKET_LIMIT = bucket_limit
                cgpt_module.load_json_loose = counting_loader
                picked = cgpt_module.find_conversations_json(root)
            finally:
                cgpt_module.JSON_DISCOVERY_BUCKET_LIMIT = original_limit
                cgpt_module.load_json_loose = original_loader

            self.assertIsNotNone(picked)
            self.assertEqual(picked.resolve(), valid_path.resolve())
            self.assertLessEqual(calls[0], bucket_limit * 2)


if __name__ == "__main__":
    unittest.main()
