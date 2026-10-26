"""One isolated end-to-end regression check; fictional records, no agent model."""

import io
import json
import os
import runpy
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "agent_mem/cli.py"
EXAMPLE = {"kind": "preference", "title": "学习卡片格式",
           "body": "每张学习卡片只放一个问题，附一个简短例子。",
           "source": "Fictional user confirmation", "agent": "host-a"}


class MemoryLoop(unittest.TestCase):
    def test_consent_check_and_mutation_share_a_write_transaction(self):
        runtime = runpy.run_path(str(REPO / "agent_mem/skills/agent-mem/scripts/mem.py"))
        original_approved = runtime["approved"]
        with tempfile.TemporaryDirectory() as directory:
            store = Path(directory).resolve() / "memory.sqlite3"
            command = [sys.executable, str(SCRIPT), "--db", str(store), "--scope", "study"]
            subprocess.run(command + ["grant", "--decision", "approve"], capture_output=True, check=True)
            source = Path(directory) / "fictional.json"
            source.write_text(json.dumps(EXAMPLE), encoding="utf-8")

            def check_locked(db, scope):
                original_approved(db, scope)
                with closing(sqlite3.connect(store, timeout=0)) as other, other:
                    with self.assertRaisesRegex(sqlite3.OperationalError, "locked"):
                        other.execute("UPDATE grants SET decision='pause' WHERE scope=?", (scope,))

            args = ["--db", str(store), "--scope", "study"]
            with patch.dict(runtime["run"].__globals__, approved=check_locked), patch("sys.stdout", io.StringIO()) as output:
                self.assertEqual(runtime["main"]([*args, "add", "--input", str(source)]), 0)
                identifier = json.loads(output.getvalue())["id"]
                self.assertEqual(runtime["main"]([*args, "update", identifier, "--revision", "1",
                                                  "--input", str(source)]), 0)
            subprocess.run(command + ["grant", "--decision", "pause"], capture_output=True, check=True)
            before = store.read_bytes()
            for action in (["add"], ["update", identifier, "--revision", "2"]):
                result = subprocess.run(command + action + ["--input", str(source)], capture_output=True)
                self.assertEqual(result.returncode, 2)
                self.assertIn(b"scope_not_approved", result.stderr)
                self.assertEqual(store.read_bytes(), before)

    def test_unencodable_search_queries_fail_without_changing_the_store(self):
        runtime = runpy.run_path(str(REPO / "agent_mem/skills/agent-mem/scripts/mem.py"))
        with tempfile.TemporaryDirectory() as directory:
            store = Path(directory).resolve() / "memory.sqlite3"
            args = ["--db", str(store), "--scope", "study"]
            subprocess.run([sys.executable, str(SCRIPT), *args, "grant", "--decision", "approve"],
                           capture_output=True, check=True)
            before = store.read_bytes()
            for command in ("search", "context"):
                for query in ("\ud800", "\udcff"):
                    output, errors = io.StringIO(), io.StringIO()
                    with patch("sys.stdout", output), patch("sys.stderr", errors):
                        self.assertEqual(runtime["main"]([*args, command, query]), 2)
                    self.assertIn("invalid_search_query", errors.getvalue())
                    self.assertNotIn("Traceback", errors.getvalue())
                    self.assertNotIn(query, errors.getvalue())
                    self.assertEqual(store.read_bytes(), before)

    def test_private_ipv6_inputs_are_refused_before_storage(self):
        with tempfile.TemporaryDirectory() as directory:
            store = Path(directory).resolve() / "memory.sqlite3"
            command = [sys.executable, str(SCRIPT), "--db", str(store), "--scope", "study"]
            subprocess.run(command + ["grant", "--decision", "approve"], capture_output=True, check=True)
            before = store.read_bytes()
            for address in ("::1", "fd00::123", "fe80::123", "::ffff:192.168.1.7"):
                result = subprocess.run(command + ["add", "--input", "-"],
                                        input=json.dumps({**EXAMPLE, "body": f"Fictional address [{address}]"}),
                                        text=True, capture_output=True)
                self.assertEqual(result.returncode, 2)
                self.assertIn("privacy_check_failed", result.stderr)
                self.assertNotIn(address, result.stderr)
                self.assertEqual(store.read_bytes(), before)
            public = {**EXAMPLE, "body": "Fictional public resolver 2001:4860:4860::8888 at 09:30:00."}
            subprocess.run(command + ["add", "--input", "-"], input=json.dumps(public),
                           text=True, capture_output=True, check=True)

    def test_explicit_expired_inspection_is_read_only_and_scope_bound(self):
        with tempfile.TemporaryDirectory() as directory:
            store = Path(directory).resolve() / "memory.sqlite3"
            command = [sys.executable, str(SCRIPT), "--db", str(store), "--scope", "study"]
            subprocess.run(command + ["grant", "--decision", "approve"], capture_output=True, check=True)
            expired = {**EXAMPLE, "expires_at": "2000-01-01T00:00:00Z"}
            created = subprocess.run(command + ["add", "--input", "-"], input=json.dumps(expired),
                                     text=True, capture_output=True, check=True)
            identifier = json.loads(created.stdout)["id"]
            subprocess.run(command + ["grant", "--decision", "pause"], capture_output=True, check=True)
            before = store.read_bytes()
            self.assertEqual(subprocess.run(command + ["get", identifier], capture_output=True).returncode, 2)
            result = subprocess.run(command + ["get", identifier, "--include-expired"], capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            record = json.loads(result.stdout)
            self.assertEqual((record["body"], record["revision"], record["expires_at"]),
                             (expired["body"], 1, "2000-01-01T00:00:00.000000+00:00"))
            subprocess.run([sys.executable, str(SCRIPT), "install", "--workspace", str(store.parent),
                            "--agent", "generic"], capture_output=True, check=True)
            installed = Path(directory).resolve() / ".agents/skills/agent-mem/scripts/mem.py"
            standalone = [sys.executable, str(installed), *command[2:], "get", identifier, "--include-expired"]
            self.assertEqual(json.loads(subprocess.run(standalone, capture_output=True, check=True).stdout), record)
            other = command[:-1] + ["other", "get", identifier, "--include-expired"]
            self.assertEqual(subprocess.run(other, capture_output=True).returncode, 2)
            self.assertEqual(json.loads(subprocess.run(command + ["search"], capture_output=True,
                                                       check=True).stdout)["items"], [])
            self.assertEqual(json.loads(subprocess.run(command + ["export"], capture_output=True,
                                                       check=True).stdout)["items"], [])
            self.assertEqual(store.read_bytes(), before)

    def test_expired_memory_can_be_forgotten_while_writes_are_paused(self):
        with tempfile.TemporaryDirectory() as directory:
            store = Path(directory).resolve() / "memory.sqlite3"
            command = [sys.executable, str(SCRIPT), "--db", str(store), "--scope", "study"]
            subprocess.run(command + ["grant", "--decision", "approve"], capture_output=True, check=True)
            retained = subprocess.run(command + ["add", "--input", "-"], input=json.dumps(EXAMPLE),
                                      text=True, encoding="utf-8", capture_output=True, check=True)
            retained_id = json.loads(retained.stdout)["id"]
            original = subprocess.run(command + ["get", retained_id], capture_output=True, check=True).stdout
            created = subprocess.run(command + ["add", "--input", "-"],
                                     input=json.dumps({**EXAMPLE, "expires_at": "2000-01-01T00:00:00Z"}),
                                     text=True, encoding="utf-8", capture_output=True, check=True)
            identifier = json.loads(created.stdout)["id"]
            subprocess.run(command + ["grant", "--decision", "pause"], capture_output=True, check=True)
            hidden = subprocess.run(command + ["get", identifier], capture_output=True)
            self.assertEqual(hidden.returncode, 2)
            self.assertIn(b"memory_not_found_or_expired", hidden.stderr)
            stale = subprocess.run(command + ["forget", identifier, "--revision", "2"], capture_output=True)
            self.assertEqual(stale.returncode, 2)
            self.assertIn(b"revision_conflict", stale.stderr)
            with closing(sqlite3.connect(store)) as db:
                self.assertEqual(db.execute("SELECT revision FROM memories WHERE id=?", (identifier,)).fetchone(), (1,))
            subprocess.run(command + ["forget", identifier, "--revision", "1"], capture_output=True, check=True)
            with closing(sqlite3.connect(store)) as db:
                self.assertEqual(db.execute("SELECT count(*) FROM memories WHERE id=?", (identifier,)).fetchone()[0], 0)
                self.assertEqual(db.execute("SELECT decision FROM grants WHERE scope='study'").fetchone()[0], "pause")
            self.assertEqual(subprocess.run(command + ["get", retained_id], capture_output=True, check=True).stdout, original)

    def test_non_utf8_json_is_rejected_before_creating_a_store(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            source = root / "fictional-card.json"
            raw = json.dumps(EXAMPLE, ensure_ascii=False)
            for encoding in ("utf-16", "utf-32"):
                store = root / f"{encoding}.sqlite3"
                source.write_bytes(raw.encode(encoding))
                result = subprocess.run([sys.executable, str(SCRIPT), "--db", str(store),
                                         "add", "--input", str(source)], capture_output=True)
                self.assertEqual(result.returncode, 2)
                self.assertIn(b"invalid_json", result.stderr)
                self.assertFalse(store.exists())
            command = [sys.executable, str(SCRIPT), "--db", str(root / "valid.sqlite3")]
            subprocess.run(command + ["grant", "--decision", "approve"], capture_output=True, check=True)
            for encoding in ("utf-8", "utf-8-sig"):
                source.write_bytes(raw.encode(encoding))
                subprocess.run(command + ["add", "--input", str(source)], capture_output=True, check=True)

    def test_interrupted_second_host_install_can_be_retried_without_removing_first(self):
        install = runpy.run_path(str(REPO / "agent_mem/skills/agent-mem/scripts/mem.py"))["install"]
        write = Path.write_bytes
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            note = root / "notes.txt"
            note.write_text("Fictional workspace note", encoding="utf-8")

            def interrupted(destination, data):
                if ".claude" in destination.parts and destination.name == "mem.py":
                    raise OSError("fictional second-host write interruption")
                return write(destination, data)

            with patch.object(Path, "write_bytes", interrupted), self.assertRaises(OSError):
                install(root, "all")
            first = root / ".agents/skills/agent-mem"
            original = {p.relative_to(first).as_posix(): p.read_bytes() for p in first.rglob("*") if p.is_file()}
            self.assertEqual(set(original), {"SKILL.md", "scripts/mem.py"})
            self.assertFalse((root / ".claude/skills/agent-mem").exists())
            self.assertFalse(list((root / ".claude/skills").glob(".agent-mem-install-*")))
            install(root, "all")
            for host in (".agents", ".claude"):
                target = root / host / "skills/agent-mem"
                self.assertEqual({p.relative_to(target).as_posix(): p.read_bytes()
                                  for p in target.rglob("*") if p.is_file()}, original)
            self.assertEqual(note.read_text(encoding="utf-8"), "Fictional workspace note")

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
