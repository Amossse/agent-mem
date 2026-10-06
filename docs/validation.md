# Release validation

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
