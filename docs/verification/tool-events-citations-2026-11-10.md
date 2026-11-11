# Safe tool events and citations: implemented and independently reviewed

This is the implementation checkpoint before stable release preparation. See
[Lab 0.9.13](../release-0.9.13.md) for the subsequent release scope and linked
publication evidence. The statements below describe the checkpoint only.

This increment adds opt-in safe tool events, captured evidence and checked citations
across Runtime, Harness and Lab. Parallel calls, MCP clients and sub-agent
orchestration remain separate follow-ups. No release tags, publication, stable
manifest replacement or hosted promotion runs were performed.

## Final private candidate handoff

| SDK | Source commit | Original wheel SHA256 |
| --- | --- | --- |
| Runtime 0.9.20.dev2 | `2c8327b0b418bad5ed4121fce9b42803c404ae7f` | `c535265b8775e976e3eb5f57c0cce63cec29683dd6714812ddcc5259bf878190` |
| Harness 0.9.14.dev2 | `711ae716c522279da836ed5df5b8220d6dad533e` | `3598bd521642d60bd3369fb4c8a94eb4745dce04b4e5a557605e7eefc450b5e6` |
| Harness PostgreSQL 0.4.3.dev2 | same Harness source | `5c7a359b5d816de883462417798abb36249038f0ba1598491d885e952eaa6f1a` |

Core 0.5.0 and Runtime PostgreSQL 0.3.0 retain their original published bytes.
Earlier private snapshots are superseded and retained separately. The final local
five-wheel manifest digest is
`120c6f93366f9540792b7fe657ec3f86030dde023464dbe96d2646aff665ea85`;
its lineage digest is
`a526ab0dbd9c0bccbef4642da470019e23ddcb1fa9a3ae5099e5475fd7e24eee`.
Provenance explicitly says `local-tool-contract-handoff`; it contains real source
and qualification receipts without invented hosted run IDs.

## Independent review and fixes

One fresh whole-branch review covered Runtime, Harness and Lab. It found no
Critical issues and four Important issues, all resolved with failing regression
tests before fixes:

1. Generic tool history bypassed current grants. History views now check
   `retainedRead`; historical model input checks `modelUse` before dispatch.
   Omitted context requires no unused grant. Denied reuse produces a durable
   no-effect receipt, with no provider request or repeated effect.
2. A failing completion event sink could erase known journal completion.
   Completion is classified before fallible completion callbacks, including
   controlled failures and replay.
3. Independently bounded registry components could exceed the combined cap.
   Complete retained documents are now checked atomically, including delivery
   growth. Capacity failure preserves known completion; unrepresentable budgets
   refuse before effects. Failed admission also leaves ambient authority intact.
4. Ordinary CI referenced stale wheel filenames. It now installs actual dev2
   artifacts and pins the final Runtime source. Release workflows were not changed.

The reviewer separately ran 61 Runtime regressions and reproduced the issues on
both protocols where applicable. Live-model semantic entailment, actual hosted
execution and application-specific authorization choices were explicitly outside
that review. There was no second review or implementer-agent delegation.

## Verification

- Runtime full checkpoint: 2,828 passed, two existing skips, at source `51929ed`.
  The final pure admission/context cleanup at `2c8327b` was then covered by 36
  fresh boundary, legacy, surface and installed-consumer checks. Twelve focused
  review regressions cover completion sinks, aggregate limits, both API protocols,
  tiny budgets and ambient authority restoration.
- Harness full checkpoint: 1,525 passed, six existing skips, at source `e885ba2`.
  Its final CI-only source-pin update at `711ae71` passed ten fresh CI tests.
- Lab stable-SDK unit checkpoint: 1,633 passed, 24 intentional candidate-case
  skips. Existing evaluation tools retain their pinned qualification requirements;
  development versions were not added to unrelated approved study trains.
- Lab candidate/blueprint checks: 38 passed. The required feature lane calls
  capability admission directly and cannot skip. Installed Lab dev2 blueprint:
  two passed, with all seven declared copied resources present.
- Harness owned storage/schema/migration checks: 52 passed each on PostgreSQL 16
  and 18. Worker DDL remains denied; readiness does not migrate storage.
- Final original-wheel Runtime and Harness consumers passed on both API protocols.
  Both SDK source distributions were independently rebuilt into wheels, installed
  outside checkouts and passed the same consumer. Strict installed payload audit
  passed for all five original selected SDK wheels.

The focused lane has 12 logical cases × `openai-compatible` / `anthropic`:
24 required cases per database/architecture cell. It covers approved and denied
scalar display, legacy returns, typed results, fabricated IDs, selected inline
content, exact partial reads and index-only refusal, one-effect journal replay,
zero-work receipt adoption, revoked views/implicit history/explicit imports,
metadata-number guard isolation, and unsupported or forged delivery.

Final local ARM64 PostgreSQL 16 and 18 runs each passed **24 cases, zero skips**,
with installed payload audit and cleanup verified. Run IDs:
`76a25d5a496c42fe98bbc911ceb2f9c4` (16),
`c803187dcdf44373bcafba8e82a93c03` (18). Final immutable consumer image:
`sha256:87bf9763a32a825ebb4a5a415c412bf252082add08035f67795b75851f0d57c0`.

The manual hosted workflow specifies AMD64/ARM64 × PostgreSQL 16/18; it has not
been dispatched. These local results do not claim hosted qualification or
live-model answer-quality improvements.

## Running the focused lane

Build a consumer with `scripts/build_consumer.py` from the same verified candidate
manifest, then run:

```sh
python -m lab_runner test --mode tool-evidence --candidate \
  --candidate-manifest PATH --consumer-image sha256:IMAGE --postgres-version 16
```

Repeat with PostgreSQL 18. Hosted curation requires successful exact-source
`Tool contract candidate` runs and matching original qualification artifacts.
The existing stable `Publish SDK` validators remain separate and unchanged.
The complete SDK-only application host is copied with blueprint `tool-evidence`.
