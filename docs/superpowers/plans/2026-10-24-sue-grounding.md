# SUE grounding generation repair

> **For agentic workers:** Use superpowers:executing-plans inline, then a fresh read-only review.

**Goal:** Reduce the observed Qwen grounding failures without changing acceptance or the comparison's cases, scorer, controls or allowances.

**Architecture:** Keep the canonical engine, schema, rules and validator unchanged. Add explicit generation-only field relationships and trusted dialogue/source index context to the constrained mode. Bind the supplement into a new adapter identity; preserve legacy mode and inspect old constrained runs with their archived candidate.

**Spec:** The user's grounding repair request and the constrained JSON qualification in `docs/verification/sue-constrained-json-2026-10-24.md`.

## Constraints and review focus

- Memory and SUE stay disabled by default; no public SDK adoption or publication.
- Do not repair responses, strip citations, coerce verdicts or grant extra attempts/calls.
- SILENT permits no answer evidence or grounded premises; source-supported answers remain possible. Do not force successful verdicts or conceal missing support.
- Premise citations must be a subset of answer citations; stated text must be verbatim. Source lines and dialogue turn numbers are separate namespaces.
- Guidance must not change canonical acceptance, frozen legacy policy or silently resume a different binding. Previous failed evidence and charged unknown reservations remain intact.

## Tasks

- [x] Add failing public-boundary tests for constrained generation context across accepted turns/retries and a distinct binding; retain rejection and raw-receipt tests for both observed failure classes, false quotes and future turns.
- [x] Add the explicit grounding supplement only to constrained mode, include its digest in adapter v1.4 and preserve canonical schema/validator/default v1.2 behavior.
- [x] Run focused and full public suites; build identical wheel/sdist candidates, qualify installed constrained PG16/18 and scripted comparison/replay.
- [ ] Freeze a separate installed-candidate operator and rerun the same 24-cell Qwen benchmark. Audit/replay without network, classify results and retain all failures.
- [ ] Fresh read-only review, fix material findings with regressions, archive verification and document limits; commit locally without push/release.

## Investigation update

The v1.4 generation-guidance study completed all 24 cells with 43 requests and
57,334 reported tokens. All 15 SUE replies matched the canonical JSON schema,
but the independent engine rejected 10. Four SUE workflows completed and three
passed the original scorer; direct passed four and critic three. Guidance alone
is insufficient. Preserve this separately identified failure before changing
generation again.

Next within the same authorized repair: express mechanical field relationships
as generation-only JSON-schema alternatives (result/verdict, SILENT empty
evidence/assumption-only premises, required claim, operator success type,
witness/revision fields and trusted source/turn index bounds). Keep canonical
schema projection and acceptance unchanged. Prove canonical-valid branches
remain generatable, reject observed invalid combinations, compile locally and
freeze another candidate/study before the same Qwen rerun. Exact quotations,
premise-to-answer citation subsets and natural-language support remain subject
to independent canonical validation and review.

The v1.5 generation-schema candidate blocks all10 prior rejected replies in the
actual installed grammar backend, while admitting all34 canonical-valid
synthetic turns and five prior valid replies. Its same120-second live rerun
safety-stops after12cells: case4 SUE accepts7turns, then answer08 times out.
Two non-verbatim stated-premise failures are rejected and corrected within
existing retries; a late provider response cannot repair Runtime's unknown
receipt. Preserve the full unknown reservation and partial/unrun outcomes.
Full24-cell live qualification remains blocked at the original deadline;
changing it requires a separately identified comparison. Do not mark that
qualification as achieved merely because mechanics/tests pass.
