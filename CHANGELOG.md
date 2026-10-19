# Changelog

## Unreleased

- Enforce the documented UTF-8 JSON input contract before any database access, rejecting auto-detected UTF-16/32 inputs. Preserve optional UTF-8 BOM compatibility and cover non-ASCII cards through the CLI.

- Fault-inject a second-host installation write failure and verify staging cleanup, preservation of the first installed copy and an idempotent retry. Runtime behavior is unchanged; this is not automatic rollback.

- Preflight every selected host before installation, so a known conflict in a later host does not leave a newly installed earlier copy. This is not rollback for later I/O failures.

- Add a two-process revision-conflict regression: exactly one competing correction succeeds, and the stored body matches the winning revision. Runtime behavior is unchanged.

- Cover cross-scope update and forget attempts even when both scopes have write approval; the owner record and revision stay unchanged. Runtime behavior is unchanged.

- Add a subprocess regression proving malformed, privacy-rejected and unknown-field updates preserve the complete original record and revision. Runtime behavior is unchanged.

- Reject duplicate JSON fields in memory inputs instead of silently keeping the last value; invalid cards never reach storage.
- Add a CLI regression proving rejection leaves the approved memory store unchanged.

## 0.2.0 — 2026-10-09

- Three-layer recall: compact search, same-scope last-update timeline, selected full records.
- Bounded context with complete provenance, untrusted-data warning, omitted IDs and more-match flag.
- Consistent read snapshots; no database migration, new runtime dependencies or automatic capture.
- Fictional regression coverage for budgets, time ties, scope/expiry, corrections and installed scripts.
- Updated portable Skill and bilingual usage/upgrade instructions. Existing 0.1.0 tag is unchanged.

## 0.1.0 — 2026-10-06

- Portable Agent Mem Skill and standalone local CLI; Codex/Claude/generic/custom-directory installers.
- Scoped consent, SQLite persistence, compact search/full retrieval, update conflicts, pause, expiry,
  forgetting and JSON export.
- Bounded inputs, best-effort privacy rejection, symlink/unknown-database/manual-edit protections.
- Fictional example, runnable cross-process regression check and three-platform CI.
- No automatic capture, host startup hooks, cloud sync, import, vector search or live-model claims.
