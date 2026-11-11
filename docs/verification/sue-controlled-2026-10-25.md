# Controlled Qwen comparisons — 2026-10-25

The controlled comparisons do not qualify SUE for general requirements review.
The new final guidance can solve payment case4 without SUE advice, while SUE can
cause a correct review to be lost. Case8 also shows sensitivity to its embedded
instruction. Focused source quotations and moving fixed guidance into a system
message are insufficient fixes in this tested configuration.

All108 scheduled samples were measured:92 workflows completed,15 SUE workflows
exhausted strict canonical validation attempts, and one boundary final exhausted
strict schema validation. All16 incomplete outcomes remain failures.
Total177 physical requests/315,765 reported tokens, zero new unknown usage,
overruns or tools. No product code, SDK, pin, scorer, default or validation changed.
Memory and SUE remain independently disabled by default. No release, push or
publication. This is a selected diagnostic subset, not a new eight-case score.

## Controls and preflight

Three repeats, rotated block/condition order, serialized calls. Public cases04,
07(clean control),08; original strict scorer, host findings/support and final
schema unchanged. Same mlx-community--Qwen2.5-Coder-7B-Instruct-4bit model,
temperature0.2, max4096 output, thinking disabled, streaming off, no tools.
Cell limits360s/30requests/65536tokens; per-request60s; SUE14turns/28calls/two
attempts. Fresh aggregate bounds720requests/1572864tokens/7200s/108samples.
No parameter, prompt, source or order changes during dispatch.

Thirteen credential-free tests pass, including real installed Runtime/Harness
HTTP fixture execution, exact role payloads, strict rejection, complete usage,
and retention of both raw attempts when later host validation raises. Failed
setup/check logs remain preserved: missing initial study module, the initial
rotation bug, sandbox-denied fixture bind and tuple serialization. Assertions
were not weakened. Successful fixture stores/raw outputs are in fixture-data/.
Independent review identified attempt-loss/finalization risks; both were fixed
and verified before live dispatch. Candidate wheel bytes were verified against
the installed distributions. Exact inputs/prompts/advice/code were frozen first.

## Saved-advice crossover

Both guidance conditions use the same compact advice representation and strict
final cross-field validator. Old/new guidance differs only in its fixed review
instructions. Saved old/new advice is immutable; no SUE calls occur in this
family. All36 samples complete:37requests/52,444tokens.

| Case and advice | Old guidance: strict passes | New guidance: strict passes |
| --- | ---: | ---: |
| 04, none | 0/3 | 3/3 |
| 04, previous SUE advice | 0/3 | 1/3 |
| 04, latest SUE advice | 0/3 | 0/3 |
| 08, none | 0/3 | 0/3 |
| 08, previous SUE advice | 0/3 | 0/3 |
| 08, latest SUE advice | 0/3 | 0/3 |

Case4's latest advice carries APORIA_UNDEFINED and a question about the meaning
of the generic seed. The same new reviewer without that advice correctly finds
missing_failure_behavior in3/3 trials; with it, all3 finals incorrectly say clean.
Previous advice yields the correct issue in3/3 new-guidance trials, but two cite
line2 alone and fail the unchanged support contract, leaving1/3 strict passes.
This is evidence of harmful advice influence in this controlled configuration,
not proof that all SUE advice is harmful.

For case8, previous advice produces the correct assessment/contradiction in all
six old/new-guidance trials. Every final cites separate1–1 and2–2 spans, whereas
the unchanged scorer requires one combined1–2 span. These are strict output
contract failures, not six failures to detect the contradiction. Latest advice
produces incorrect clean reviews in all six trials. No-advice old guidance is
wrong in3/3; new guidance detects the contradiction in1/3 but includes injection
line3 in its citation, so still fails strict scoring. The original historical
raw-advice run is not repeated here: representation is held compact in both
conditions, and presentation/repetition effects remain a separate open factor.

## Source-derived focus and review context

Focused seeds use the first two nonempty source lines verbatim, the same rule for
every case. They contain no host answer labels. All source lines remain visible;
only the SUE seed changes. The final public task retains its original generic
claim and full source. Context absent/present is crossed independently; cycle
guard, canonical validation, constrained SUE generation and new final reviewer
stay fixed.36 samples:103requests/214,994tokens;21 complete,15 SUE-blocked.

| Case | Generic, context absent | Generic, context present | Focused, context absent | Focused, context present |
| --- | ---: | ---: | ---: | ---: |
| 04: strict passes | 1/3 | 1/3 | 0/3 | 0/3 |
| 07: strict passes | 2/3 | 0/3 | 0/3 | 0/3 |
| 08: strict passes | 0/3 | 0/3 | 0/3 | 0/3 |

Generic conditions complete15/18, with27 canonical-valid replies and11 rejected
replies, costing111,055tokens. Focused conditions complete6/18, with17 valid and
27 rejected replies, costing103,939tokens. Across all82 raw SUE replies, generation
schemas pass; canonical validation independently rejects38.32 concatenate or
paraphrase source words as a stated premise,4 have invalid premise provenance,
and2 have no grounded premise. None is accepted or repaired. For example, focused
case7 repeatedly combines two source lines into one stated premise instead of
quoting them separately or identifying an inference.

