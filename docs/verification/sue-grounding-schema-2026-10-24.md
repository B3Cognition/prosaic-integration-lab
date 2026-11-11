# SUE grounding generation schema — 2026-10-24

## Scope and cause

Canonical SUE acceptance, source handling and public SDK pins are unchanged.
Memory, SUE and constrained generation stay independently disabled by default.
The pure engine, Runtime candidate0.9.8+jsonschema.2, Harness, original Castle,
SUE lenses and SOAR are unchanged by this repair. This is a Lab adapter change;
it does not establish natural-language entailment or release readiness.

Canonical JSON schema describes field shapes but leaves inter-field rules to
the engine. The preceding [guidance-only study](sue-grounding-2026-10-24.md)
still produced 10 rejected replies among 15 schema-valid SUE replies. Explicit
prompting alone did not reliably enforce SILENT evidence, supported claims or
operator answer types. Preserve that failed candidate at Lab `b8b429e` and its
604-file archive `castle-sue-grounding-fix-20261024`, manifest SHA256
`c4f5904c46c256e003f277a6c02108ae579f3a53b7b533cdccd19d97194b8d74`.

## Repair and boundaries

The v1.5 adapter preserves the canonical responseSchema in its projected prompt,
then requests generation-only alternatives through Runtime. Each alternative is
one canonical result/verdict pair with necessary constraints for its evidence,
premise kinds, claim, operator success type, witness and revision fields.
Source citation bounds come from frozen sources; address bounds come from
recomputed accepted turns. No response is edited, citations removed, verdict
rewritten, attempt added or budget increased. Canonical checked_advance and the
Harness validator are AST-identical to the previous candidate.

The generator owns a JSON copy before narrowing fields. Tests caught and fixed
shared schema-array aliases that initially excluded valid answers. The
canonical schema remains unmodified. All result branches for all eight
operators remain generatable, including examples, partial/unknown/conflict
outcomes, disclosed assumptions and exact substring quotations. Extra schema
conditions are necessary conditions, not a second acceptance engine: exact
quotes, premise-to-answer citation subsets, uniqueness, revision coverage and
natural-language support still require independent validation/review.

The new generation policy version and existing guidance digest are sealed into
adapter v1.5. Legacy v1.2 behavior/policy/binding remains unchanged. Copied v1.3
and v1.4 stores remain inspectable with their original wheels; the new candidate
returns binding_unavailable with networking denied. No original store changes.

## Verified mechanics

- 18 generation tests pass after watched failures, covering canonical-valid
  results and invalid combinations, plus continuing independent rejection of
  false quotes, out-of-set premise references and paraphrased stated premises.
- Full public SDK suite: 2,158 passed, zero skips; one existing Starlette
  deprecation warning. All assertions and frozen comparison inputs remain.
- Focused schema/grounding/constrained tests: 39 passed. Installed final SUE and
  comparison tests: 62 passed. SDK-only absent-package lane: 105 passed.
- Installed oMLX xgrammar compiled23schemas and matched49values: all34
  canonical-accepted synthetic turns and five accepted prior wire replies are
  admitted; all10 prior rejected replies are blocked. Zero model calls. This is
  grammar compatibility evidence, not truthful-review evidence.
- Scripted comparison24/24,88synthetic requests/1,320tokens,56constrained SUE
  requests; network-denied replay adds zero calls.
- Installed constrained PostgreSQL16/18 lanes pass six cases each with exact
  inventories, no skips and verified owned-fixture cleanup. Runtime usage is
  recorded through the actual PostgreSQL recorder and separate runtime role.
- Legacy memory/SUE installed acceptance: 76/76 on each PostgreSQL16/18,
  complete inventories, zero skips and verified owned-fixture cleanup.
- Direct wheel and rebuilt-sdist wheel are byte-identical; installed package
  payloads are verified before benchmark dispatch. General closed SDK adoption
  is still unqualified; ordinary public Runtime remains0.9.8.

Fresh read-only review found no canonical-valid exclusion or acceptance defect.
macOS ARM64 consumer and Linux ARM64 PostgreSQL containers do not qualify native
Linux consumer/remote CI or a public release.

## Same Qwen benchmark: partial, safety-stopped

The original24-cell schedule stopped after its first12cells (cases1–4). The
original120-second cell deadline expired during case4 SUE's eighth answer.
Three SUE workflows completed; case4 accepted seven turns before timeout. No
grounding-rejected reply was accepted, and no observed workflow exhausted its
attempts on grounding. Two non-verbatim stated-premise replies were rejected
and corrected by the already configured second attempts. They remain evidence,
not repaired outputs or a claim that the model never makes grounding mistakes.

| Strategy | Observed/scheduled cells | Completed | Strict passes among observed |
| --- | ---: | ---: | ---: |
| Direct | 4/8 | 4/4 | 2/4 |
| Critic/author | 4/8 | 4/4 | 3/4 |
| SUE | 4/8 | 3/4 | 3/4 |

The other12cells have no outcome. This is not a completed comparison or evidence
of a general quality advantage. All13 SUE wire replies match both the canonical
schema and generation schema;11 pass canonical validation, including one late
response never received/accepted by Runtime. There are no provider schema
enforcement warnings. Actual accepted-state replay is authoritative.

The gateway recorded28physical requests. Runtime knows44,810reported tokens;
the provider later reported another3,894tokens after Runtime timed out. The
wire total48,704 is observational evidence only: the receipt remains
`usage_unknown`/`timeout`, with no accepted answer08. One unknown cell retains
its full30request/65,536token reservation. Total retained allowance is
49requests/90,345tokens, zero tools/pending samples/overruns. No automatic retry,
reservation release, allowance expansion or dispatch of the remaining cells.

The frozen operator's original complete-usage observer correctly failed its
wire-versus-Runtime usage equality assertion after this late response. Its
source and failed log are unchanged. A separate network-denied partial observer
verifies the exact12-cell prefix, all checkpoints/receipts and the one unknown
invocation; it explicitly distinguishes Runtime usage from late wire usage.
Replay adds zero calls. Independent audit joins all28physical requests and
recomputes accepted history. Four observed direct prompts and four initial SUE
prompts are byte-identical to v1.4. Limits, canonical guidance, source cases,
scorer and model profile are unchanged.

Remaining qualification blocker: the same benchmark cannot finish within its
original deadline with this Qwen SUE trajectory. A longer-deadline experiment
would be a separately identified comparison, not a passing rerun of this one.
Normal memory and SUE defaults stay disabled. There is no release/promotion.

## Evidence

Private study root: `/private/tmp/prosaic-sue-grounding-schema-20261024`.
The same Qwen model, cases, rotating schedule, original scorer, profile and
finite allowances are retained. Canonical guidance and the generation
supplement are unchanged from v1.4; only generation transport constraints and
the explicit v1.5 binding change. Provider warnings stop the study rather than
silently accepting downgraded schema enforcement. Prior failed evidence and
charged unknown reservations remain unchanged. No push, merge or publication.

Final source is `e9ae33e` (the final hygiene change removes only a test-file
blank line). Frozen archive `reports/castle-sue-grounding-schema-20261024` has
539files; manifest SHA256
`157d9ca70a0052078cb63941cfdbd3185dbfde6055d5fa70ee40938ab41ed61e`.
All3,090files across seven previous archives verify unchanged. The final source
wheel matches the frozen study wheel byte for byte. The unmodified diff check
initially caught the trailing test-file blank line; its failed export log is
retained alongside the successful export. This archive records a failed partial
live qualification, not a successful full benchmark.
