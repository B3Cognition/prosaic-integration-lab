# Optional SUE review fixes and 360-second rerun — 2026-10-25

The five approved changes were implemented in order and separately verified.
The fresh Qwen comparison measured all 24 cells: 18 workflows completed, five
final workflows exhausted strict validation attempts, and one SUE dialogue
exhausted canonical validation attempts. All six unfinished workflows remain
failed outcomes. There is no new unknown usage, overrun or tool call.

Memory and SUE remain disabled by default. The new cycle policy and review
context are explicit opt-ins. Canonical turn validation, source/provenance
checks, original cases, strict scorer and final schema are unchanged. Existing
v1/v2 workflows remain available. No Runtime/Harness implementation or ordinary
dependency pin changed; the same unpublished Runtime JSON-schema candidate was
explicitly admitted for this experiment. No push, release or publication.

## Implementation and separate verification

1. Pure SUE adapter: `initial_state(..., cycle_guard=False)` preserves legacy
   state/transitions by default. The opt-in policy stops exact repeated cycles
   without new substantive arguments, coverage or resolved issues, returning
   BOUNDED_STOP with canonical turn reason `repeated_cycle_no_progress`.
   Missing dimensions remain missing. Three watched RED failures became 49
   passing engine checks; 75 standalone wheel/source-distribution checks pass.
   Replaying the original case 4 evidence stops at six accepted turns, retaining
   its unestablished dimensions; no new model calls were used for that replay.
2. Lab SUE session: bounded host-supplied purpose, public issue definitions and
   criteria are frozen in the signed request. The context mode and cycle policy
   are frozen in workflow identity; resume uses saved values. Source evidence,
   canonical guidance, identity and tool authority remain separate. Five RED
   tests became five GREEN context checks, then 12 compatibility checks and all
   101 focused SUE checks passed. A compatibility regression for old direct
   requests without optional reviewPolicy was caught and fixed without changing
   assertions. Original engine bytes remain necessary to resume old reviews.
3. New comparison v3: only the model-facing final advice is deduplicated. It
   retains distinct premises, witnesses, questions, coverage, source hashes and
   originating turn references. Raw reports/history/receipts stay intact. Eight
   checks including unchanged v2 behavior passed after the missing projection
   was observed RED.
4. V3 final consistency: incompatible assessment/issue combinations are rejected
   and retried within the existing two-attempt/call/token bounds. Outputs are
   never rewritten. Critic guidance remains distinct from the final response
   contract. Two watched RED integration failures became 21 passing checks;
   rejected receipts, token usage and no-call completed resume are verified.
5. Evaluation separates strict final scores, execution completion, examination
   coverage and unverified entailment. Four RED diagnostics checks became GREEN.
   Independent review found no Critical/Important implementation defect, but
   identified insufficient held-out integration coverage. Three additional
   scripted source cases now run through session/report/final projection and
   original strict scoring, including progress, uncertainty without asserted
   contradiction, and rejection of extra findings. All three pass. These are
   mechanical fixtures, not proof of held-out model reasoning quality.

Fresh complete default Lab suite: **2,033 passed**, zero failures/skips. Fresh
installed source-isolated SUE/v2/v3 suite: **116 passed**, zero skips. Synthetic
installed 360-second matrix: **24/24**, 88 requests/1,320 fixture tokens; 56
constrained SUE calls. Its network-denied replay makes zero additional calls.
Installed constrained SUE acceptance on PostgreSQL 16.15 and 18.6: **six passed
per major**, zero skips, separate runtime roles and verified fixture cleanup.
Consumer is macOS ARM64; native Linux qualification was not rerun here.

All 186 Lab Python payloads match current source. All 218 wheel-member payloads
match the wheel rebuilt from the final source archive. ZIP hashes differ due to
archive metadata; no whole-wheel byte reproducibility claim is made for Lab.

The full legacy Castle suite is not green in this environment: candidate
93 failures/38 errors/2,478 passes versus pre-change 93 failures/38 errors/2,475
passes. All **131 failing/error test IDs are identical**, with no new failures.
This establishes differential behavior for that run, not legacy release
qualification. The exact failing IDs and both complete logs are preserved.

Failed verification setups are preserved too: missing optional legacy test
dependencies, a Lab-installed environment used for SDK-only assertions, and
missing CLI entry points in new disposable environments. Dependencies/entry
points were provisioned in new environments; assertions and skip conditions
were unchanged. The final full and installed results above are separate reruns.

## Same controlled Qwen comparison

