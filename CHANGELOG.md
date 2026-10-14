# Changelog

## Unreleased

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
