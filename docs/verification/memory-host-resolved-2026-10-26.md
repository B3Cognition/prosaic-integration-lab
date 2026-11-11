# Optional host-resolved generation — 26 October 2026

`compact-host-resolved-v1` is implemented as an explicit freeze-time generation
profile. It leaves memory/SUE defaults, prior generation/execution modes, the
canonical answer schema, validator, source scope/provenance and scorer unchanged.
It is not a release or a claim that the Qwen memory comparison is qualified.

Question parts carry exact quoted text instead of model-calculated offsets.
The host requires a unique exact Unicode substring, including overlapping-match
detection, and derives its offsets. Missing/ambiguous/normalized matches fail.
Frames still require a review reason and an unreferenced disposition; selected
evidence determines used-frame status and claim IDs. Used links follow the claim
array order in this profile. The same canonical gate validates the assembled
object. Historical rejected outputs remain rejected; no output is repaired.

## Verification

| Check | Result |
| --- | --- |
| Full source suite, previously qualified released SDK environment | 2,187 passed, 73 subtests passed; existing Starlette warning |
| Source focused/candidate lanes | 70 passed, 36 subtests passed |
| Final host unit tests, including schema ownership regression | 22 passed |
| Fresh installed candidate memory/profile lanes | 92 passed, 36 subtests passed |
| Installed live-diagnostic fixtures | 7 passed |
| Independent final implementation review | No actionable findings |
| Source/wheel/sdist/fresh-install Lab payload equality | 238 matched |
| Exact qualified SDK wheel/fresh-install payload equality | 7 packages, 133 payloads matched |
| Canonical validator functions and answer contract | Unchanged |

Tests include Unicode and overlapping ambiguity, foreign/missing/duplicate
references, rejection of old manual offset/link fields, every-frame coverage,
exact source preservation, draft encoding, public Runtime/Harness answer and
review, frozen resume/cross-profile rejection and unknown-usage retention.
The mutable schema alias regression was watched failing before the ownership
fix. Generated host-profile schemas cannot mutate the canonical validator.

The separately attempted full default suite with Runtime
`0.9.8+jsonschema.3` and the Lab installed produced **45 failures, 2,141 passes
and 73 subtests**. All 45 failed node IDs reproduce against the untouched
pre-change installed package. These are existing SDK qualification/environment
guards (including checks that expect the Lab absent), not host-profile
regressions. Their assertions and qualification allowlists were not weakened.
The memory candidate lanes qualify this explicit experiment; they do not add
the candidate SDK to other Lab applications' public qualification closures.

Builds, installed tests and the live call use fresh artifacts/environments;
older environments and evidence were retained. Changes are local/unpublished.
No new PostgreSQL, Linux, native or cross-architecture acceptance claim is made.

## Same Qwen task, 360-second diagnostic

One fresh request used the same frozen q001/manual question, all displayed source
frames, ThinkingCap Qwen checkpoint, temperature 0, 4096 output tokens and strict
validation. Only the explicit generation profile and its required prompt/schema
changed. The frozen source packet digest remains
`0a4affa8ca91dca8c0dcd353640430cafec5868406aa91c70cad5cd82cbbba49`.

The request **timed out at 360.005 seconds**. HTTP 200 headers arrived at 0.056 s;
first reasoning-channel text arrived at 184.731 s. No final content, terminal
finish, DONE or usage arrived. The 3,028-character partial reasoning-channel
buffer is incomplete JSON. It is diagnostic evidence, never an accepted answer.
Cache usage is unknown because terminal usage is absent; this is not labelled
as a measured cold run or compared as a cache-controlled latency improvement.

No retry/repair followed. The fresh allowance retains its full **one request /
32,768 tokens**; SHA-256:
`0a13b443afb8a5bcc3c2a95807fd0b11689e482fcc230a92eb8d5c00a9be4fc1`.
All ten prior unknown reservation files and 31 prior evidence copies (34,565
indexed files) reverify unchanged, including failed setup evidence and its
conservative reservation. Global/model settings hashes stayed unchanged.

The previous 360-second result was warmed and mechanically invalid. This new
run cannot establish live improvement because it did not finish. Schema and
canonical acceptance are therefore unestablished here, not a completed answer
rejected on a newly observed grounding error. Semantic quality, completeness
critic benefit and the 100-question model comparison remain unmeasured/gated.

Evidence is preserved privately with test logs, baseline guard reproduction,
source/package/dependency proofs, the frozen protocol, raw request/SSE/timing,
strict rejection proofs, allowance and preservation records. No credentials or
private corpus/run evidence were added to the repository. Memory and SUE remain
disabled by default; nothing was published to PyPI or pushed.
