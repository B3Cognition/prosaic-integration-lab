# Loaded ThinkingCap Qwen rerun — 2026-10-26

The maintainer reported ThinkingCap was now loaded in oMLX and requested another
run. Read-only status confirmed `ThinkingCap-Qwen3.8-27B-MLX-4bit-DWQ` loaded and
the server idle before inference. Earlier preflights explicitly requested
`mlx-community--Qwen2.5-Coder-7B-Instruct-4bit`; this is a separately labelled
model comparison, not a same-model loading fix.

The new run changes only the selected model in its private configuration. It
reuses the [qualified question-first candidate](memory-question-first-2026-10-26.md),
same frozen three cases/nine samples, source corpus, strict schema/grounding,
scope/provenance, scorer, focused guidance, temperature zero, 60-second calls,
4,096 output-token limit, no tools and no retries. The new shared allowance is
27 requests /884,736 tokens /3,600 seconds. Memory and SUE remain disabled by
default; SOAR is separate. No package/source behavior changed or was published.

| Result | Observation |
| --- | --- |
| First sample | `q001-manual` |
| Answer-stage elapsed | 60.254 seconds |
| Attempt result | Timeout, unknown usage |
| Retained output | Empty; not proof that the server emitted nothing |
| Provider requests / accepted answers / critic calls | 1 /0 /0 |
| Remaining samples | 8 blocked by unknown-usage policy |
| New reservation retained | 3 requests /98,304 tokens |
| Full 100-question model batch | Not started; readiness gate failed |

The request records the same artifact, arguments and declared wire-schema
identities as the preceding focused-profile trial. Model selection is explicitly
ThinkingCap 27B in the frozen run settings. No accepted answer exists for strict
semantic scoring, and no conclusion about Castle versus file search or critic
benefit follows.

The local settings file has no explicit thinking-token budget enabled for this
model; model status reports thinking enabled by default. The admin settings API
returned 401, so the selected local settings snapshot is labelled as disk evidence,
not proof of effective live settings. No server setting was changed.

The available server log contains a soft-memory-pressure eviction of the other
7B model near the end of this request. Afterward only ThinkingCap remained loaded,
with no active/waiting requests. This is a useful observation, not evidence that
memory pressure caused the timeout. The run has no per-phase stream trace, so
queue, prefill, reasoning and answer-generation time cannot be separated. The
next diagnostic should measure those phases under a separately bounded trace
before changing deadlines, reasoning settings or validation.

Verification rechecks the unchanged candidate's code identities against its
previously qualified protocol. Earlier full-suite results remain historical;
no new full-suite run is claimed for a model-only rerun. Sealed replay and the
same completed-run command return identical results with zero dispatch and no
output-file changes. The strict scorer's ungraded report retains all nine samples
in the denominator.

All 19 prior archive copies /33,729 indexed files verify unchanged, along with
all seven earlier unknown reservations. This run adds an eighth, without
settling or replacing any earlier reservation. Raw receipts, model/serving
state, frozen configuration/protocol, scorer/replay outputs and failed admin
read are preserved privately in `qwen-reloaded-20261026`; credentials and private
source payloads are outside Git.
