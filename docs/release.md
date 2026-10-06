# Agent Mem v0.1.0

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
