# Smaller-model native tool calling — 2026-10-16

The user requested fixing the smaller model's native calls, then rerunning the
benchmark. All earlier studies and reservations are preserved. Core and Harness
engines, model weights, server settings and API secrets are unchanged.

## Diagnosis and rejected intervention

All twenty smaller-profile outputs from the previous candidate study described
lookup_records in ordinary assistant text: nineteen fenced JSON and one bare
JSON. None used the installed Qwen template's tool-call envelope. The server's
json_tools parser expects that envelope; template and parser agree. Earlier
generic native-call clarification and named tool_choice probes had also failed;
the installed oMLX route does not enforce named choices.

An explicit envelope/final-JSON prompt clarification passed 47 focused checks
and the 1034-test consumer suite (one existing warning, 114.19s), but its one-case
live diagnostic still failed: **2 known requests, 0 tools, 1779 tokens**.
This disproven instruction intervention was reverted. Its separate
0.5.0+smallnative.1 snapshot and private evidence remain available. No prompt
change is credited as a fix.

A separate request using the server's supported structured_outputs.regex
constraint returned **one native tool_call**, finish_reason tool_calls, correctly
named lookup_records, with both record IDs publicly declared: **1 request,
830 tokens, 0 handler executions**. This proves the native response format on the
same 7B model; it is a transport diagnostic, not a successful benchmark task.

## Reviewed implementation

Operator feature `omlx_tool_call_envelope: true` requests the oMLX regex
`<tool_call>\s*\{[\s\S]*\}\s*</tool_call>` only while tools are offered.
It requires explicit finalize_after_tool_rounds. The final-answer phase removes
the constraint. json_mode is suppressed during tool generation and restored
for final JSON. Native Anthropic rejects this vendor option before dispatch.
The host still checks native tool names/arguments, grants, budgets and usage;
ordinary assistant text is never promoted to an executable call.

The smaller profile enables this option plus existing json_mode. The larger
profile retains its prior features. Benchmark prose, schemas, scorer, workflow,
policy and model IDs match the previous qualified finalization study; only SDK
provenance and the smaller endpoint fingerprint change.

Initial regressions: 7 fail/1 pre-existing safety guard passes. Focused 35 pass.
Fresh review found tool-free dispatch bypassing config validation; four new
cases failed on old ordering, then all **39 focused tests passed**, 19.87s.
One fix pass; no deferred minors.

Runtime source commit: **566d71d77ceb1ab8c004edb0237486ea9498e16d**.
Version **0.9.3+finalize.4**, isolated branch codex/runtime-tool-finalization,
worktree /private/tmp/prosaic-runtime-tool-finalization. .3 was an unqualified
pre-review archive; all .2 candidate evidence/environments are preserved.

| Artifact | SHA-256 |
| --- | --- |
| Runtime wheel | 9754b80be34df692d67e01b08be2a691e94b8c9c9ad744e1c2f76006c64c0111 |
| Runtime sdist | b3b8feb8fe668c2ad6f3c43b8b4dd056fd43f337c4509447bbbc9e729d4a2500 |
| Five-wheel manifest | 027f857a2fc344b87201d3c4da4a850730f0fc435e6fcddb1384bf03229fef0e |
| Consumer 0.5.0+smallnative.2 wheel | 289020bfb83839965fc4f03475721c775c146523c2a23302ce283180f9c8683b |
| Consumer sdist | b9d906ac66c59b79d8d11ef84605ec2a94f9031d58d07433d10a5e19097afd36 |

The four released sibling SDK wheels are unchanged. Candidate consumer was
built from a separate snapshot with exact manifest provenance. All 17 benchmark
source/resource files match source except explicit sdk-provenance.json. The
source's default released SDK provenance remains unchanged.

## Qualification and live schedule

- Wheel/sdist builds pass; new Python 3.11 Runtime and Python 3.12 consumer
  environments use locked dependencies and exact wheels.
- Installed Runtime ownership/CLI/admission/recorder-construction checks,
  mandatory installed metadata gate, pip check and five-wheel payload audit pass.
- Installed consumer smoke passes using real synthetic native dispatch.
- New flag plus json_mode: **10/10 fixture cases and 3/3 recovery probes** pass;
  16 final payloads verified grammar-free and JSON-constrained. All tool-phase
  payloads carry the envelope grammar and omit final response_format.
