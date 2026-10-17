"""One isolated end-to-end regression check; fictional records, no agent model."""

import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "agent_mem/cli.py"
EXAMPLE = {"kind": "preference", "title": "学习卡片格式",
           "body": "每张学习卡片只放一个问题，附一个简短例子。",
           "source": "Fictional user confirmation", "agent": "host-a"}


class MemoryLoop(unittest.TestCase):
    def test_all_host_install_preflights_conflicts_before_creating_any_copy(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            manual = root / ".claude/skills/agent-mem/SKILL.md"
            manual.parent.mkdir(parents=True)
            manual.write_text("Fictional manually maintained skill", encoding="utf-8")
            result = subprocess.run([sys.executable, str(SCRIPT), "install", "--workspace", str(root),
                                     "--agent", "all"], capture_output=True)
            self.assertEqual(result.returncode, 2)
            self.assertIn(b"existing_skill_conflict", result.stderr)
            self.assertFalse((root / ".agents/skills/agent-mem").exists())
            self.assertEqual(manual.read_text(encoding="utf-8"), "Fictional manually maintained skill")

    def test_competing_processes_cannot_both_apply_the_same_revision(self):
        with tempfile.TemporaryDirectory() as directory:
            store = Path(directory).resolve() / "memory.sqlite3"
            command = [sys.executable, str(SCRIPT), "--db", str(store), "--scope", "study"]
            subprocess.run(command + ["grant", "--decision", "approve"], capture_output=True, check=True)
            created = subprocess.run(command + ["add", "--input", "-"], input=json.dumps(EXAMPLE),
                                     capture_output=True, text=True, encoding="utf-8", check=True)
            identifier = json.loads(created.stdout)["id"]
            candidates = [{**EXAMPLE, "body": f"Fictional competing correction {index}."} for index in range(2)]

            def update(candidate):
                return subprocess.run(command + ["update", identifier, "--revision", "1", "--input", "-"],
                                      input=json.dumps(candidate), capture_output=True, text=True, encoding="utf-8")

            with ThreadPoolExecutor(max_workers=2) as workers:
                results = list(workers.map(update, candidates))
            self.assertEqual(sorted(result.returncode for result in results), [0, 2])
            winner = next(index for index, result in enumerate(results) if result.returncode == 0)
            self.assertIn("revision_conflict", results[1 - winner].stderr)
            current = subprocess.run(command + ["get", identifier], capture_output=True,
                                     text=True, encoding="utf-8", check=True)
            record = json.loads(current.stdout)
            self.assertEqual(record["revision"], 2)
            self.assertEqual(record["body"], candidates[winner]["body"])

    def test_other_approved_scope_cannot_update_or_forget_a_memory(self):
        with tempfile.TemporaryDirectory() as directory:
            store = Path(directory).resolve() / "memory.sqlite3"
            base = [sys.executable, str(SCRIPT), "--db", str(store)]
            owner = base + ["--scope", "study"]
            other = base + ["--scope", "other"]
            for command in (owner, other):
                subprocess.run(command + ["grant", "--decision", "approve"], capture_output=True, check=True)
            created = subprocess.run(owner + ["add", "--input", "-"], input=json.dumps(EXAMPLE),
                                     capture_output=True, text=True, encoding="utf-8", check=True)
            identifier = json.loads(created.stdout)["id"]
            original = subprocess.run(owner + ["get", identifier], capture_output=True, check=True).stdout
            for mutation in (["update", identifier, "--revision", "1", "--input", "-"],
                             ["forget", identifier, "--revision", "1"]):
                result = subprocess.run(other + mutation, input=json.dumps(EXAMPLE),
                                        capture_output=True, text=True, encoding="utf-8")
                self.assertEqual(result.returncode, 2)
                self.assertIn("memory_not_found", result.stderr)
                self.assertEqual(subprocess.run(owner + ["get", identifier], capture_output=True,
                                                check=True).stdout, original)

    def test_rejected_update_preserves_record_and_revision(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            command = [sys.executable, str(SCRIPT), "--db", str(root / "memory.sqlite3"), "--scope", "study"]
            subprocess.run(command + ["grant", "--decision", "approve"], check=True, capture_output=True)
            created = subprocess.run(command + ["add", "--input", "-"], input=json.dumps(EXAMPLE),
                                     capture_output=True, text=True, encoding="utf-8", check=True)
            identifier = json.loads(created.stdout)["id"]
            original = subprocess.run(command + ["get", identifier], capture_output=True, check=True).stdout
            source = root / "candidate.json"
            private = "sk-" + "z" * 24
            for raw in ("{broken", json.dumps({**EXAMPLE, "body": private}),
                        json.dumps({**EXAMPLE, "unknown": 1})):
                with self.subTest(case=raw == "{broken"):
                    source.write_text(raw, encoding="utf-8")
                    result = subprocess.run(command + ["update", identifier, "--revision", "1", "--input", str(source)],
                                            capture_output=True)
                    self.assertEqual(result.returncode, 2)
                    self.assertNotIn(private.encode(), result.stderr)
                    self.assertEqual(subprocess.run(command + ["get", identifier], capture_output=True,
                                                    check=True).stdout, original)

    def test_duplicate_json_fields_never_write_memory(self):
        with tempfile.TemporaryDirectory() as directory:
            store = Path(directory).resolve() / "memory.sqlite3"
            command = [sys.executable, str(SCRIPT), "--db", str(store), "--scope", "study"]
            subprocess.run(command + ["grant", "--decision", "approve"], check=True, capture_output=True)
            raw = json.dumps(EXAMPLE)[:-1] + ',"body":"fictional replacement"}'
            result = subprocess.run(command + ["add", "--input", "-"], input=raw,
                                    text=True, encoding="utf-8", capture_output=True)
            self.assertEqual(result.returncode, 2)
            self.assertNotIn("fictional replacement", result.stderr)
            with closing(sqlite3.connect(store)) as db:
                self.assertEqual(db.execute("SELECT COUNT(*) FROM memories").fetchone()[0], 0)

    def test_complete_local_protocol(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            store = root / "store/memory.sqlite3"

            def call(*args, scope="study", value=None, error=None, script=SCRIPT):
                command = [sys.executable, str(script), "--db", str(store), "--scope", scope, *args]
                result = subprocess.run(command, input=json.dumps(value) if value is not None else None,
                                        text=True, encoding="utf-8", capture_output=True,
                                        env={**os.environ, "PYTHONIOENCODING": "cp1252"})
                if error:
                    self.assertEqual(result.returncode, 2, result.stdout)
                    self.assertIn(error, json.loads(result.stderr)["error"])
                    return result.stderr
                self.assertEqual(result.returncode, 0, result.stderr)
                return json.loads(result.stdout)

            call("add", "--input", "-", value=EXAMPLE, error="scope_not_approved")
            call("grant", "--decision", "approve")  # Simulated human approval, not a model decision.
            saved = call("add", "--input", "-", value=EXAMPLE)
            identifier = saved["id"]
            self.assertEqual(saved["revision"], 1)
            hits = call("search", "学习 卡片")["items"]
            self.assertEqual(hits[0]["id"], identifier)
            self.assertNotIn("body", hits[0])
            self.assertEqual(call("search", "学习", scope="other")["items"], [])
            call("get", identifier, scope="other", error="memory_not_found")
            retrieved = call("get", identifier)
            self.assertEqual(retrieved["body"], EXAMPLE["body"])
            revised = {**EXAMPLE, "agent": "host-b", "body": "每张卡片一个问题，加一条例子和来源。"}
            self.assertEqual(call("update", identifier, "--revision", "1", "--input", "-",
                                  value=revised)["revision"], 2)
            call("update", identifier, "--revision", "1", "--input", "-",
                 value=EXAMPLE, error="revision_conflict")
            self.assertEqual(call("get", identifier)["body"], revised["body"])
            self.assertEqual(call("export")["items"][0]["agent"], "host-b")
            self.assertEqual(call("search", "%")["items"], [])
            call("search", "x", "--limit", "100", error="invalid_search_bounds")
            call("add", "--input", "-", value={**EXAMPLE, "grant": "approve"}, error="invalid_record_fields")
            call("add", "--input", "-", value={**EXAMPLE, "expires_at": "tomorrow"}, error="invalid_expiry")
            call("add", "--input", "-", value={**EXAMPLE, "body": "\ud800"}, error="invalid_text_encoding")
            private = "sk-" + "a" * 24
            message = call("add", "--input", "-", value={**EXAMPLE, "body": private}, error="privacy_check_failed")
            self.assertNotIn(private, message)
            call("add", "--input", "-", value={**EXAMPLE, "body": "C:\\Users\\private-user\\notes"},
                 error="privacy_check_failed")
            expired = call("add", "--input", "-", value={**EXAMPLE, "expires_at": "2000-01-01T00:00:00Z"})
            call("get", expired["id"], error="memory_not_found_or_expired")
            self.assertEqual(len(call("export")["items"]), 1)
            call("grant", "--decision", "pause")
            call("add", "--input", "-", value=EXAMPLE, error="scope_not_approved")
            call("forget", identifier, "--revision", "1", error="revision_conflict")
            call("forget", identifier, "--revision", "2")
            self.assertEqual(call("search")["items"], [])
            self.assertEqual(call("status")["active"], 0)
            self.assertEqual(call("status", script=REPO / "agent_mem/skills/agent-mem/scripts/mem.py")
                             ["decision"], "pause")
            self.assertNotIn(revised["body"].encode(), store.read_bytes())

            # Both host adapters use the same standalone protocol against the same store.
            call("install", "--workspace", str(root), "--agent", "all")
            call("install", "--workspace", str(root), "--agent", "all")
            for host in (".agents", ".claude"):
                standalone = root / host / "skills/agent-mem/scripts/mem.py"
                self.assertEqual(call("status", script=standalone)["decision"], "pause")
                self.assertEqual(call("context", "study", script=standalone)["ids"], [])
            controller = root / ".agents/skills/agent-mem/SKILL.md"
            controller.write_text("manual edits", encoding="utf-8")
            call("install", "--workspace", str(root), "--agent", "codex", error="existing_skill_conflict")
            self.assertEqual(controller.read_text(), "manual edits")
            unknown = root / "unrelated.sqlite3"
            with closing(sqlite3.connect(unknown)) as db:
                db.execute("CREATE TABLE unrelated (value TEXT)")
            result = subprocess.run([sys.executable, str(SCRIPT), "--db", str(unknown), "status"],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertIn("unrecognized_database", result.stderr)
            try:
                (root / "link").symlink_to(root / "store", target_is_directory=True)
            except OSError:
                pass  # Windows without symlink permission; other checks still run.
            else:
                result = subprocess.run([sys.executable, str(SCRIPT), "--db", str(root / "link/m.sqlite3"),
                                         "status"], capture_output=True, text=True)
                self.assertIn("symlink_not_allowed", result.stderr)


if __name__ == "__main__":
    unittest.main()