Same eight cases/scorer/host keys, rotating three-arm order, one trial per cell,
mlx-community Qwen2.5-Coder-7B-Instruct-4bit, temperature 0.2, max 4,096 output
tokens, thinking disabled and no tools. Cell limits remain 360 seconds,
30 requests/65,536 reported tokens; request timeout 60 seconds; SUE 14 turns,
28 calls/two attempts. Shared limits remain 720 requests, 1,572,864 tokens and
7,200 seconds. New run IDs, stores and allowance; no previous run was resumed.

Declared experimental changes are the five items above. All arms use the same
updated final reviewer. The original source tasks/cases/scorer are byte-identical;
prompt/policy changes are explicitly recorded, not described as unchanged.
The ordinary closed 120-second builder still rejects 360 seconds. Public
WorkflowFactory construction at 120 has identical fingerprints to the new v3
builder; raising that experiment to 360 changes only its max_run_s definition.

| Strategy | Prior strict passes | New strict passes | New workflows completed | Prior tokens | New tokens | New requests |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Direct | 3/8 | 4/8 | 6/8 | 8,442 | 12,420 | 11 |
| Critic/author | 2/8 | 5/8 | 6/8 | 14,851 | 18,523 | 18 |
| SUE | 4/8 | 3/8 | 6/8 | 98,498 | 56,170 | 25 |

New total: **54 requests / 87,113 reported tokens**, fully reconciled across
wire observations, Runtime receipts and the new allowance. Independent offline
audit joins all 54 requests and all 24 cells. Network-denied replay makes zero
additional calls. Seventeen SUE responses match strict generation schemas;
canonical validation accepts 14 and rejects three. No invalid turn is accepted.

SUE still uses 4.52 times direct's reported tokens. Its tokens decrease 43.0%
relative to the prior trial, while its strict passes decrease by one. Direct and
critic improve descriptively. Sampling/cache/local load are uncontrolled and
multiple declared changes were combined; this single trial establishes neither
causality, statistical significance nor general review quality. Timings are
descriptive and do not qualify comparable production latency or billing cost.

## What remains wrong

- Case 4 SUE drops from 64,408 tokens/263.950 seconds to **3,480 tokens/22.483
  seconds**, a 94.6% token reduction. It exits DEFINE as APORIA_UNDEFINED after
  one accepted turn. Its final still says NO_KNOWN_ISSUES despite explicitly
  unspecified failure behavior, so the strict score remains failed. The new
  live trajectory differs; attribute neither its quality nor all cost reduction
  solely to the guard. The original trace separately proves the guard behavior.
- Case 3 now exercises the guard in the live run: eight accepted turns,
  repeated_cycle_no_progress, 26,822 tokens/128.963 seconds and a correct final
  untestable-acceptance finding. Only DEFINE is established; the final pass does
  not certify the dialogue. This cell uses about 47.8% of SUE's new tokens.
- Case 2 SUE exhausts two canonical attempts, including a fabricated seed
  quotation and invalid conflict witnesses; its second witness gives identical
  readings. No final is produced.
- Case 5 direct/critic and case 6 all three arms exhaust final consistency
  attempts. Case 6 uses INSUFFICIENT_CONTEXT but omits its missing_context issue;
  case 5 mixes ISSUES_FOUND with missing_context. Retries retain these failures.
- SUE case 5 still misses the unsupported assumption. Case 8 changes from a
  passing SUE final to a clean verdict that misses the contradiction and cites
  the injected line. The strict assessment/issue/citation checks reject it.

SUE passes cases 1, 3 and 7; its lost pass versus the previous trial is case 8.
No SUE dialogue reaches RESOLVED. Six stop after one accepted turn, one stops
after eight, and one accepts no turn. Passing finals and advisory terminals do
not establish sound natural-language entailment. The result does **not** qualify
the new SUE profile for routine use; keep it disabled. A structured category
review or model-quality comparison is a better next experiment than increasing
the deadline again. Neither validators nor the scorer should be relaxed.

## Preservation and evidence

All nine previous archives/**4,078 files** verify unchanged. The failed original
120-second case 4 entry remains unknown with actual=null and its full maximum
**30 requests/65,536 tokens** retained. Its old total remains **49 requests /
90,345 tokens**. The new known results never release, offset, reconcile or reset
that reservation. The previous failed Qwen runs and all new rejected receipts
are preserved independently.

Private evidence root: `/private/tmp/prosaic-sue-review-fixes-20261025`.
Durable archive: `reports/castle-sue-review-fixes-20261025`. It includes raw
RED/GREEN/full-suite and failed setup logs, source/build proofs, candidate wheels,
frozen operator/plan, raw wire/receipts/checkpoints, allowance, replay/audit,
comparison diagnostics and preservation proofs. Temporary environments and the
expanded pre-change source tree are excluded; commit identities and complete
baseline logs remain. No public dependency adoption or release certification.
