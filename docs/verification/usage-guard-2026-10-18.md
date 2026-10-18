# Provider-neutral usage guard — 2026-10-18

The experimental Lab candidate fixes a consumer admission defect found after
the [stopped live comparison](correction-live-2026-10-18.md). The old observer
enforced component bounds only for `reported` usage. A synthetic counterexample
showed `unsupported` usage with input 101 against bound 100 continuing through
two requests and accepting the result; independent scoring then rejected the
missing breach. No such component breach was observed in the live study.

## Change

A pure normalized-count reader now separates count completeness from format or
pricing support. `reported` and `unsupported` observations both enforce bounds
when input/output/total are complete, consistent nonnegative signed 64-bit
integers. Boolean, partial, contradictory, unknown and untrusted values remain
unavailable. The observer latches either component breaches or `usageUnavailable`
before continuation or acceptance; scoring reconstructs these decisions.
Complete unsupported counts remain visible in role costs without changing their
raw usage status or implying known monetary cost.

Correction policy v2 prevents matching with historical v1 runs. Historical
recovery uses the original pinned environment. Frozen operators, prior raw
observations, receipts, reports and reservations were not rewritten.

## Offline qualification

Candidate `0.5.1+usage.1` uses the unchanged checksum-pinned response-diagnostics
SDK manifest: **unpublished Runtime `0.9.8+diagnostics.1`** and Harness `0.9.4`.
Qualification uses scripted loopback responses, not real models.

- Test-first reproductions: both supported wire formats allowed four requests
  after an unsupported input breach; complete unsupported usage erased all
  three role totals. Partial observations also failed to latch a Lab stop.
- 104 focused tests pass, including 20 count-contract cases and 42 new wire
  cases across lookup, worker-final, critic and corrector observations.
- Full source suite: 1,643 tests pass in 382.22 seconds, no skips and one
  existing Starlette/httpx deprecation warning.
- Installed usage matrix: 48 arms and 48 network-denied recoveries. Input and
  output breaches stop at each stage; missing/partial/invalid counts stay
  unknown; healthy unsupported counts permit acceptance; correct worker-final
  breaches prevent acceptance without requiring another role.
- Installed correction baseline: 48 scripted arms, 24 matched pairs, 54
  network-denied recoveries and two malformed-output checks.
- All 132 Lab payload files match source, wheel and isolated installed bytes;
  all five installed SDK payloads match their pinned wheels.
- Historical read-only proof verifies 9,853 frozen guards, all 38 prior ledger
  hashes and the current 39-ledger identity, with zero replay/provider calls.

The first installed runs completed behavioral assertions but could not write
their top-level reports because the output parent was not private. Their
evidence remains preserved; final runs use a fresh mode-0700 root. No production
permission check was weakened.

Reproduce installed checks using the commands in the
[adoption guide](../bounded-correction.md), against the exact pinned candidate
SDK payloads. The full source-suite result, artifact identities, review and
preservation receipt are recorded in the accompanying
[qualification data](data/usage-guard-2026-10-18.json).

One fresh independent review found no Critical or Important issues and approved
draft experimental publication. It independently reran the 20 count-contract
tests and checked installed evidence and v1-frame rejection. One minor remains:
the historical pinned manifest's note says “Public SDK bytes” despite its
explicit private Runtime entry. Its checksum is preserved; this report and the
PR identify the unpublished version. The review does not certify real models,
SDK internals, production trace durability, or merge/release acceptance.

## Limits and readiness

No live requests. Per arm remains 4 requests / 2 tools / 8,192 tokens / 600
seconds, with 512 output tokens per response. Charged usage remains
1,509 requests / 610 tools / 1,835,168 tokens, including nine retained unknown
reservations, against ceilings 1,558 / 637 / 1,976,623.

Memory and correction remain experimental and opt-in. This qualification closes
the Lab guard blocker; it does not establish critic or memory efficacy, certify
any model, or qualify a stable release. No Core/Runtime/Harness source, active
release manifest, model settings or ceilings changed. The review PR can preserve
the reusable blueprints now; merge/release acceptance must separately resolve the
public SDK train and ordinary clean-consumer/platform/database checks. Current
release CI still targets the published 0.5.0 train and is not evidence for this
unpublished candidate.

The next framework milestone can address durable failure isolation and explicit
recovery. Another live comparison requires a fresh frozen operator/accounting
baseline and explicit authorization; the stopped study must not be resumed.
