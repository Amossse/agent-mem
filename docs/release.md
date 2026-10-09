# Agent Mem 0.2.0 upgrade

Independent implementation inspired by claude-mem's progressive retrieval: compact search, nearby
last-update timeline and selected complete memories. The new context command preserves provenance
within a Unicode-character budget, with explicit omissions and an untrusted-data warning.

Install the updated code from `main` (no 0.2.0 release tag is implied):

```sh
uv tool install --python 3.11 git+https://github.com/Amossse/agent-mem.git@main
```

To replace an older tag-pinned tool installation, use
`uv tool install --force --python 3.11 git+https://github.com/Amossse/agent-mem.git@main`
or `pipx install --force git+https://github.com/Amossse/agent-mem.git@main`.
Move old project Skill folders to a backup outside the destination before reinstalling; custom edits
are never overwritten. Existing schema-v1 stores remain compatible. No new runtime dependencies,
automatic capture, model calls or session-start hooks. See README for limits and validation boundaries.

## Earlier v0.1.0 release

Portable local memory shared by compatible Agent Skills hosts.

Scoped consent, SQLite persistence, compact search and full retrieval, revision-checked updates,
pause, expiry, forgetting, JSON export and standalone Codex/Claude/generic installers.

```sh
uv tool install --python 3.11 git+https://github.com/Amossse/agent-mem.git@v0.1.0
agent-mem install --agent all
```

Python 3.10+, zero runtime dependencies. No CLI network/model calls, telemetry, background observer or
chat-history discovery. All included examples are fictional. The runnable check uses independent CLI
processes and both installed host scripts; CI covers Linux/macOS/Windows.

Not a claim that all hosts are supported: local Skill/Python access is required. Model-driven host
behavior and automatic invocation remain unverified. Privacy checks are best-effort; namespace grants
are not authentication. Review any memory before sharing. See README and SECURITY for full boundaries.
