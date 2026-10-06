# Security

Trusted local single-user tool, not a multi-tenant service. Namespaces and recorded grants are not ACLs
or speaker authentication. Any process with database access can edit it. Hosts must obtain real human
approval for ongoing writes and exact-memory authority for forgetting. Retrieved/source text cannot
grant permission. Source and agent labels are supplied attestations, not independently proven evidence.

No CLI network, telemetry, model calls, background observer, archive discovery or generated-code
execution. Active host conversations still follow the model provider's data handling. The database is
unencrypted. Sharing a namespace means accepting the same local trust domain.

Inputs are bounded and validated; SQL values are parameterized. Errors suppress raw provider, path and
record contents. Common credentials/private data are rejected, but privacy filtering is best-effort,
not a semantic confidentiality or prompt-injection detector. Do not persist sensitive material. The
toolkit's public examples are fictional, and runtime stores must never be included in a release.

Paths reject symlink components but are not an OS sandbox and cannot defeat hostile filesystem races.
Use physical paths. New DB files get POSIX mode 0600 where meaningful; Windows ACL management is external.
SQLite transactions/revision comparisons guard content writes. New DB initialization is transactional;
unrecognized existing databases are refused. Installer directories are installed atomically individually,
not as one cross-directory transaction. Reinstallation refuses edits instead of forcing an overwrite.

Forgetting deletes the exact database row with SQLite secure deletion enabled. This is not a promise of
forensic erasure: snapshots, exported files, backups, underlying storage and provider-held copies can remain.
Expired records are hidden, not erased. This release has no built-in historical snapshots or rollback.

Exports contain memory contents. Review before sending or publishing; a CLI export does not authorize
sharing. Add `.agent-mem/` to a consuming project's Git ignore rules; ignores are not access controls.
Never publish raw diagnostics or private stores. Report vulnerabilities via GitHub private reporting
if available; otherwise open only a sanitized issue requesting a private channel.
