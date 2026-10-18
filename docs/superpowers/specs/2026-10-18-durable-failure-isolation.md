# Durable failure isolation and explicit recovery

Approved scope: maintainer's 2026-10-18 instruction; native execution and existing
question opt-out apply. Experimental Lab blueprint, no SDK or live changes.

Build a consumer-owned, single-host durable admission journal. It surrounds a
whole bounded SDK operation; it does not implement workflow checkpoints,
provider accounting, tool replay or a replacement recorder. Harness and Runtime
remain authoritative for those concerns. An atomic private file, fsync and a
process lock fit the existing local experiment consumer. PostgreSQL service
recovery remains a separate existing blueprint; this is not distributed fencing.

Every admitted work item retains its entire maximum reservation, including after
recovery. A known overrun retains the greater actual count and blocks admission
globally. Unknown or failed work is isolated individually: unrelated explicitly
authorized work can use only the remaining preauthorized budget. A journal is
containment inside a separately reserved allowance, never additional allowance.
Existing historical ledgers and stop-on-unknown policies must remain unchanged.

Identity binds trusted scope, immutable operation/configuration and limits.
Each work item binds its input/configuration digest. Admission is single-use;
start is persisted before SDK dispatch. Crash before/after dispatch stays
uncertain. Quarantine revokes the writer token. A stale writer cannot commit;
an already in-flight request cannot be recalled by journal fencing. Never
automatically expire and reassign work, replay calls, or reuse an identifier.

Recovery requires an explicit host decision digest and matching work binding.
It either closes unknown work conservatively or records reconciled, host-verified
SDK evidence/counts. It never dispatches or grants retry consent. A new attempt
requires its own authorization, identifier and full reservation. Conflicting
decisions/evidence are rejected; exact recovery replay is idempotent. Recovery
may not accept a successful outcome without known counts and an evidence digest.

Per case: 4 provider requests / 2 tool calls / 8192 reported tokens / 600 seconds
/ 512 output tokens per response. Deadlines are persisted and never reset by
restart or recovery. Runtime enforces execution limits; the journal records
terminal evidence and rejects late acceptance. Ceiling accounting stays
1558 / 637 / 1976623; charged 1509 / 610 / 1835168; 9 unknowns retained.

Qualify crash boundaries in real subprocesses, concurrent admission, stale
writers, scope/input drift, malformed files/counts, expiry, and receipt-only
recovery without network. Exercise both public wire fixtures through installed
SDKs, with one failed sample and an unrelated completed sample. No live run,
model tuning or benefit claim. Memory and correction remain experimental.