- Full Runtime suite: **1117 passed, two expected skips**, 376.54s. The
  installed-wheel gate passed separately; the other skip needs framework Python.
  No database/service acceptance lane rerun;
  this remains local execution/consumer qualification, not release qualification.

The user explicitly approved **80 additional provider requests**, raising the
cumulative request ceiling **480 → 560**. Tool **240** and token **983040**
ceilings remain unchanged. The eight earlier ledgers retain **470 requests /
103 tools /421418 tokens**, including three fully charged historic unknowns.
Fresh study residual limits: **90 /137 /561622**, twenty samples, 300-second
cases and 10800-second batch window. No old allowance is reset.

The study schedules the same ten cases × one repetition × two profiles as the
previous candidate study, in reports/quality-live-20261016-small-native.
Authenticated catalogue and exact provenance/contracts/allowance preflight
passed immediately before inference. Live session99281 and the final offline
audit are complete; results follow.

## Completed same-schedule rerun

Session99281 completed with CLI exit1 for the four failed smaller-model tasks,
not incomplete measurement. **baselineComplete:true, usageComplete:true**;
all20/20 samples settled known. **54 requests /27 tool executions /48386
reported tokens**. Summed sample time1078.45s (17.97min), maximum182.74s;
no timeouts or new unknowns. All27 agent invocations exited0 and each executed
one genuine native lookup, joined to its handler journal and receipt.

| Metric | Previous candidate | Native-envelope candidate |
| --- | ---: | ---: |
| Smaller task passes | 0/10 | 6/10 |
| Smaller ordinary first-pass | 0/8 | 5/8 |
| Smaller native tool executions | 0 | 15 |
| Smaller schema repairs | 10 | 0 |
| Smaller critic detections | 0/2 | 0/2 |
| Smaller strict repaired-draft passes | 0/2 | 0/2 |
| Larger task passes | 10/10 | 10/10 |
| Larger critic / corrected-draft passes | 2/2 / 2/2 | 2/2 / 2/2 |

The native-calling failure is resolved in this tested model/server configuration.
Remaining smaller-model failures are reasoning errors: conflict-02 and missing-01
exhausted correction attempts with wrong decisions; both repair workflows
produced correct final author answers but their critics missed the required
draft flaw, so the unchanged strict scorer rejects them. Five rejected answer
attempts had wrongDecision; no answer JSON parse/schema failures. Three semantic
retries account for three excess calls across invocations, not repeated tool
rounds within an invocation. No irrelevant records were read.

Smaller30requests/15tools/23946tokens, median6.19s, max14.37s. Larger
24requests/12tools/24440tokens, median85.75s, max182.74s. Larger all eight
ordinary cases pass first try; no schema/task retries or excess calls. These
are one-repetition local results; latency differences and success rates are not
production reliability or causal statistical estimates.

## Final audit and disposition

Offline audit independently rescored all twenty canonical samples, checked
evidence digests, receipt/event/journal joins, tool counts and known settlements,
and rebuilt the exact public summary. Replay with sockets and provider execution
forbidden left summary, allowance and all twenty canonical samples byte-identical.
The two diagnostic ledgers' evidence digests and counts were checked separately.
Only sdkVersions/sdkManifestDigest changed in benchmark identity; the smaller
endpoint fingerprint also binds envelope+json_mode. The larger fingerprint is
unchanged.

All nine ledgers retain **524requests /130tools /469804tokens**, under
**560 /240 /983040**. Remaining **36 /110 /513236**. All three historic unknown
reservations remain fully charged; no further inference was started.

Exact candidate archives, manifest, unsuccessful prompt snapshot and verification
scripts are preserved under dist/quality-small-native/. The private study retains
offline-audit.json. Reusable opt-in configuration:
configs/runtime-local-native-candidate.example.yml; its fingerprints match the
tested profiles. Default released SDK manifests/configs remain unchanged.
The Runtime branch and worktree are retained for review, unpublished and unmerged.

## Decisions and limits

The failed prompt change is reverted rather than bundled with the grammar fix;
cost: native correctness depends on the explicit host/server capability.
The vendor feature is opt-in and protocol-specific; unsupported servers may
reject or ignore it. Envelope constraints do not prove correct arguments or
answers; the unchanged grader and handler receipts remain authoritative.
Keep isolated branches and exact candidate artifacts for review; no release,
merge, push, database or shared server changes are performed.
