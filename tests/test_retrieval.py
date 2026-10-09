"""Layered retrieval with fictional data; no model or real conversation archives."""

import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from test_memory import EXAMPLE, SCRIPT


class Retrieval(unittest.TestCase):
    def test_timeline_and_budgeted_context(self):
        with tempfile.TemporaryDirectory() as directory:
            store = Path(directory).resolve() / "memory.sqlite3"

            def call(*args, scope="study", value=None, error=None):
                result = subprocess.run(
                    [sys.executable, str(SCRIPT), "--db", str(store), "--scope", scope, *args],
                    input=json.dumps(value) if value is not None else None,
                    text=True, encoding="utf-8", capture_output=True)
                if error:
                    self.assertEqual(result.returncode, 2)
                    self.assertEqual(json.loads(result.stderr)["error"], error)
                    return
                self.assertEqual(result.returncode, 0, result.stderr)
                return json.loads(result.stdout)

            call("grant", "--decision", "approve")
            ids = [call("add", "--input", "-", value={**EXAMPLE, "title": f"学习卡片 {i}"})["id"]
                   for i in range(5)]
            call("grant", "--decision", "approve", scope="other")
            hidden = call("add", "--input", "-", scope="other", value=EXAMPLE)["id"]
            expired = call("add", "--input", "-", value={**EXAMPLE, "expires_at": "2000-01-01T00:00:00Z"})
            # Equal timestamps must still have a deterministic chronological order.
            with closing(sqlite3.connect(store)) as db, db:
                db.execute("UPDATE memories SET updated_at='2026-01-01T00:00:00.000000+00:00'")
            ordered = sorted(ids)
            result = call("timeline", ordered[2], "--before", "1", "--after", "1")
            self.assertEqual([v["id"] for v in result["items"]], ordered[1:4])
            self.assertEqual(result["anchor_id"], ordered[2])
            self.assertEqual([v["id"] for v in call("timeline", ordered[2], "--before", "0",
                                                   "--after", "0")["items"]], [ordered[2]])
            self.assertTrue(all("body" not in v and "source" not in v for v in result["items"]))
            self.assertEqual(len(call("timeline", ordered[0])["items"]), 4)
            self.assertEqual(len(call("timeline", ordered[0], "--after", "20")["items"]), 5)
            call("timeline", hidden, error="memory_not_found_or_expired")
            call("timeline", expired["id"], error="memory_not_found_or_expired")
            call("timeline", "bad-id", error="invalid_id")
            call("timeline", ids[0], "--before", "-1", error="invalid_timeline_bounds")
            call("timeline", ids[0], "--after", "21", error="invalid_timeline_bounds")

            call("grant", "--decision", "pause")
            result = call("context", "学习 卡片", "--limit", "2", "--max-chars", "2000")
            self.assertEqual(result["ids"], ordered[:2])
            self.assertTrue(result["has_more"])
            self.assertEqual(result["omitted_ids"], [])
            self.assertEqual(result["characters"], len(result["context"]))
            self.assertLessEqual(result["characters"], 2000)
            records = [json.loads(line) for line in result["context"].splitlines()[1:]]
            self.assertEqual([v["id"] for v in records], result["ids"])
            self.assertTrue(all(v["source"] == EXAMPLE["source"] and v["revision"] == 1 for v in records))
            self.assertEqual(call("context", "%")["ids"], [])
            self.assertEqual(call("context", "学习", scope="empty")["ids"], [])
            call("context", "x", "--max-chars", "255", error="invalid_context_bounds")
            call("context", "x", "--max-chars", "32001", error="invalid_context_bounds")
            call("context", "x", "--limit", "21", error="invalid_context_bounds")
            call("context", "x" * 501, error="invalid_search_bounds")
            small = call("context", "学习", "--limit", "2", "--max-chars", "256")
            self.assertEqual(small["ids"], [])
            self.assertEqual(small["omitted_ids"], ordered[:2])
            self.assertLessEqual(small["characters"], 256)
            self.assertEqual(call("status")["decision"], "pause")
            self.assertEqual(call("status")["active"], 5)

            call("grant", "--decision", "approve")
            big = call("add", "--input", "-", value={**EXAMPLE, "body": "卡" * 8000})["id"]
            mixed = call("context", "学习", "--limit", "2", "--max-chars", "2000")
            self.assertEqual(mixed["omitted_ids"], [big])
            self.assertEqual(mixed["ids"], ordered[:1])
            call("forget", big, "--revision", "1")
            self.assertNotIn(big, call("context", "学习")["ids"])
            call("update", ordered[0], "--revision", "1", "--input", "-",
                 value={**EXAMPLE, "body": "每张卡片附一个例子和公开来源。"})
            corrected = call("context", "学习", "--limit", "1")
            latest = json.loads(corrected["context"].splitlines()[1])
            self.assertEqual(latest["revision"], 2)
            self.assertEqual(latest["id"], ordered[0])
            self.assertEqual(latest["body"], "每张卡片附一个例子和公开来源。")
