# Release validation

## 0.2.0 local checks, 2026-10-09

- Both fictional regression checks passed on macOS with Python 3.10, 3.11 and 3.13.
- Ruff, compilation and Agent Skills structural validation passed; wheel/sdist builds passed.
- Installed the wheel in an isolated environment, outside the source directory. Verified the 0.2.0
  entry point, both installed host scripts, timeline and bounded context against a fictional database
  created with the actual v0.1.0 script. Retrieval left that database's bytes unchanged.
- Tests cover same-time ordering, scoped/expired exclusion, paused recall, complete-record budgets,
  oversized omissions, more-match flags, correction visibility and forgetting. No real memories used.
- Gitleaks and an internal-identifier check run before push. Scanner success is not proof that every
  sensitive detail can be detected; public changes are also reviewed manually.
- Chinese README/launch review preserved commands, numeric limits, consent and unverified-host claims.
  Mechanical punctuation/dash/empty-emphasis scan: 0 matches; no exceptions. Added upgrade and retrieval
  instructions without changing unrelated prose.

Windows/Linux execution is delegated to the existing CI matrix; consult the run for this commit.
Automatic host invocation, model-driven recall quality and token savings are not tested or claimed.
No startup hooks, transcript capture, vector search or new release tag was created in this upgrade.

## Earlier 0.1.0 checks

Local release checks on 2026-10-06:

- The single end-to-end regression check passed on Python 3.11. It invokes independent CLI processes
  for the complete fictional lifecycle and both installed host scripts; it is not a paid-model benchmark.
- Ruff, Python compilation and Agent Skills structural validation passed.
- Wheel building passed; package-data includes the standalone Skill.
- Public files use fictional examples. Review and a secret scanner are performed before public push;
  no automatic scanner can establish complete confidentiality.
- Chinese README/launch draft review preserved CLI commands, version/runtime numbers, permissions and
  unverified-host boundaries. The mechanical scan found 0 mixed Chinese/half-width punctuation,
  decorative dash or empty-emphasis matches. No prose changes were needed after that scan.

CI executes the same deterministic check on Linux/Python 3.10 and 3.13, macOS/3.11 and Windows/3.11;
consult Actions for the current run outcome. Model-driven memory selection/consent and automatic host
invocation remain unverified. A host with no local Python access cannot use this release.
