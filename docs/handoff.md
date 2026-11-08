# Codex handoff

## Accounting request metadata and Lab0.9.10 — 2026-11-08

The maintainer authorized Runtime accounting labels and a Lab blueprint, tests,
merge/release and notes. Develop against an explicitly labeled candidate; advance
active pins/freezes only after actual Runtime0.9.17 publication/public-byte proof.
Core0.5.0/Harness0.9.12 and recorder0.3.0/store0.4.1 keep released bytes. Previous
active profiles/manifests/freezes are preserved as pre-accounting-metadata; all
five earlier blueprint resources/corpus/prompts/scoring remain unchanged.
Trusted benchmark labels never replace actual run/tenant/payer authority. Saved
Harness labels win on resume; same-call relabeling conflicts. Labeled contexts
need >=0.9.17 readers; no DDL or adapter republish. No live calls.
Follow the [guide](accounting-request-metadata.md),
[release gates](release-0.9.10.md) and
[ledger](verification/accounting-request-metadata-2026-11-08.md).
Require all ten final-head hosted jobs, exact merge/tree and original qualified
archives, public consumers and all post-merge CI before marking complete.


## Workflow enforcement V2 and Lab0.9.9 — 2026-11-07

The maintainer authorized workflow enforcement tags with accepted earlier outputs,
implementation/testing/merge/release and a new Lab blueprint/release notes.
Harness0.9.12 PR16 merged816436b and is published/verified; retain released
Runtime0.9.16/Core0.5.0 and both adapters. Active manifests now adopt its exact
public wheel SHAfb07797c3e42ab2e7e8f0a727b7bd25229e9b223cf15309716f10ff9d1f1147b. Existing
V1 resources and all historical manifests/profile/freezes stay unchanged; prior
active records are preserved as pre-workflow-enforcement. No live calls.
Follow the [release guide](release-0.9.9.md), [feature map](feature-blueprints.md) and [current ledger](verification/workflow-enforcement-2026-11-07.md).
Require the complete four native ordinary cells, four rule/feature cells and
both reasoning jobs, final review, exact merge tree, original archives, public
wheel/rebuilt-source consumers and all post-merge checks. Older checkpoints
below retain their historical limits.


## Latest SDK blueprints and Lab 0.9.8 — 2026-11-07

The maintainer authorized a new Lab release adopting Runtime 0.9.16 and Harness
0.9.11, with a copyable blueprint, installed acceptance and guide per added
capability. Core 0.5.0/recorder 0.3.0/store 0.4.1 retain their public bytes.
Previous active records are archived as pre-cerebro; benchmark inputs are unchanged.
Follow the [feature map](feature-blueprints.md) and
[qualification ledger](verification/cerebro-sdk-blueprints-2026-11-07.md). Full source,
installed consumers, final native matrix, review, merge equality and original
archive/public-consumer proof remain required before publication. No live calls
or upstream SDK publication. Older checkpoints retain their historical scope.


## Harness 0.9.10 SDK adoption — 2026-11-06

The maintainer authorized Lab 0.9.7 with Harness 0.9.10, Runtime 0.9.14 and
Core 0.5.0, retaining recorder 0.3.0/store 0.4.1 public bytes. Both active
manifests and current provenance/freezes advance; previous records are archived
verbatim. No session migration or live calls. Follow the
[release plan](superpowers/plans/2026-11-06-harness0910-lab-release.md),
[release guide](release-0.9.7.md) and
[verification ledger](verification/harness0910-sdk-release-2026-11-06.md).
Require all ten final-head hosted jobs, equal qualified/merged trees and original
CI archive/public-consumer proof. Earlier checkpoints below retain their scope.

## Guarded ecosystem release authorized — 2026-11-06

The maintainer explicitly authorized updating, merging and releasing Runtime,
Harness and Lab after the independent Lab 0.9.5 release completed. That release
is now published and verified. This isolated follow-up combines its main tree
with the #45 blueprint and #46 guarded Harness companion. Preserve both sets of
changes and all historical manifests, prompts and verification evidence.

Runtime 0.9.14 and Harness 0.9.9 are published and publicly verified. Both active
Lab manifests now select their exact public wheel bytes with Core 0.5.0 and the
unchanged recorder 0.3.0/store 0.4.1. Current provenance/freezes have advanced;
all five prior snapshots remain byte-identical. Final Lab hosted qualification
must consume these published bytes; local candidates are not release evidence.
No new live inference is authorized.
Follow the [0.9.6 release guide](release-0.9.6.md) and
[current ledger](verification/guarded-sdk-release-2026-11-06.md). The isolated
merge with Lab 0.9.5 preserves both the author blueprint and guarded companion;
its pre-guarded snapshots must never be overwritten. Require all ten final-head
hosted jobs, equal qualified/merged trees and original CI archive/public-consumer
proof before marking Lab complete.

## Lab 0.9.5 merge and release authorized — 2026-11-06

The maintainer explicitly requested merging, pushing and releasing the tested SDK
adoption. This supersedes the earlier source-only scope below. Prepare 0.9.5 from
main `3cf2d6416f822acde27bf721982571deaa38fe6b`, preserve the exact five public
SDK pins and historical snapshots, and follow the
[release plan](superpowers/plans/2026-11-06-core050-lab-release.md) and
[release guide](release-0.9.5.md). Require four native Linux acceptance cells and
both installed-reasoning jobs on the final source, expected-head merge with equal
trees, original CI archives and fresh anonymous-download/installed-consumer proof.
No new live inference or upstream SDK publication is needed.

## Core 0.5.0 SDK adoption — 2026-11-05

The current request updates both active manifests to Core 0.5.0, Runtime 0.9.13,
Harness 0.9.8, recorder 0.3.0 and store 0.4.1. It supersedes prior requests to
keep those active pins unchanged. Historical manifests, benchmark profiles and
freeze records are archived verbatim; corpus, prompts and scoring are unchanged.
Read the [adoption ledger](verification/core050-sdk-adoption-2026-11-05.md) for
current verification results. Work is isolated from the original experiment
checkout; no Lab version bump, commit, push or publication was requested.

## Guarded Harness companion — 2026-11-05

The maintainer authorized implementing the remaining Harness and Lab gaps.
This follow-up branch starts at PR #45 `44539fd`. The guarded lane now uses
released Core 0.5.0, fixed Runtime #16 `498ffc7`, and local Harness companion
`5b3f0f2` (branch `codex/harness-rule-admission`). It owns policy and composed
inspection rules, registers guards at every phase, seals explicit guard project
roots, and persists bounded rule receipts and ruleViolation failures.

The copyable `blueprint/harness.py` and both-wire acceptance cover before-tool
repair, composed after-tool failure, retry exhaustion and file-store recovery.
Independent value-source regressions now pass through Harness; three strict
expected failures still document the upstream fee grammar limits. A separate
required PostgreSQL lane covers receipt recovery with installed SDKs.

Both candidate wheels were rebuilt twice with identical recorded hashes and
both five-wheel train audits pass. The Harness source suite passed 1,035 with
real PostgreSQL 18; its saved compatibility regressions pass all four cases.
Final installed/default/PG qualification is recorded in
[the companion ledger](verification/guarded-harness-2026-11-05.md).

No release or author-branch modification is included. Before remote CI can
build this lane, push the exact Harness companion commit. For local rebuilding,
the builder accepts an explicit `--local-repository` checkout and still archives
only that commit and verifies its hash. Ordinary/reasoning manifests are unchanged.
Earlier checkpoints below describe their historical candidates.

## Rule-admission blueprint, draft only — 2026-11-05

The maintainer asked for an adoption example of Prosaic rule admission.
Branch `feat/rule-admission-blueprint` is based on main `3cf2d64`. Its draft
PR waits for prosaic-runtime#16. No version bump, no `release-x.md`, and the ordinary and
reasoning manifests are unchanged.

