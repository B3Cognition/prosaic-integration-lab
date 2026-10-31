# Protected independent review and handoff comparison

The user authorized protecting independent review from SUE advice, then comparing
stronger instruction boundaries and raw/compact handoffs with the same Qwen and
strict scorer. Memory and SUE remain disabled by default. Existing modes, source
formats, canonical SUE, SDKs and failed evidence remain intact.

Add an explicit consumer-owned source-first workflow. It accepts only a frozen
public task, invokes the existing final-review guidance without advice or other
agent artifacts, and retains strict final consistency and source citation checks.
Harness owns accepted output and receipts; Runtime owns all model execution.

Capture a completed independent result as immutable bytes bound to its task,
source snapshot and run identity. A candidate may contain a separately validated
complete review, but the exported canonical final always comes from the captured
independent result. No candidate promotion, merging or hidden approval exists.
This protects accepted output from advice influence; it does not certify that
the original review is correct. Invalid/blocked independent reviews remain failed.
Advice failure cannot destroy an already captured independent result.

Expose explicit raw/compact candidate inputs and two instruction partitions:
fixed guidance in system with public criteria in user (weak), versus fixed
guidance plus the complete trusted criteria/schema in system (strong). Evidence,
source wording, title, claim, independent model output and advice remain user
data. Criteria must match the host's case-neutral public definitions/schema and
instructions. No model-supplied instruction can acquire system authority.

Candidates use the same strict final schema/provenance/consistency checks and
the unchanged original scorer, but are advisory outputs. Report canonical scores
and candidate scores separately; unchanged canonical output is a safety invariant,
not evidence that SUE improved quality. Existing v1/v2/v3 remain unchanged.

The experiment has three repeats. Fresh independent and existing critic/author
baselines cover all eight original cases (24+24 samples). Candidate comparisons
on cases04/07/08 cross weak/strong boundaries with none, old-raw, old-compact,
new-raw, new-compact advice (90 samples). All conditions in each case/repeat
reuse that repeat's frozen independent result and identical saved advice. No
fresh SUE generation is included; candidate costs exclude historical generation.
This isolates handoff effects and is not a live end-to-end SUE efficacy trial.

Same Qwen model, temperature0.2, max4096 output, thinking disabled, no tools,
360s/30requests/65536tokens per sample,60s per call, two validation attempts.
Aggregate bounds720requests/1572864tokens/7200s/138samples. Stop on unknown usage,
provider warning or overrun and retain the maximum reservation. Freeze inputs,
scripts, installed-wheel identity and order before dispatch. Never mutate prior
archives or reconcile an old unknown using new successful usage.

Implement with watched rejection/immutability/transport tests, full default Lab
suite, isolated wheel checks, public SDK fixtures and frozen replay. Archive raw
wire results, all failures, receipts, snapshots, allowance and audits separately.
No automatic enablement, push, release or publication is authorized.
