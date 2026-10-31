# SUE grounding guidance study — 2026-10-24

This first repair is insufficient and remains experimental. The v1.4 adapter
adds explicit generation-only field relationships and trusted source/accepted
turn index context only when `constrained_json=True`. Canonical guidance,
schemas, pure engine and independent validators are unchanged. Default v1.2
behavior, saved policy format, public SDK pins and memory/SUE defaults remain
unchanged. No output is repaired, citations stripped, verdict coerced or retry
allowance increased.

## Observed cause and result

The preceding constrained-JSON study produced 16 schema-valid SUE replies but
13 engine rejections: 11 SILENT answers with answer citations and two with
premise citations outside an empty answer-evidence set. Some responses also
paraphrased stated premises or addressed future dialogue turns. The general
instruction “SILENT has empty evidence” left these field relationships implicit,
and retries received only `sue_answer_invalid`.

The new supplement spells out the relationships without selecting a successful
verdict. It distinguishes the seed from a required verbatim source phrase and
source line numbers from prior dialogue turn numbers. Its digest is sealed in
v1.4. Existing v1.3 runs fail closed under the new binding and remain inspectable
with their archived original wheel; v1.2 reports remain identical under both.
Compatibility inspection denied all network access and preserved the original
stores.

Same Qwen7B model/profile, eight cases, three strategies, rotating order,
temperature .2, 4096 output cap, no thinking/tools, cases/scorer/limits unchanged:

| Strategy | Completed | Strict passes | Requests | Reported tokens | Median cell seconds |
| --- | ---: | ---: | ---: | ---: | ---: |
| Direct | 8/8 | 4/8 | 8 | 8,434 | 4.817 |
| Critic/author | 8/8 | 3/8 | 16 | 14,915 | 8.169 |
| SUE | 4/8 | 3/8 | 19 | 33,985 | 20.680 |

All 43 requests/57,334 tokens reconcile; zero new unknowns, pending samples,
overruns or tools. Offline replay added zero calls. All 15 SUE replies are strict
canonical-schema-valid JSON, but 10 fail independent engine validation. Observed
conditions include four SILENT answer citations, one out-of-set premise reference
and one non-verbatim stated premise (conditions may overlap). The engine also
rejects missing DEFINE claims and successful answers of the wrong operator type.
All four completed SUE reviews stop after one DEFINE at APORIA_UNDEFINED; one
blocked review accepted a DEFINE before rejecting both DISTINGUISH attempts.
There is no sustained-review quality qualification.

All eight direct prompts are byte-identical to the preceding study. This is one
trial per case/strategy, with uncontrolled model/cache and concurrent local test
load. Failed-cell timings do not measure successful-review latency; neither
score differences nor latency differences establish efficacy.

## Verification and preservation

The source context regression was watched failing before implementation.
Installed candidate execution/schema/guidance/grounding/comparison tests: 44
passed. SDK-only absent-package lane: 105 passed. Scripted comparison: 24/24,
88 synthetic requests/1,320 reported tokens, 56 constrained SUE calls and zero
additional replay calls. PostgreSQL16/18 constrained installed lanes: six each;
unchanged legacy memory/SUE lanes: 76 each, exact inventories, zero skips and
verified owned-fixture cleanup. Consumer is macOS ARM64; database containers are
Linux ARM64. These are not native Linux consumer/remote CI qualification.

The Lab wheel and rebuilt-sdist wheel are byte-identical; installed wheel payloads
are checked before live dispatch. Runtime stays at the prior unpublished
0.9.8+jsonschema.2 candidate; closed general SDK adoption remains unqualified.
Public Runtime0.9.8 is still the ordinary Lab pin.

First synthetic/full attempts lacked sandbox loopback permissions and are
retained alongside correctly permissioned runs. Two new public-lane test cases
initially passed no store and failed during setup; the test now supplies the real
FileRunStore and preserves the exact fail-closed assertion. Compatibility
observer setup initially passed a newer constructor keyword to the old wheel,
then used disabled settings with nondefault policy; corrected inspection uses
the actual constructor and frozen enabled policy with networking denied. All
failed observer logs and old raw model responses remain evidence.

Fresh read-only review found no correctness defect. Its boundary-test gap was
resolved with raw receipt, generation-guidance and digest-binding regressions
for both SILENT failure classes, plus archived v1.3 rejection proof. Full-suite
and final archive facts accompany the completed study. The next repair will
enforce representable field relationships during generation while retaining
canonical acceptance, before another separately frozen comparison.

Private evidence root: `/private/tmp/prosaic-sue-grounding-fix-20261024`.
Preserve all six earlier archives and charged unknown reservations. Memory and
SUE remain disabled by default. No push, merge, publication or original Castle
backport is included.