- Candidates: Core `9d5a02f` (main, PR #4) and Runtime `65ba15d` (PR #16 head).
  Both are rebuilt from `git archive` with `setuptools==80.9.0`, no isolation
  and `SOURCE_DATE_EPOCH` set to the commit time. Two local builds produced
  identical bytes. Neither commit has a `Publish SDK` run; the draft PR asks the
  maintainer to dispatch one so action-built wheels can replace the local ones.
- Blueprint: `lab_runner/rule_admission/blueprint`. It has no Harness workflow:
  Harness 0.9.7 lacks `ruleViolation` in `_FAILURES` (it raises after provider
  spend), and its conversation path drops `required_guards`, composed rules and
  guards.
- Review: an adversarial pass found 9 defects, each pinned by a test that
  failed first; all are fixed. The worst was a policy bypass: `"days": 28.0`
  skipped the loan-period guard. Coverage now takes its verdict from real
  admission.
- Re-pin 1: Runtime `4082e72` to `65ba15d` (review changes). No blueprint test
  broke. One new variant pins the cross-file rule change: different settings at
  one stage are now refused. Generic guard sources changed without a version
  bump, so the rules fingerprint did not move; reported for #16's thread.
- PR #45 review: 7 inline comments and 2 general points, all addressed
  test-first. The floor now covers the custom guard; the id rule's wording
  matches the guard; the companion moved to `companions/` (never distributed as
  an agent); `fix` where the guard cannot repair is refused by the host; the
  missed fee formats are strict expected failures; huge periods are repaired;
  the blueprint checks the SDKs on import.
- PR #45 re-review: the floor needs a guard bound only once, so prose could drop
  the loan check's `before_tool` tag (or move it to `after_tool`) and a 300-day
  loan was placed before the turn failed. The host now declares
  `REQUIRED_STAGES` and `compose` refuses a bound guard missing one (coverage:
  `hostPolicy`). `place_loan` also refuses over-policy periods itself. Smaller
  points fixed: trailing `€` is read by Runtime (docs corrected), duplicate
  README header, frontmatter behind a BOM or blank lines. The lane has 123
  tests.
- Verification: see the [ledger](verification/rule-admission-2026-11-05.md).
  CI (`rule-admission.yml`) rebuilds the candidates byte-identically on Linux
  AMD64 and ARM64. It is not a required check until the re-pin to releases.
- Next: after Core releases `parse_rules` and #16 merges and releases, follow
  the re-pin steps in [the lane guide](rule-admission.md#re-pin-after-release).

## Lab 0.9.4 merge and release authorized — 2026-11-04

The maintainer explicitly requested keeping the tested Qwen and Gemma prompts,
getting CI green, fixing failures, merging and releasing the next Lab version.
This supersedes the experiments' earlier no-publication scope. Target 0.9.4
from current main `0220109` (tree identical to 0.9.3 source `719fdb1`). Keep all
selected prompt bytes and both SDK manifests unchanged; no new model calls or
SDK release are needed. Follow the
[release plan](superpowers/plans/2026-11-04-reasoning-model-prompts-release.md)
and [release guide](release-0.9.4.md): six final-source CI jobs, fresh review,
expected-head merge, equal qualified/merge trees, original CI archives and
separate anonymous-download/fresh-consumer postpublication proof. Earlier
checkpoints below retain their historical experimental state and limits.

## Separate Gemma prompt comparison completed — 2026-11-04

Keep all seven shared compact Qwen agents unchanged. The explicit new
`subagents/gemma-medium.md` removes the CRT procedure while retaining the full
tested JSON contract, including the no-fences line. Its 69-word body renders to
111 tokens for the original CRT task versus shared C3's 192. The default Gemma
workflow explicitly selects this file; Qwen workflows must select their Qwen
profile and shared xhigh agent. Runtime profiles and the Lab multi-effort live
command do not automatically substitute prompts.

The first positive-only attempt was too aggressive: all three completed answers
were fenced. It stopped safely after 16 known responses, cleanup verified,
leaving 20 unused slots and no unknown reservation. The final revision restored
the explicit no-fences line and completed a fresh 36-call paired comparison.
Gemma usable correct JSON improved from 9/18 to 12/18; all three fenced baseline
answers recovered. All twelve completed candidate responses were correct strict
JSON. Both arms had six caps (knapsack and digit counting), below historical
C3's thirteen but not a completion gain over fresh 0.9.3. Arithmetic correct
returns remained 12/18 for both; token costs were task-dependent and censored.

All 36 native-control/activation/generation-input checks passed; owned cleanup,
all prior hashes and seven unchanged Qwen agents verified. Total follow-up
inference was 52 requests, including the stopped prefix; no retries or Qwen
inference occurred. Full source tests passed 2,077; reasoning tests passed 31;
both five-wheel SDK audits and private builds passed. Python payloads, SDK pins
and version 0.9.3 remain unchanged. The
[Gemma qualification](verification/reasoning-gemma-minimal-2026-11-04.md) records
both attempts and limits. This remains local adaptive regression development;
no commit, PR, push or release was requested. Historical checkpoints below
describe their own candidates and point-in-time state.

## Compact prompt comparison completed — 2026-11-04

The seven unreleased agent bodies are shortened from 169 to 95 words. They keep
the constructive CRT formula, inverse condition and positive-zero handling,
plus the exact first-`{`/last-`}` JSON boundary rule. Generic check/correct loops
and duplicate verification instructions are removed. Original-CRT rendered
input shrank 26.8% for Qwen and 28.6% for Gemma; shorter input did not reliably
reduce generated reasoning or caps.

The fresh 72-request comparison completed with all native-control, rendered
activation and generation prompt-count checks passing, cleanup verified, no
retries, no transport failures and zero unknown reservations. Qwen xhigh usable
correct JSON improved from 9/18 to 15/18: CRT and knapsack were each correct in
3/3 compact trials; both prompts capped on digit counting in 3/3. Gemma medium
thinking-on regressed from 8/18 to 5/18 usable correct JSON, with caps rising
from seven to thirteen (historical longer candidate: nine caps). All five
completed compact Gemma responses were correct strict JSON, but only one of
three fenced baseline pairs recovered; the other two capped. The Gemma
cap-reduction target failed. Do not present this as a Gemma reliability fix.

The full source suite passed 2,077 tests; the reasoning lane passed 31. Both
five-wheel SDK audits and the private wheel/sdist build passed. SDK pins,
Python payloads and version 0.9.3 remain unchanged. This is local adaptive prompt
development on reused questions, not held-out qualification or a new release.
See the [compact qualification](verification/reasoning-prompt-compaction-2026-11-04.md).
Preserve prior failed/unknown reservations and historical C2 evidence. No push,
merge, tag or publication was requested by this experiment. Older checkpoints
below describe their own longer candidates and point-in-time state.

## Gemma prompt comparison completed — 2026-11-04

The restored Gemma endpoint completed all 36 remaining calls using the frozen
candidate and existing shared allowance. Correct fenced answers fell from two
to zero, and both affected pairs returned correct bare JSON with the candidate.
Among normally completed responses, strict JSON improved from 10/12 to 9/9.
However, capped outputs rose from six to nine, reducing usable correct JSON
from 10/18 to 9/18. The candidate improves the observed wrapping behavior but
regresses overall Gemma reliability at the fixed 4,096-token limit; do not
describe it as a general Gemma reliability fix.

The [qualification ledger](verification/reasoning-answer-validation-2026-11-03.md)
records the complete 72-response Qwen/Gemma study. All native-control and prompt
count checks passed, cleanup was verified, and the current allowance is fully
consumed with zero unknowns. Earlier unknown reservations remain unchanged.
The previous Qwen-only report is preserved separately. Prompts, SDK pins and
published artifacts are unchanged by this continuation; the candidate remains
local and unreleased.

## Unreleased reasoning answer validation — 2026-11-03

The maintainer requested improving the blueprints for Qwen's CRT failure and
Gemma's JSON fences without restoring the removed reasoning prohibition, then
repeating the comparison. The seven source agents now require condition checks,
a constructive Chinese Remainder Theorem procedure with inverse/remainder
verification, and explicit JSON boundaries. Generic checking alone failed the
Qwen CRT target in two trials; the constructive candidate passed all three
paired target trials. The completed 36-call Qwen comparison improved correct
results from 9/18 to 12/18, entirely from CRT; the other five questions remained
9/15 for both prompts. Gemma's 36-call new stage awaits endpoint availability;
its TCP port and model-list API remain unreachable. Do not claim its JSON
regression has been verified fixed. The existing unused allowance permits that
authorized stage once the endpoint is restored, without retrying the prior timeout.
Effort metadata, SDK pins, Python execution and released artifacts are unchanged.
The [qualification ledger](verification/reasoning-answer-validation-2026-11-03.md)
records offline checks and the bounded paired study. This is an unreleased
source candidate; this follow-up does not authorize publication. Preserve prior
studies and consumed/unknown allowances, and keep model quality, strict output
format and native controls as separate measurements.

## Authorized Lab 0.9.3 prompt cleanup and release — 2026-11-03

The maintainer explicitly requested removing the ambiguous reasoning prohibition
from all blueprints, running tests and releasing a new Lab version. Follow the
[0.9.3 plan](superpowers/plans/2026-11-03-reasoning-prompt-cleanup-release.md).
Remove only the phrase from the seven effort-agent bodies. Preserve strict JSON,
native mappings, both SDK manifests and previous evidence/releases. The preceding
12-call prompt comparison found no arithmetic accuracy improvement from removing
the phrase. No additional inference or SDK publication is needed. Qualify the
exact versioned source in both workflows, merge on green CI, publish original CI
archives and verify fresh public consumers without further confirmation.

## Authorized Lab 0.9.2 and four-PR closure — 2026-11-03

The maintainer explicitly authorized getting CI green, fixing failures, merging
Lab42/Core3/Runtime15/Harness10 and releasing a new Integration Lab version.
Follow the [0.9.2 release plan](superpowers/plans/2026-11-03-reasoning-lab-release.md).
This authorization supersedes the earlier no-publication scope below. Both SDK
manifests and prior release evidence remain unchanged; no live inference or new
SDK release is required. Publish original qualified CI archives and verify their
public downloads and installed consumers before claiming completion.

## Reasoning-effort integration — 2026-11-03

The maintainer requested adding the reasoning integration and blueprints and
reviewing documentation across the Prosaic packages. Use the separate
[reasoning lane](reasoning-effort.md), installed Runtime 0.9.12 and
`dependencies/releases-reasoning.json`. The ordinary manifest retains its
original pins. Fixtures and opt-in live runs have distinct evidence contracts;
this update does not authorize inference or a new Lab/SDK publication.
Historical ledgers and dirty sibling checkouts are preserved.

## Authorized Lab 0.9.1 release — 2026-11-02

The maintainer explicitly requested checking all four PR #41 cells, fixing any
failures, merging and publishing a new version once green. All four implementation
head cells passed at `f0398df87e0490ca96f51745da2305a6eccfc158` in run41343271503.
Prepare 0.9.1 metadata/notes and qualify its final source separately before merge.
Follow the [release plan](superpowers/plans/2026-11-02-observatory-monitor-release.md).
Publish original CI bytes with safe receipts and provenance, verify anonymous
downloads and isolated consumers, and preserve all earlier release artifacts.
This authorization supersedes the earlier unreleased-only scope below; no further
merge/release confirmation is required. No new inference is needed.

## Authenticated Observatory monitoring — 2026-11-01

The maintainer confirmed automatic monitoring of all their Integration Lab runs.
The hosted page now defaults to idle monitoring, discovers owned captured
Chat/API and standalone workflow runs, keeps watching after completion, and
requires explicit selection of demos/replay. Safari restores the exact verified
Lab identity; provider keys are clearly distinguished. Capture remains optional,
process-local and bounded; workflow raw text is withheld and missing callback
timing is explicit. See the [plan](superpowers/plans/2026-11-01-observatory-monitor.md)
and [verification ledger](verification/observatory-monitor-2026-11-01.md).
One external real-model API request was automatically observed in Safari:
533 input / 111 output / 644 provider-reported tokens in both views. Keep the
unqualified accounting marker, immutable published artifacts and SDK pins.
The source-only preview is retained for the maintainer; this follow-up is not
merged or released.

Final regressions: 2,077 Python + 32 Node passed. Owned PostgreSQL16 observability
acceptance: 26 passed with cleanup verified; focused review has no blockers.

## Real-model usage compatibility fix — 2026-11-01

The maintainer requested actual token counts in both Observatory views after
the released 0.9.0 real-model preview showed unknown usage. On
`codex/observatory-token-usage`, the local gateway translates only the exact
empty oMLX prefill heartbeat into a transport comment. Its fake model name had
caused correct recorder quarantine of otherwise present counts. Live verification
now shows 533 input / 98 output / 631 total provider-reported tokens in both views, with
the existing unqualified marker; accounting qualification is unchanged. See the
[verification ledger](verification/observatory-token-usage-2026-11-01.md).
All 2,072 Python tests and 25 frontend tests passed, along with a focused review.
Keep published 0.9.0 artifacts/tags, older previews, SDK pins and model-server
settings unchanged. This fix has not been released.

## Authorized Lab 0.9.0 release — 2026-11-01

The maintainer now explicitly authorizes the version bump, release notes, PR,
four-cell CI, fixes, merge and release once green. This supersedes the earlier
no-merge/release scope below. Version 0.9.0 includes actual generation, streaming
defaults, exact legacy identity retention and launcher reconnection, with the
unchanged released SDK train. Follow the
[release plan](superpowers/plans/2026-11-01-observatory-streaming-release.md).
Require the exact versioned head's four CI cells and publish its original CI
artifacts/provenance; preserve earlier releases and unrelated worktree changes.

## Streaming defaults and usable launcher connection — 2026-10-31

The maintainer additionally authorized enabling streaming throughout Lab/chat,
fixing the nonworking Start button, testing, committing and pushing this whole
work package. The earlier screenshot showed a401 before dispatch; the old real
preview also had a spent one-call allowance. New defaults preserve retained
buffered identities and explicit opt-out. Launcher sessions survive reload;
invalid manual credentials cannot appear Connected. A fresh synthetic preview
is retained for repeated review. See the [follow-up ledger](verification/observatory-streaming-defaults-2026-10-31.md).
No merge/release or SDK changes are included. Preserve original0.8.0 artifacts
and the unrelated dirty original checkout.

## Unreleased Observatory generation — 2026-10-31

The maintainer authorized research and implementation of visible generation in
both Observatory views. Branch `codex/observatory-token-stream` starts at current
main `4787265953bbda9a9e7ed63b500d152b8bcf486b` after the published 0.8.0 release.
It consumes public Runtime/Harness callbacks, adds bounded owner-only provisional
output and event-driven animation, and preserves SDK pins and published bytes.
See the [generation ledger](verification/observatory-generation-2026-10-31.md)
for tests, independent review, actual local-model observations and preview use.
This feature is not merged or released; require the normal exact-head CI gate
before integration. Preserve the original dirty Lab checkout and older evidence.

## Lab 0.7.0 published; verification documentation — 2026-10-25

Lab 0.7.0 is published at qualified source
`9a7542c8b736939bf4d22ee2cd3164760eb07449`; PR #35 merged as `4fa6e46` with
the same tree. All four versioned CI cells passed, original archives were
published with checksums/provenance, and anonymous downloads matched. The
[release ledger](verification/release-0.7.0-2026-10-25.md) records both clean
public consumers with Runtime 0.9.8: 64 fixture/browser checks each, installed
visual docs/playback, explicit live confirmation and actual synthetic Runtime
CLI execution, duplicate protection, cancellation, retained allowance and
blocked admission across restart. Cleanup passed; no real vendor inference or
new benchmark was performed.

The maintainer authorized documenting these results, committing the docs and
preparing a PR. This follow-up changes documentation only; preserve published
archives, package versions, SDK pins and historical evidence. Earlier entries
below retain their original authorization/checkpoint context.

## Explorer PR #34 CI review and merge gate — 2026-10-25

The maintainer authorized fixing PR #34 and merging once all required checks
pass. Independent review found no new Explorer blocker. CI exposed Playwright's
automatic GitHub PR diff capture fetching the base with depth one, making the
browser lane's original checkout shallow. Disable optional Git metadata capture
and retain an early full-history gate; candidate-only fetch and branch/detached
fixtures preserve depth-one rejection and exact released-baseline bytes. See the
[review/CI ledger](verification/explorer-pr-2026-10-25.md). Merge only the exact
head passing all four Linux/database cells. No release or real inference is
included in this authorization.

## Explorer review and PR preparation — 2026-10-25

The maintainer authorized reviewing Explorer, fixing findings, completing checks
and preparing an integration-lab PR. This supersedes the earlier local-only scope
for these branch changes; it does not authorize merging or a release. Explorer
includes visual documentation, eight deterministic scenarios, explicitly bounded
live controls, System/Light/Dark appearance and viewport-stable chapter navigation.
The [review ledger](verification/explorer-pr-2026-10-25.md) records final checks
and two corrected navigation/receipt-selection findings. SDK pins and released
artifacts remain unchanged; no new live inference is included. Require the exact
PR head's four Linux AMD64/ARM64 × PostgreSQL 16/18 cells before a later merge.

## Guided ecosystem onboarding — 2026-10-25

The maintainer approved a newcomer-oriented README, credential-free first run,
fallback walkthrough, optional service/browser demo, real-model setup, benchmark
and developer integration map. The [quickstart](quickstart.md) reuses released
SDKs; `examples/first_workflow.py` only parses, admits and prepares, never executes.
Unified browser pooling remains separate. The old README's operator/history
material is retained in `reference-guide.md`, with original section anchors
linked from the new README. [Local verification](verification/guided-onboarding-2026-10-25.md)
passed 1,923 source tests, fresh setup, installed consumers and both service demos
with cleanup verified; independent review is clean after fixing setup. Keep this
follow-up local; no new release or live benchmark is authorized by onboarding work.

Lab 0.6.2 is published at qualified source
`b5773c33ba7305b92667c9874e4a8526c4394dd9`, with PR33 merged as 46a2d80.
The [release ledger](verification/release-0.6.2-2026-10-25.md) records exact
artifacts and both clean consumers' 54 checks. Preserve immutable release bytes,
private receipts and all earlier benchmark/model evidence.

## Lab 0.6.2 release preparation — 2026-10-25

The maintainer authorized releasing 0.6.2 with configurable local timeout and
post-publication clean-install checks using Runtime 0.9.8. PR #32 merged as
`eff161943c5e816468eef504bf9c4fc055a0fb11` after four green CI cells and review.
The [release notes](release-0.6.2.md) describe the patch. Qualify the versioned
source in all four cells, retain original CI artifacts, then publish and verify
downloaded bytes. Clean consumers must exercise default180s/explicit240s and
the installed evaluation lanes without live inference. Preserve SDK pins,
historical releases and private benchmark evidence.

## Configurable local benchmark deadline — 2026-10-25

The maintainer authorized configurable unified benchmark local timeouts, tests,
documentation, commit and PR preparation. `--local-timeout` now accepts finite
1–300s values with a 180s default, retained in command arguments and receipts.
Native60s/pool300s, all grants/budgets, tasks and inputs remain unchanged. This
feature is not in the immutable 0.6.1 archives; no patch release is published here.

The [240s study ledger](verification/unified-cli-lab061-local240-2026-10-25.md)
records 27/27 successes using released Lab 0.6.1 / Runtime 0.9.8 and a private
deadline-only driver. Audits paired all 27 input/Markdown hashes, regraded 54
current/prior outputs and reconciled 45 known mixed units. Cleanup restored
native marks, preserved the local bucket's original unknown state and stopped
only the owned server. That absent capacity record is separate from the zero
unknown dispatch reservations. Preserve all private and historical evidence.

## Lab 0.6.1 released and verified — 2026-10-25

[PR #30](https://github.com/B3Cognition/prosaic-integration-lab/pull/30) merged as
`4b0258f306b8fde91ef22aaf347d7113a1ed630c` after review and four green CI cells.
The [0.6.1 release](release-0.6.1.md) publishes the original qualified wheel and
source archive from run `40133039899`. Tag `v0.6.1` selects qualified source
`73a071480f4399ddea52839f6836ccaa742e9a03`, whose tree matches the merge.

The [verification ledger](verification/release-0.6.1-2026-10-25.md) records exact
artifact hashes, 1,899 source tests per CI cell, 1,336 real-stack checks and
post-publication clean installs. Public wheel and rebuilt-source consumers each
passed all four standalone CLI lanes (51 checks each) using Runtime 0.9.8,
without repository `scripts`. Quota fallback, persisted cooldowns, no partial
replay, import ownership, installed payloads and cleanup passed; zero live calls.

This documentation follow-up marks publication after the immutable source
snapshot's pre-release changelog. Keep the released archives, tag, SDK pins,
freezes, 0.6.0 artifacts and historical benchmark evidence unchanged.

## Lab 0.6.0 release preparation — 2026-10-24

The maintainer authorized releasing 0.6.0 with unified pools and the released
Runtime benchmark docs. The [release notes](release-0.6.0.md) summarize the
release. SDK pins, benchmark code/inputs/deadlines and historical evidence
remain unchanged. Build and review the final source, require all four native
Linux/PostgreSQL CI cells, then retain the original CI wheel/sdist and attach
checksums plus exact-source verification. Verify downloaded public assets
against those same bytes; do not substitute a later local rebuild.

## Released Runtime live measurements — 2026-10-24

The separately authorized [0.9.8 live studies](verification/unified-cli-released-2026-10-24.md)
completed 27/27 assignments twice, using the same tasks/inputs and native60s,
local180s, pool300s deadlines. The latest Claude/Codex/local medians were
11.37s/23.07s/60.69s; each model passed nine assignments per study. Private
paired audits regraded all saved outputs and verified hashes, admissions and
cleanup. Each run retained 45/243 known mixed dispatch units, zero unknowns.
Each verified 27 controlled cooldown skips and zero provider-triggered fallback;
no quota exhaustion was induced. Preserve original candidate/release reports.

Adoption [PR27](https://github.com/B3Cognition/prosaic-integration-lab/pull/27)
merged as `8194f6a0f6e64c6186c8aa129bc759e9e3ef3008` after all four exact-head
CI cells passed, including 36 real-stack lanes with cleanup verified. This
documentation follow-up does not change SDK pins, execution or benchmark code.

## Runtime 0.9.8 public adoption — 2026-10-24

Runtime [v0.9.8](https://github.com/B3Cognition/prosaic-runtime/releases/tag/v0.9.8)
is public. Adopt its verified PyPI wheel and preserve the other four SDK pins.
The [qualification ledger](verification/runtime-unified-release-2026-10-24.md)
binds source `a9433a68f60eeecf1946a398267f749c7ff89d8e`, public wheel SHA-256
`d9d416baf9a7f4b87328532d41b281a2f6dbc9bafc744f973661a5cf6015a540`
and active manifest `36eec99280acb8688d2496f704f4445b59c3ff269fc506a83d6e7fe83bc92698`.
Require the exact-head four-cell real-stack CI matrix before merging adoption;
the public path now includes installed native/unified acceptance.

Old public SDK and freeze snapshots retain their original bytes and bindings.
The active memory freeze explicitly records the new SDK qualification lineage
and binds the archived profile too. Benchmark inputs, limits, allowances,
historical measurements and unknown reservations are unchanged. No live model
call or memory efficacy claim is authorized by this infrastructure qualification.

## PR22 Linux regression repair — 2026-10-20

The first four Linux CI cells passed mandatory actual confinement, then each
failed four direct child-witness regressions. The [observer repair](verification/sandbox-ci-observer-2026-10-20.md)
addresses reproduced GNU ps truncation, adds three real-process regressions
and safe count diagnostics, preserving every confinement/early-stop gate.
58focused tests pass locally; full regressions/adoption and new exact-head CI
are still required. Do not merge or publish until the four cells qualify.

## Lab 0.6.0 version and authorized push — 2026-10-20

Prepare the reviewed codex/sandboxed-tools branch as a PR against main. The
additive consumer blueprints warrant Lab0.6.0; Core/Runtime/Harness/adapter pins
remain unchanged. Requalify the versioned wheel/sdist and exact source, then
push. The four Linux/platform CI cells remain required before merging/releasing.
Memory/correction and all live allowances/charges remain unchanged. No package
publication or live inference is included in this authorization.
The fresh [0.6.0 qualification](verification/sandbox-version-0.6.0-2026-10-20.md)
passes1824source tests, clean wheel/rebuilt-sdist consumers and142payload checks.

## PR21 merged; sandboxed CLI consumer milestone — 2026-10-20

PR21 merged at5a966ae after all four exact-head CI lanes passed. The experimental
[sandboxed CLI blueprint](sandboxed-tools.md) adds conservative admission,
whole-invocation host permission, actual OS canaries and receipt-only inspection
using public Runtime0.9.7. Hard CPU/memory/process-count/detached-cleanup
requirements refuse admission. Timeout/output failures preserve Runtime's
toolEffectUncertain stop; no precise CLI subtype is invented. See
[offline proof](verification/sandboxed-tools-2026-10-20.md). The newer authorization
above supersedes this checkpoint's local-only handoff. Linux operational enforcement is
a required later platform gate. No live calls, SDK changes, allowance changes
or release; memory/correction remain experimental. Older checkpoints retain
their original state.

## PR20 merged; trajectory evaluation milestone — 2026-10-19

PR20 merged at5bd896a after its exact head passed all four CI lanes:1729source
tests and334real-stack checks per cell, public wheel/sdist adoption and demos.
The next experimental [trajectory blueprint](trajectory-evaluation.md) composes
public SDK observations and independent host assessment, with a second-domain
parcel example. Fixed trajectory.2 passes1769source/40focused tests,12installed
both-wire lanes/replays,139payload matches and clean wheel/rebuilt-sdist adoption.
One fresh review found no defects;40focused tests/130malformed probes/12replays
passed independently. Scope rulings are in the qualification. Keep
codex/trajectory-evaluation local for later PR/platform CI;
no live requests, allowance changes or SDK changes. Memory/correction remain
experimental; preserve all nine unknown reservations. Earlier checkpoints below
retain their original state.

## PR19 merged; tool approval qualified offline — 2026-10-18

PR19 merged at216941a after rechecking its exact reviewed head and four green
CI lanes. New experimental [tool approval blueprint](tool-approval.md) binds
exact actions to trusted host decisions and consumes consent durably once.
It uses public Runtime APIs; it neither authenticates actor strings nor records
effect completion. [Offline proof](verification/tool-approval-2026-10-18.md):
Finalapproval.2:1729source/51focused tests;24installed both-wire scenarios,
25network-denied recoveries and a subprocess-loss check.137payloads and clean
public wheel/rebuilt-sdist adoption pass. One fresh review's Important replay
defect fixed with watched regressions, including immutable audit identities;
zero deferred minors. Six scope rulings are explicit in the qualification. Memory/correction
stay experimental, limits and nine unknown reservations unchanged, no live run
or SDK change. Keep new branch local pending review and later PR/CI.

## PR18 merged; durable failure isolation qualified offline — 2026-10-18

PR18 was marked ready and merged at `1c52747` after all four exact-head required
CI lanes passed. The next [consumer blueprint](failure-isolation.md) adds local
durable admission, isolated uncertainty, revoked journal writers and explicit
receipt-only recovery. It creates no allowance and makes no retry decisions.
Memory/correction remain experimental; no live run or SDK change is authorized.
[Qualification](verification/failure-isolation-2026-10-18.md): final
Lab0.5.1+isolation.2,1678source tests,25focused tests, four both-wire installed
lanes/16synthetic requests/four network-denied recoveries/three process-loss
boundaries/six queued-overrun gates. One Important review finding fixed with
six RED→GREEN regressions; zero minors/rulings.135installed payloads match;
clean public wheel/rebuilt-sdist checks pass. Limits,39canonical ledgers and
nine unknown reservations unchanged. Keep the local branch/worktree for a
review PR and CI; no new milestone push, merge, release or live run performed.

## PR18 CI repair on the public SDK train — 2026-10-18

[Qualification](verification/pr18-ci-2026-10-18.md): active manifest advances to
already published Runtime0.9.7/Harness0.9.4. Benchmark identity admits only the
exact public or preserved private candidate profile. Packaging qualification
derives the current source version; all required platform/database lanes remain.
Memory/correction stay experimental, with no live calls or allowance changes.
Unpublished response diagnostics retain separate candidate-only qualification.
Keep the PR draft until its exact head is green and reviewed. No SDK release is
required merely to merge public-compatible consumer examples; a stable Lab
release and diagnostics promotion have their own acceptance gates.

## Usage guard fixed offline; experimental review PR — 2026-10-18

[Qualification](verification/usage-guard-2026-10-18.md): complete numeric usage
now enforces input/output bounds independently of pricing support. Missing or
untrusted component counts latch a stop; role costs retain known unsupported
counts. Policy v2 keeps the frozen v1 study separate. Both-wire installed fault
and baseline matrices pass, with network-denied recovery. Source-suite, artifact
and review results are in the qualification data. No live calls or SDK changes;
limits and all nine unknown reservations remain charged unchanged.

The reviewed branch is published in [draft PR #18](https://github.com/B3Cognition/prosaic-integration-lab/pull/18), without a release. Memory and
correction remain opt-in; no critic/model benefit is established. Public SDK
train and clean-consumer/platform/database acceptance remain release gates.
Next broad milestone: durable failure isolation and explicit recovery; any new
live evaluation needs fresh frozen operators and an audited accounting baseline.
The historical checkpoints below describe their state at the time.

## Frozen correction comparison safely stopped; promotion blocked — 2026-10-18

[Audited partial findings](verification/correction-live-2026-10-18.md):6of16
samples claimed,5known/1unknown; remaining10unrun, no retries.0matchedpairs,
so causal critic benefit unmeasured. Smaller critic named1of2flawed fields and
neither correction repaired the draft; larger critic/corrector never called.
One correct larger worker passed directly, two workers hit512tokenlength;
HTTP200providererror with missing usage stopped the full frozen schedule.

Charged15requests/5tools/29975tokens including unknownfull4/2/8192reservation;
cumulative1509/610/1835168 versus1558/637/1976623.9unknowns now fully retained.
Per-arm limits unchanged.6network-denied state recoveries,9853frozen guards and
38old ledgers verified; no SDK/Core/executableLabchanges, push or release.

Separate synthetic test confirms a generic Lab bug: `unsupported` numeric usage
can bypass the component-bound latch, allowing continuation until scoring fails.
No such breach was observed live. Fix/qualify this offline before promotion or
another live run. Push for review recommended; stable Lab release blocked on
that fix, public SDK train and clean-consumer release acceptance. Next broad
milestone: durable failure isolation/explicit recovery, preserving unknown
reservations and avoiding automatic retries. Keep models/prompts frozen; no
local-model tuning proposed. Frozen operators are closed after canonical live
ledger preservation; future work needs a fresh root/accounting baseline.

## Bounded correction blueprint — 2026-10-18

Opt-in Lab0.5.1+correction.2 adds provider-neutral sanitized feedback and matched
no-critic comparison helpers, plus a separate one-shot rollout consumer through
public SDKs. [Adoption guide](bounded-correction.md),
[qualification](verification/bounded-correction-2026-10-18.md). Both arms receive
the same verified diagnostics/evidence; critic hints cannot bypass host gates.
Unusable/interrupted corrections keep honest field diagnostics and observed or
unresolved costs. Each arm retains4requests/2tools/8192tokens/600s/output512.

Installed offline proof:48scripted arms/24matched pairs,54network-denied
recoveries,2malformed-output checks,131installed payloads verified. One fresh
review's2Important findings reproduced RED and fixed in one pass; no deferred
minors. Final source counts and preservation hashes are in the qualification.
No live calls, new allowance, SDK/Core change, model tuning, push or release.
38ledgers/8unknowns and charges1494/605/1805193 remain unchanged. Keep branch and
worktree. Consumers qualify their own roles/counters and reserve both arms
before future live use; synthetic proof establishes no model/critic benefit.

## Consumer role qualification blueprint qualified offline — 2026-10-18

The maintainer clarified the goal: reusable framework/consumer adoption, not
hardening specific local models. [Adoption guide](role-qualification.md),
[proof](verification/role-qualification-2026-10-18.md). Generic role assessment,
configuration-bound qualification and host-pinned admission helpers live in Lab;
a separate rollout adapter verifies scoped evidence and reports all field errors,
missed/unsupported critique issues and partial warning coverage. Consumers supply
their own roles, policies, evidence grants, suites, models and requalification.
No SDK/Core changes, model-specific branching, prompt tuning, repair or live run.
Final Lab0.5.1+roles.2:1524source tests,46focused tests,24installed both-wire
synthetic lanes; four synthetic qualifications explicitly rejected for live use.
127installed files match source/wheel; five SDK payloads unchanged. One fresh
review found2Important accounting/scope gaps, fixed with9RED→GREEN regressions;
no minors. Existing Starlette deprecation warning only. Current per-case and
cumulative limits unchanged; charged1494/605/1805193 versus1524/625/1976623,
38canonical ledgers/eight unknown reservations untouched. Read-only historical
verification passed. No inference allowance spent, push or release. Existing
frozen model evidence/environments retained. Keep this branch/worktree; any
future live study requires separate frozen consumer-owned cases and authorization.
Preserved410offline evidence files; archive
`prosaic-role-evidence-20261018.tar.gz`, SHA256
`558d53effc722f728814fe3c0ea38fb71ee955a16fffce3666c032efb6a55159`.
Final installed environment `/private/tmp/prosaic-role-final-env`; metadata
`/private/tmp/prosaic-role-study-20261018`; closing verifier
`/private/tmp/prosaic-role-verify.py` is read-only and makes no provider calls.

## Frozen direct worker/critic live evaluation complete — 2026-10-18

[Result](verification/direct-handoffs-live-2026-10-18.md):12/12fresh samples ran
under unchanged caps. Each model passed1/3workers. Smaller critic accepted the
clean control and correctly escalated2/2actual flaws plus2/2seeded flaws, but
all four issue lists were incomplete (5/14required fields; zero invented fields).
Larger controls3/3unusable at512output; full-handoff workers also truncated, so
natural critic benefit remains unmeasured. No answer repair was tested.
Independent host gates prevented acceptance of wrong full-handoff results.
Study18requests/4tools/28754tokens; cumulative1494/605/1805193 versus approved
ceilings1524/625/1976623, remaining30/20/171430. All usage known, no new unknown,
timeout, overrun or counter violation;8old unknown reservations remain charged.
All receipts/accounting reconcile; copied-state recovery denies sockets and
makes zero additional calls. Prepared host41tests/12offline lanes; one fresh
review with3Important fixes before approval. Package/SDK/models stay frozen.
Preserved795new files, canonical ledger38; prior37ledger hashes unchanged.
Archive `prosaic-direct-live-evidence-final-20261018.tar.gz`, SHA256
`cbccd6bd9f717b6983186b53365a045218110c4ef4452f0a8cc5c81ca4e8990b`.
Private study `/private/tmp/prosaic-direct-live-study-20261018`; preserve all
intermediate evidence, including the initial report-directory preservation
failure. No frozen dispatch/audit/analysis code changed after live observation.
Closed operators expect37historical ledgers and cannot dispatch again after
canonical publication. Use a fresh root/baseline for future work.
Next recommended development milestone: provider-neutral role qualification,
source-grounded review diagnostics and separately qualified bounded correction
with a no-critic baseline. No new milestone implementation/live allowance is
authorized by this recommendation. Memory stays experimental; no push/release.

## Direct worker/critic offline qualification — 2026-10-18

Opt-in Lab 0.5.1+direct.2 adds explicit model-visible JSON contracts, host-prepared
assignments and invocation-scoped host evidence for the critic. Worker-only,
critic-only controls and full handoffs skip the model planner.
[Guide](direct-handoffs.md), [qualification](verification/direct-handoffs-2026-10-18.md).
Final: 1,478 source tests, 76 installed both-wire scenarios, 36 unchanged-counter
offline trajectories. One fresh review; three material findings fixed with
RED→GREEN regressions. Largest quoted path: 5,287 tokens. Zero live requests.
Prior 2,596 files / 37 ledgers / eight unknown reservations verified unchanged.
Ceilings 1,500 requests / 617 tools / 1,976,623 tokens; charged usage
1,476 / 601 / 1,776,439. Per-case four / two / 8,192 / 600 seconds / output 512.
No push, release, SDK source change or memory rollout. Real-model contract
compliance and critic benefit remain unmeasured. Next: a small frozen direct-role
live study with full reservations under current limits.
Executable source 7c77df8; candidate environment
`/private/tmp/prosaic-direct-final-env/bin/python`; results
`/private/tmp/prosaic-direct-final-study-20261018`. Previous live environment and
initial candidate/evidence remain intact.
Preserved 1,996 new files in `/private/tmp/prosaic-direct-evidence-20261018.tar.gz`;
hashes are in the qualification's preservation proof. Keep this branch/worktree.

## Eight-sample real-model handoff evaluation complete — 2026-10-18

The [live result](verification/real-handoffs-live-2026-10-18.md) ran all8frozen
samples, four per model, under unchanged caps. All stopped at planner: smaller
4/4schema descriptions instead of values; larger4/4incomplete JSON at512output
tokens. Worker/tool/critic reached0; critic benefit unmeasurable, not negative
efficacy evidence. No new unknown, overrun, timeout or counter violation.
Study8requests/0tools/7268tokens; cumulative1476/601/1776439 versus approved
1500/617/1976623, remaining24/16/200184;8old unknown reservations retained.
Auditor reconciles all receipts/observations and copied-state recovery with
network denied. No model/prompt/graph changes or extra probes during the study.
Next: provider-neutral model-visible output contracts, deterministic host-owned
assignment preparation, and direct worker/critic qualification before another
fresh live evaluation. Memory remains experimental; no push/release.
Preserved450new files;37canonical ledgers,36prior hashes unchanged. Latest ledger
SHA256b87e25f97d522d3a89fb2dd953cc64ee09813d26dcbfc53f3ded9606f31aa17e.
Closed operators expect their original36-ledger baseline and cannot be reused
for a new run; create a fresh study root using the current37-ledger baseline.

## Real-model handoff evaluation frozen; allowance pending — 2026-10-18

[Prepared study](verification/real-handoffs-2026-10-18.md) uses local experimental
Lab0.5.1+handoffs.4, exact sourcefef4182. Full1388tests and15installed regressions
pass;8fixture trajectories use actual qualified counters,4reporting/interruption
phases pass. All3Important review findings fixed; one one-use-audit-path minor
deferred. No live requests. Graph/prose/models/per-case caps unchanged; memory off.
Bindingcd6988b2f6f89197ed25a4a0f731dc657a257c96a4caee2692137374df78eb5d
freezes4fresh cases×2models and3155guard files. Full reservation32requests/16tools/
65536tokens needs25requests/13tools beyond current headroom; token ceiling stays.
Question sent to user; no approval yet. Do not create allowance-approval.json or
dispatch until explicit approval arrives. Cumulative charge1468/601/1769171,
ceilings1475/604/1976623,8unknown retained. Requested new ceilings1500/617/1976623.
Private host operators `/private/tmp/prosaic-real-handoff-{common,live,audit,analyze}.py`,
installed environment `/private/tmp/prosaic-handoff-real-env/bin/python`, root
`/private/tmp/prosaic-real-handoff-study-20261018`. Preserve all prior evidence.

## Offline typed handoffs qualified — 2026-10-18

Lab0.5.1+handoffs.2 adds experimental request-bound planner/worker/critic
contracts and full-trajectory scoring using the same installed SDK candidate
family. [Qualification](verification/typed-handoffs-2026-10-18.md):1373source tests,
40focused regressions,30installed both-wire scenarios and3review regressions pass.
Both independent Important reporting findings closed with RED/GREEN tests;
no deferred minors. Missing/unread/conflicting evidence and disagreement cannot
approve; human review offers stop only. Four-request cap permits no extra repair.
Saved final critic receipt adopts without calls; missing receipt blocks;
earlier interruption is inspection-only. Exact source dc69d1f and wheel audited.
No live calls, SDK changes, push or release. Memory remains experimental with no
new efficacy claim. All1902prior evidence files and36ledgers verify; charge still
1468/601/1769171 versus1475/604/1976623,8unknown retained. Next: frozen real-model
handoff evaluation once its full reservation fits authorized remaining allowance;
full four-sample comparison cannot fit7requests/3tools. Prior checkpoints retained.

## Fresh four-sample missing-evidence comparison complete — 2026-10-18

The [audited held-out comparison](verification/missing-evidence-memory-live-2026-10-18.md)
completed all four samples with known usage under unchanged limits. Both enabled
arms actually recalled relevant history. Smaller off/on failed both after the
permitted correction; fact/citation fields were correct but decision remained
approve despite missing-authority feedback. Larger off/on passed first attempt.
No observed memory benefit; recall added608/221tokens without fewer requests or
tools. All6tools succeeded, no continuation refused, one quote overage correctly
admitted by shared budgeting. New diagnostics show message/unsupported usage
details; numerical totals reconcile, no pricing/cost qualification claimed.
Cumulative1468requests/601tools/1769171tokens; remaining7/3/207452. Eight unknown
reservations and35previous ledgers unchanged;36thledger appended,178new evidence
files preserved. No product/model/default changes, push or release. Ready for
offline provider-neutral typed multi-agent handoff/trajectory qualification;
memory remains experimental. Another full4sample study cannot fit remaining
request/tool reservations. Prior checkpoints below retain original state.

## Response diagnostics qualified offline — 2026-10-18

Runtime0.9.8+diagnostics.1 and Lab0.5.1+diagnostics.1 are local unreleased
candidates. The [qualification ledger](verification/response-faults-2026-10-18.md)
records portable response/usage classifications, sticky contradictory-error
fencing, strict bounded SSE UTF8 and preserved receipt diagnostics. Harness
requires no change. Runtime1345passed/2documented skips; Lab1333passed;
installed57checks,36fault/replay,14continuation and10legacy scenarios pass.
All five independent review findings closed. Exact candidate payloads audited;
active releases and prior manifests/evidence unchanged. No live inference,
push or publication. All35live ledgers still charge1456requests/595tools/
1752686tokens, eight unknown reservations retained; remaining19/9/223937.
Ready for a fresh bounded live comparison that fits full reservations, not a
memory efficacy or live-provider certification claim. Eight full samples do
not fit the current remaining request/tool allowance. Preserve old checkpoints.

## Strict validation fixed; fresh comparison stopped safely — 2026-10-17

Lab0.5.1+continuation.2 fixes derived integer-field validation in both plan
versions. Source b0072fa: full1333passed, installed four regressions,
14both-wire continuation and10legacy scenarios; exact-source payloads audited.
The [fresh eight-sample study](verification/continuation-memory-live-2026-10-17.md)
completed four samples, then stopped on larger-model missing/on unknown usage.
Three samples remain unexecuted; no retry or forgiveness. Approval pairs pass
both arms; smaller memory/on saves one correction, larger has no recall exposure.
Memory benefit remains unproven. Charge1456requests/595tools/1752686tokens;
remaining19/9/223937, eight unknown reservations retained across35ledgers.
Next: provider-neutral response/usage failure diagnostics and synthetic fault
qualification before another live efficacy run. Lab remains experimental;
no new push/release. Prior checkpoints below retain their original state.

## SDK releases and experimental continuation budgeting complete — 2026-10-17

Runtime0.9.7 and Harness0.9.4 are merged and publicly released, with downloaded
bytes matching their exact-source qualification receipts. Core/adapters unchanged.
Lab0.5.1+continuation.1 remains an unreleased local experimental candidate.
Its explicit manifest pins the new public SDKs; the active release manifest and
historic candidates/evidence remain unchanged. Opt-in version2 uses quotation for
context planning and public Runtime shared-budget admission for actual native
continuations; version1 stays default and current caps are unchanged.

Read the [release/qualification ledger](verification/continuation-budgeting-2026-10-17.md)
and [usage contract](continuation-budgeting.md). Full Lab1329passed; final focused35;
installed and network-none Linux ARM6414both-wire scenarios plus10legacy replay
scenarios per platform. Independent review: no blockers, one derived-count type
validation minor deferred. No new live inference. Charge1442/588/1731251 versus
ceilings1475/604/1976623, seven old unknown reservations retained;34ledger and
428prior evidence hashes preserved. Next: frozen held-out validation that fits
remaining33requests/16tools/245372tokens. Memory efficacy remains unproven.

## Fresh balanced memory comparison complete — 2026-10-17

All12 fresh held-out samples settled with known usage under unchanged limits.
Smaller model off/on success is0/3 versus1/3; larger is3/3 versus3/3. The smaller
gain is confounded by quotation-based continuation admission, not demonstrated
reasoning improvement. All14 tools succeeded; three continuations were refused
by fixed planning bounds despite available outer-budget headroom. Read the
[audited comparison](verification/balanced-memory-live-2026-10-17.md).
Cumulative charge1442requests/588tools/1731251tokens; remaining33/16/245372.
Allseven historic unknown reservations remaincharged;34canonical ledgers preserved.
Next recommended milestone: provider-neutral adaptive continuation planning
under the same caps. Generic Runtime/Harness fixes are candidates for normal
release qualification; Lab memory/planning remains experimental. No push/release
was performed by this comparison.

## Provider-neutral tool outcomes and bounded recovery candidate — 2026-10-17

The next operational-hardening milestone is implemented in local Runtime
`0.9.7+tools.1`, Harness `0.9.1+tools.1` and Lab `0.5.1+tools.1` candidates.
[`dependencies/tool-outcome-candidate.json`](../dependencies/tool-outcome-candidate.json)
pins the exact SDK family; the released manifest is unchanged. Read the
[qualification and review record](verification/tool-outcomes-recovery-2026-10-17.md)
before another live run. Recovery is opt-in, provider-neutral and bounded by the
existing case limits. Historic tool errors remain unclassified. No live
inference, merge, push or publication is included in this milestone.

## Native tool and experimental memory release preparation — 2026-10-17

The active train adopts published Runtime 0.9.6 with Core 0.4.1, Runtime recorder 0.3.0, Harness 0.9.0 and Harness store 0.4.0. The previous context train is preserved in `dependencies/releases-lab-context-0.5.0.json`. Agent-quality and controlled retrieval memory examples are opt-in; memory remains experimental. Historical live findings retain their original candidate identity. See [the release ledger](verification/release-0.5.0-2026-10-17.md) for final qualification and publication.

## Published timeout patch adoption — 2026-10-14

The active manifest now pins published Runtime 0.9.3 and Harness 0.8.2, retaining
Core 0.4.1 and both PostgreSQL adapters at 0.3.0. Use `.venv-latest` for this
checkout's audited installed family; `.venv-published` preserves the earlier
demo environment. The full local suite passes 955 tests. Required conversation
acceptance now has 97 cases, adding real provider timeouts for ordinary and
interpretation turns with no redispatch on replica replay/recovery.

Read the [patch ledger](verification/conversation-timeout-patch-2026-10-14.md)
for exact publication, manifest hashes and acceptance results. Older checkpoints
retain their original versions and counts.

## Published SDK adoption — 2026-10-13

Runtime 0.9.0/recorder 0.3.0 and Harness 0.8.0/store 0.3.0 are now published.
The active release manifest selects their exact verified PyPI wheels alongside
unchanged Core 0.4.1. The former patch manifest is preserved in
`dependencies/releases-lab-0.4.0.json`. Ordinary released acceptance now selects
the conversation lane without candidate flags. Start with the README's assistant,
workflow and approved-conversation recipes, and read the separate
[fresh adoption ledger](verification/published-conversation-adoption-2026-10-13.md).
Lab release and hosted-provider qualification are separate remaining work.
The checkpoints below preserve their original publication state and evidence.

## Conversation adoption checkpoint — 2026-10-12

Lab target 0.5.0 implements authenticated bounded conversations, a fixed host-only
selection/review workflow, actual diagnostic conformance, and a ninth required
acceptance lane. Read [the conversation guide](conversations.md) and
[its qualification evidence](verification/conversation-adoption-2026-10-11.md#final-source-platform-qualification--2026-10-12).
Exact source `34f291e8c7f7dd3809767c2fbf518b55e50204d6` passed
[run 38212165309](https://github.com/B3Cognition/prosaic-integration-lab/actions/runs/38212165309):
325 required cases per Linux AMD64/ARM64 × PostgreSQL 16/18 cell, plus 95
extracted-sdist conversation checks on ARM64/16. All 1,395 acceptance executions
passed with zero skips and verified cleanup, including 475 conversation checks
and both documented candidate demos per cell. Closed capacity diagnostics
reconcile 18 requests/ledger calls with p95 0.2085–0.2469 seconds.

The final local suite passed 943 candidate tests and 921 applicable published
baseline tests with zero skips; only three functional files requiring the absent
conversation API are excluded from the old baseline. The earlier failed
`0f7791c` capacity qualification and its unidentified cause remain recorded;
the earlier `018425b` commit improved diagnostic reporting without claiming a
capacity bug fix. Subsequent CLI, interpreter-format and native-call clarifications
retain their separate historical results in the live ledger.
[Actual local Qwen evidence](verification/local-conversation-2026-10-12.md)
records the original blocked 7B native-tool run and subsequent successful closure
at `34f291e`: explicit strong effecter binding, 943 candidate/921 applicable
published-baseline tests, a complete live journey plus two independent workflow
sessions, quoted approval denied, and duplicate approval replay with zero calls.
All earlier failed allowances are preserved; the maintainer authorized further
bounded testing and fixes. The final four-cell run qualifies that exact executable
source; this later documentation commit records its result. Runtime/Harness
publication, Lab release, ordinary public-index adoption and hosted qualification
remain pending. Published and
historical manifests below are unchanged.

The subsequent main-branch merge also includes the previously verified prepared-
context handoff, described in the [context ledger](verification/context-handoff-2026-10-12.md#integration-with-the-conversation-candidate).
The combined source passed 948 candidate and 926 applicable published-baseline
tests. Its required contract has 54 native plus 95 conversation cases: 326 per
candidate cell. This newer source needs its own platform receipts; the exact
`34f291e` results above retain their original identity. Harness ordinary CI now
curates the original qualified Core/Runtime artifacts while Runtime 0.9.0 is
unpublished, preserving sandbox and database requirements. Version bumps already
select Runtime 0.9.0/recorder 0.3.0, Harness 0.8.0/store 0.3.0 and Lab 0.5.0.

Checkpoint: 2026-10-09, first working synthetic consumer on a local feature branch.

## Release checkpoint

For the current published ecosystem and Lab 0.4.0 release at `f47328d`, read
[the current delivery status](current-status.md) and
[the release closure](verification/production-readiness-m1-m2-2026-10-11.md#lab-040-release-closure).
The historical Lab 0.3.0 release remains recorded in
[the public adoption ledger](verification/public-release-adoption-2026-10-11.md).
The checkpoint and release ledger below retain their historical versions and
evidence.

The maintainer subsequently authorized committing all repository changes and
publishing new releases. The earlier no-publication statements below describe
their historical tasks. Read [the historical release ledger](verification/release-train-2026-10-09.md)
for the earlier version pins, verification and remote publication status. All Lago
work is now committed; earlier shared-file staging constraints are historical.

## Lago extension checkpoint

The approved Lago design/plan adds `lab_runner test --mode lago`. A separate
application-owned outbox exports public Runtime evidence to digest-pinned local
Lago 1.55.0, with frozen attribution, unknown-cache exclusions, duplicate recovery,
fenced leases, open-period gating and independent fixture-charge reconciliation.
Prosaic core, Runtime and Harness sources remain unchanged.

The required lane passed 25 cases on both PostgreSQL 16 and 18 on Docker Desktop
Linux/arm64, zero skips and verified cleanup. Existing deterministic (21) and
recovery (27) lanes passed on 16. Read `verification/lago-progress.md` for receipts,
review findings/fixes, setup failures and the exact verification checkpoint.
The tests use synthetic inference and separate direct public-ledger fixtures;
no payment collection, customer invoicing or production billing certification.

Shared runner files are also being changed by other authorized lab work. Preserve
those changes; do not stage whole files indiscriminately or assume the latest
consumer image tag equals a recorded immutable image ID.

## Completed

- Maintainer approved the separate integration-lab design.
- Public repository and Apache-2.0 license created.
- Approved design, README, agent instructions and remaining-work checklist saved.
- [Tracking issue #1](https://github.com/B3Cognition/prosaic-integration-lab/issues/1)
  published with staged work and acceptance requirements.
- No existing Prosaic/Harness/Runtime library sources changed for this handoff.

## Implementation checkpoint

Native implementation was authorized by the maintainer's “proceed”. Branch
`codex/integration-lab` contains the consumer image, wheel provenance/audit,
owned runner, explicit grants, owner-only HTTP APIs, zero-call approval and
synthetic inference/accounting. PostgreSQL 16 and 18 acceptance ran on Docker
Desktop Linux/arm64 with verified cleanup. Read `verification/progress.md` for
exact receipts and remaining coverage. No push or release is implied.

The optional host-side local model reads `~/.omlx_token`; its 7B Qwen Coder smoke
succeeded and reported 85 tokens. No cloud/TokenProxy model calls were made.

## Historic initial handoff

At the initial documentation-only handoff, no Python application, dependency lock, image, PostgreSQL fixture, workflow asset,
model stub, test runner, load balancer or CI job exists yet. No container or model
was started. No acceptance test, architecture matrix or live endpoint was run.
Commands in the design are target interfaces, not commands available today.

## Initial next action (superseded)

Read the [approved design](superpowers/specs/2026-10-09-prosaic-integration-lab-design.md)
and [tracking issue #1](https://github.com/B3Cognition/prosaic-integration-lab/issues/1).
Review the [written implementation plan](superpowers/plans/2026-10-09-prosaic-integration-lab.md)
and its execution ledger. The plan was prepared and approved in this checkout
on 2026-10-09. Native execution starts with released-dependency provenance and
exact-owned provisioning. No paid calls are needed for synthetic milestones.

Do not re-request approval of the already approved project direction unless a
material change is needed. The written implementation plan is now approved.

Recommended milestone order:

1. Clean released-package consumer image and exact-owned stack lifecycle.
2. Trusted identity, durable ownership/idempotency and filtered HTTP endpoints.
3. Zero-model-call cross-replica workflow approval.
4. Synthetic inference, public SDK accounting and multiuser acceptance.
5. Fault-gated recovery, overload, accounting failures and repeatability.
6. Non-sticky load balancing and PostgreSQL 16/18 CI on Linux/arm64 and amd64.
7. Explicit live TokenProxy mode and its separate evidence/limitations.

Each milestone needs independently executable tests and a commit with evidence.
Pay particular attention to app ownership reservation versus Harness creation:
they are not one transaction. Never reinterpret a missing response/checkpoint
as permission to redispatch a possibly completed request.

## Released dependency baseline

Initial baseline verified from release metadata on 2026-10-09:

| Distribution | Version | Release source commit |
| --- | --- | --- |
| prosaic-harness | 0.6.0 | 2bd14fd8aa17f30c957ff29f886ffd16b2af52ca |
| prosaic-harness-postgres | 0.1.0 | same Harness source commit |
| prosaic-runtime | 0.6.0 | b13a62eac955b19b13fe2c9dc646a188069f72f2 |
| prosaic-runtime-postgres | 0.1.0 | same Runtime source commit |

- [Harness v0.6.0 assets](https://github.com/B3Cognition/prosaic-harness/releases/tag/v0.6.0)
- [Runtime v0.6.0 assets](https://github.com/B3Cognition/prosaic-runtime/releases/tag/v0.6.0)

Both releases include core/adapter wheels, source archives and
`SHA256SUMS-0.6.0.txt`. Download the artifacts, verify their checksums and save a
dependency manifest during implementation. Assets have not been downloaded or
checksum-verified by this new repository's handoff task. Install each core
before its adapter and lock the complete service/test dependency graph.

Harness 0.6.0 pins Runtime 0.6.0, which installs Prosaic transitively. Review the
resolved dependency provenance rather than adding a second interpreter or an
editable sibling dependency.

## Operator references

- [Harness PostgreSQL provisioning/grants](https://github.com/B3Cognition/prosaic-harness/blob/v0.6.0/adapters/postgres/README.md)
- [Harness accounting attribution/recovery](https://github.com/B3Cognition/prosaic-harness/blob/v0.6.0/docs/accounting.md)
- [Runtime PostgreSQL recorder contract](https://github.com/B3Cognition/prosaic-runtime/blob/v0.6.0/adapters/postgres/README.md)
- [Runtime measurement and coverage](https://github.com/B3Cognition/prosaic-runtime/blob/v0.6.0/docs/accounting.md)

Read these before defining roles or interpreting unknown evidence. Shared
PostgreSQL does not make workflow and accounting writes atomic. Namespaces are
not authorization, leases are not external-effect idempotency, and estimates
are not customer charges.

## Historic initial verification record

At handoff, verification is limited to documentation/file consistency, Git
publication and public repository/issue visibility. Implementation-specific
test results must be recorded by the next session; do not inherit upstream
test counts as proof that this service works.
