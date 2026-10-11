# Production readiness milestones 1 and 2

Date: 2026-10-11. Scope authorized by the maintainer after the production coverage
assessment, including local Qwen tier routing. Extend existing Lab workflows and
qualification; no new SDK features, scheduler, automatic recovery or cloud calls.

## Intent and boundaries

Prove the released five-package train behaves safely under native transport and
database failures, preserves native state through logical restoration, and can
be consumed through ordinary PyPI installation. Exercise strong and balanced
model tiers with distinct deterministic targets and bounded local Qwen inference.
Keep installed public SDK APIs, immutable release pins and trusted host authority.
Library defects require upstream regressions/fixes; never patch installed engines.

## Native failure scenarios

Use the existing native graph and consequential fixture tool. Add owned model
transport scenarios: connection loss after request acceptance, truncated JSON,
429/503, malformed response shape and slow non-streaming response. Exercise first
and post-tool calls. Record fixture acceptance independently of recorder intents;
unknown usage is not a zero charge and explicit retry cannot bypass its budget.
Each operation terminates within its policy deadline, never automatically
redispatches and leaves an already committed domain effect unique. The next
unrelated execution succeeds and public views remain sanitized.

An owned TCP fault proxy isolates only A's Harness SQL connection. Hold A after
a durable accepted receipt, sever established and new SQL connections, observe
actual lease expiry and B's new SQL generation, then restore A's route. The old
session remains fenced, B adopts the saved receipt and A can create a fresh
session afterward. Verify the exact live A container persists across the fault.
Use SQL/event barriers and bounded polling, not timing guesses. Proxy resources
join the exact-owned durable inventory and are always cleaned up.

## Native logical restoration

Preserve legacy qualification and extend existing `qualify-recovery --mode native`.
Seed two legacy runs and four native states: a composed graph awaiting structured
approval, a saved receipt before checkpoint, a completed consequential tool and
an uncertain tool whose domain effect persisted. Require eight calls and six run
records before seeding; use three immutable native proposals. Generate all state
through real public execution and existing crash barriers, never receipt fabrication.

Take the existing consistent dump and restore into another owned database on the
same primary. Connect a genuinely fresh replica to the restored database. Verify
frozen attribution, reservations, proposal/reference/bundle identity, revisions,
artifacts, receipts, structured interaction, usage, journal signatures/tokens and
domain rows. Completed journal evidence replays; uncertain evidence grants no
dispatch. Reads/claims introduce no provider calls or tool handlers. Missing or
false evidence fails qualification. Keep snapshots and dump private and emit only
fixed booleans/counts. This remains logical restoration, not primary loss, HA/PITR
or rollback of external effects. Restore original worker configuration in finally.

## Routing and public adoption

Use public WorkflowFactory/Harness/Runtime construction against a dedicated HTTP
fixture with visibly distinct default/balanced/strong model identifiers. Prove
named selection, default selection with empty explicit tier grants, configured
but ungranted rejection, granted but absent route rejection, catalogue projection,
balanced-to-strong composition and denied client host-binding injection. Admission
failures allocate no run state and dispatch no HTTP request.

Add an explicitly opted-in loopback-only local routing script. Trusted config
maps balanced to `mlx-community--Qwen2.5-Coder-7B-Instruct-4bit` and strong to
`ThinkingCap-Qwen3.8-27B-MLX-4bit-DWQ`, with an omitted-tier default case. Read the
existing credential file only after loopback/config preflight; never export it.
Three shared calls maximum, one provider request per invocation, no tools/retries,
finite output tokens and time limits, stop at first failure, no cloud fallback.
Tier names establish routing, not a quality benchmark. Usage is not synthetic cost.

A fresh adoption script uses a temporary isolated venv and ordinary cache-free
PyPI resolution for all five exact public distribution pins, with dependencies
enabled. Verify pip-report identities/archive hashes, separately downloaded wheel
bytes and installed payloads, import ownership, CLI versions/help, pip check and
the public factory construction example. Neutral working directory and isolated
Python prevent sibling imports. Recheck manifest digest, sanitize receipts and
delete only the script-owned temporary environment. Candidate lanes cannot claim
public adoption for unpublished artifacts.

## Verification and delivery

Test fixture changes with observed failures before implementation. Run the full
source suite against audited published SDKs, build one immutable consumer image,
run affected owned native/qualification lanes on PostgreSQL 16 and 18, and retain
zero-skip cleanup receipts. Update exact count contracts only after collection.
The four native Linux architecture/database CI cells remain required. Public
adoption gets a released-only CI check; local Qwen never runs in default CI.
Record actual limits and failed attempts; synthetic evidence never implies live
provider or deployment certification. Milestones 3 and 4 remain outside this work.