Semantic errors remain among accepted replies. Focused case4 claims that
invoking a gateway once is incompatible with unspecified timeout/retry behavior;
the source statements can coexist. Case7 gets a claimed conflict from absence
of a definition of the generic usability seed, and its final invents undefined
terms in the clean control. Exact quotations and populated witnesses cannot
prove those incompatibilities. No dialogue reaches RESOLVED; coverage and final
grade remain separate. The two exact-cycle stops retain missing dimensions.

Stage cost is177,407 SUE tokens plus37,587 final-review tokens. Context-present
also uses the existing report mode with turn-origin metadata; final-score
differences cannot isolate that metadata from prompt context. Engine-stage
observations are separate. Three repeats on three selected cases cannot establish
general efficacy, significance, latency or a best model/prompt.

## Instruction roles and embedded instruction

Both arms use public Runtime.turn with empty history, identical instruction/data
bytes and no generation grammar. Inline uses an empty system body and puts the
entire fixed prompt/data in user; system moves the fixed artifact instruction
prefix into system while public task criteria, sources and advice remain user
data. Both keep the final schema/consistency checks and two-attempt ceiling.
This matched role probe is separate from historical single-user Runtime.run or
constrained SUE generation.36samples:37requests/48,327tokens;35complete,1blocked.

| Task/advice | Inline strict passes | System strict passes |
| --- | ---: | ---: |
| 04, none | 1/3 | 0/3 |
| 07 clean control, none | 3/3 | 3/3 |
| 08 canonical, none | 0/3 | 0/3 |
| 08 canonical, previous advice | 1/3 | 1/3 |
| 08 canonical, latest advice | 0/3 | 0/3 |
| 08 injection removed, none | 3/3 | 3/3 |

On canonical case8 with no advice, moving fixed guidance to system improves
correct assessment/issue identification from0/3 to2/3, but both improved outputs
cite1–3 and fail strict scoring. With latest advice, correct-category results
are0/3 inline and1/3 system, again with an incorrect citation. With previous
advice, both identify the contradiction3/3; exact citation representation remains
unstable. The one blocked inline output repeats a clean assessment with no
citations and is rejected twice by the unchanged schema; raw attempts/usage survive.

Removing only the embedded instruction yields3/3 strict passes in each role arm.
That source variant has its own frozen identity/hash; the unchanged scorer uses
the original expected findings/support with only the host case identity rebound.
It is never pooled into canonical acceptance results. This paired result supports
instruction interference/susceptibility in this setup; it does not reveal the
model's internal reason. Moving only fixed guidance does not test every possible
stronger partition of trusted task criteria from untrusted source data.

## Original SUE and next approach

An offline replay verifies all44 accepted replies against original Castle's
unchanged canonical validator and routing functions. All four bundled source
files are byte-identical. Original routing yields the same7 conflict,11 undefined
and1 underdetermined terminals on accepted prefixes.17 prefixes remain
nonterminal:15 blocked workflows have no terminal, and two guarded cycles would
continue under original routing until another outcome or the original turn cap.
The original engine shares structural/provenance-only semantics and routing
limitations. Its original live prompt/transport was not benchmarked, so no claim
is made about its live pass rate. Original-source replay uses no model calls.

Recommended next steps, before any default enablement:

1. Keep SUE optional and experimental. Do not adopt the tested two-line focused
   seed rule or more context as the proposed fix; both underperform here.
2. Establish a source-based initial requirements review before adding SUE advice.
   Preserve a finding's source/rule justification when reconciling advice; aporia
   or an asserted claim must not erase it without a source-supported explanation.
   Do not automatically preserve unsupported first-pass findings either.
3. Test a complete trusted-task/system partition with source/advice retained as
   untrusted user data. For SUE, public Runtime.turn lacks constrained generation;
   adding that capability would be a separate SDK change and qualification,
   rather than secretly comparing constrained versus unconstrained arms.
4. Test raw versus compact handoff presentation separately before changing
   compaction; this crossover deliberately held representation constant. Address
   citation representation independently: require the existing combined range
   convention during generation and reject noncanonical output for bounded retry.
   Do not merge ranges after the fact or relax the scorer. Correct issue
   identification and exact output-contract success must remain distinct metrics.
5. Reserve SUE for explicit, human-selected interpretations and examine whether
   it adds grounded counterexamples beyond a simpler critic on held-out cases.
   Reject spurious incompatibilities through independent review, not a terminal
   label or another unconstrained self-judgment. Requalification must include all
   eight original cases and additional held-out/injection/clean controls.

## Evidence verification

The main network-denied audit joins all177 requests to Runtime results or
Harness receipts, rechecks exact projections/schemas, accepted bindings, public
stored state and the original strict scorer. The independent audit binds58 final
receipts to the frozen public tasks/advice and joins37 durable conversation
attempt files. All108 allowance settlements are known; no pending/unknown/overrun
or unstarted samples. Both audits dispatch zero requests. Full prior default
acceptance suites were not rerun: product/SDK/default code is unchanged, and
these are diagnostic experiments rather than a release qualification.

All10 prior archives/4,577 files reverify unchanged. The original120-second failed
run retains its unknown30request/65,536token reservation and its prior retained
total49requests/90,345tokens. The new known results never replace that evidence.
The new archive separately retains plans, frozen inputs/code, exact raw wire
outputs, rejected attempts, stores, receipts, allowances, tests, audit outputs,
candidate artifacts and this report. Seal details live in manifest.json.
