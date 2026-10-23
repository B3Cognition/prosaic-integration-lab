# Released SDK fixes and experimental continuation budgeting — 2026-10-17

Runtime 0.9.7 and Harness 0.9.4 are merged, pushed and publicly released.
Lab memory remains experimental and unreleased. Provider-neutral continuation
budgeting is implemented and offline-qualified under unchanged limits; it has
not been tested in a new live memory comparison.

## Public SDK releases

- [Runtime 0.9.7](https://github.com/B3Cognition/prosaic-runtime/releases/tag/v0.9.7):
  trusted native-input admission to shared budgets, honest captured usage and
  overrun retention, typed tool outcomes and opt-in bounded recovery.
- [Harness 0.9.4](https://github.com/B3Cognition/prosaic-harness/releases/tag/v0.9.4):
  complete tool-call identity validation, bounded correction and terminal failure
  precedence; preserves published lifecycle and original-message retry fixes.

Each exact-source candidate has 24 qualification receipts covering Linux
AMD64/ARM64 and macOS, Python 3.11–3.13, installed wheel gates, dependency floors
and real PostgreSQL 16/18. Runtime database lanes pass41 cases each; Harness
database/store/installed/recovery lanes pass186 each, with no skipped SQL gates.
Local full suites: Runtime1290passed/1source-only installed gate skip (separately
passed installed); Harness872passed/2disposable-database skips covered remotely.
Installed local checks: Runtime70, Harness24 plus workflow/conversation smoke.

Downloaded public wheel/sdist hashes match the qualified receipts. Runtime's
successful candidate/promotion runs are39061836495/39062844433; Harness's are
39063280993/39063830690. Both promotions completed on attempt2: immediate
post-upload version endpoints temporarily returned404; public project listings
and actual file hashes were verified before resuming only the failed jobs.
Neither digest gates nor publication payloads were changed. GitHub releases
contain the same distributions and qualification receipts.

The failed, unpublished Harness0.9.3 candidate exposed stale adapter packaging
version paths. Those fixtures were corrected, the failing packaging/container
checks passed, and a new immutable0.9.4 candidate qualified. The failed tag and
evidence remain preserved. Adapter versions Runtime recorder0.3.0 and Harness
store0.4.0 were not republished; rebuilt artifacts are compatibility witnesses.
Core0.4.1 is unchanged. Release PRs:
[Runtime8](https://github.com/B3Cognition/prosaic-runtime/pull/8),
[Harness8](https://github.com/B3Cognition/prosaic-harness/pull/8).

## Continuation policy and findings

The previous live comparison refused three smaller-model continuations that
exceeded individual quotation slots by27 or59 tokens despite shared headroom.
The new opt-in version2 policy preserves full planning quotations for optional
context selection, but counts the actual final native request and lets one
public Runtime ExecutionBudget reserve input plus maximum output atomically.
The scope spans every Harness attempt. No new SDK change or provider/model
special case was needed. Version1 remains the default.

Synthetic execution reproduces both observed mismatches (1307/1280 and1211/1152)
without increasing caps. Both memory arms admit affordable continuations;
optional recall no longer creates a larger hard slot through quotation rounding.
An exact next-request fit at150already-paid+7530input+512maximum-output=8192
succeeds. A proposal above the remaining allowance still stops before HTTP.
Unknown usage retains its reservation; concurrent work cannot reserve the same
headroom; actual overruns remain recorded and fence later dispatch. Counted
proposals are diagnostic, not dispatch or paid-usage evidence.

Frozen identity binds the policy, counter and quotation provenance. Receipt-only
recovery performs no inference, quotation or retrieval and preserves trace bytes.
Mandatory current evidence remains intact. A rejected full mandatory quotation
still refuses execution, and affordability of one continuation never guarantees
that every later possible trajectory will fit.

Executable Lab candidate: `0.5.1+continuation.1`, source
`1d983508d9f48080fa7be2998e34272749a4ad20`.
[`dependencies/continuation-candidate.json`](../../dependencies/continuation-candidate.json)
pins all five public SDK wheels. Packaged experimental benchmark provenance uses
that manifest; the active release manifest and historic candidate manifests are
unchanged. Lab was not pushed or published by this milestone.

## Qualification and review

- Fresh full Lab suite:1329passed, zero failed/skipped; one existing Starlette
  HTTP-client deprecation warning. Final focused checks35passed.
- Installed final wheel on macOS/ARM64/Python3.12.14:14continuation scenarios,
  24synthetic requests/6tools, both OpenAI-compatible and native Anthropic formats.
- The same final wheel on Linux/ARM64/Python3.12.15: identical14scenarios in a
  network-disabled, read-only, unprivileged container with all capabilities
  dropped. Exact image identity is in the attached data; owned containers removed.
- Both platforms also pass legacy scoped-memory/bounded-recovery10scenarios,
  19synthetic requests/9tools, pure preflight and network-denied receipt replay
  with unchanged saved traces.
- All five SDK installed payloads match verified wheels. Runtime57installed/
  50source files, Harness35/29 and Lab119/115 additionally match immutable source.
  Final wheel and sdist hashes are retained in the data and private archive.
- New regressions were watched failing before implementation. An initial full
  run additionally caught39 stale packaged-provenance failures after SDK adoption;
  provenance was corrected, focused25passed, then the full1329passed.

One fresh independent whole-branch review found no Critical/Important issues.
Deferred minor: derived `requiredTokens` and `availableTokens` accept numerically
equal floats through dictionary equality, also present in version1. Reproduced
read-only; actual hard caps, native counts and output bounds remain strict.
This is a validation limitation, not additional execution allowance.

Review rulings: live tokenizer/provider behavior and memory efficacy remain
outside offline certification; separate frozen live validation is required.
Publication/provenance and final wheel/container gates were independently
verified after reviewer dispatch. Cross-version recovery under changed code
identity is not promised: preserve original qualified environments; in-place
upgrades require separately qualified migration. The costs of getting these
boundaries wrong are overstated efficacy, wrong SDK bytes, transport regressions
or unsupported historic upgrades, respectively.

## Limits, preservation and readiness

No live dispatch occurred. Case caps remain4requests/2tools/8192tokens/600seconds/
512output tokens. Cumulative ceilings stay1475requests/604tools/1976623tokens;
charged usage stays1442/588/1731251, leaving33/16/245372. Allseven historic unknown
reservations remain charged. All34 ledgers and428 prior comparison evidence files
retain their hashes. The new offline archive contains282files plus its manifest.

The budgeting milestone is ready for a fresh held-out comparison with a frozen
protocol that fits the remaining allowance. Memory still has no demonstrated
reliable reasoning benefit; this offline fix removes a known admission confound,
not the smaller model's semantic decision/feedback failures. Keep deterministic
acceptance checks and bounded escalation. Full external Lab DB/auth/billing,
distributed effects and multi-agent handoff are not newly qualified here.

See [structured evidence](data/continuation-budgeting-2026-10-17.json),
[preservation receipt](data/continuation-budget-preservation-2026-10-17.json),
[usage contract](../continuation-budgeting.md) and
[completed plan](../superpowers/plans/2026-10-17-continuation-budgeting.md).
