# Runtime final-answer candidate qualification — 2026-10-16

The user explicitly authorized extending Runtime and qualifying a pinned wheel
after the instruction-only study still produced repeated tool requests.
Runtime owns execution; Core and Harness engines were not changed.

## Candidate behavior and identity

Host endpoint feature `finalize_after_tool_rounds: 1` removes tools and
tool_choice after the permitted lookup and adds trusted final-answer guidance.
Further tool calls fail before dispatch with `tool_finalization_not_honored`.
Public conversation turns retain their closed `providerFailure` vocabulary.
Existing request/tool/token/deadline/cancellation admission remains in force;
missing usage remains unknown. Defaults are unchanged.

Runtime is isolated at `/private/tmp/prosaic-runtime-tool-finalization`,
branch `codex/runtime-tool-finalization`, based on qualified v0.9.3 commit
`342d4fa40068e2b3a48165ea29cfcb2248a39833`.
Candidate source commit: `0d47abcf00ba44f5820b5f51ab3ceac4fa6e4198`.
Local version: **0.9.3+finalize.2**. No release, tag, merge or publication.

| Artifact | SHA-256 |
| --- | --- |
| Runtime wheel | ae8653fe86cd7b88c22239a68450188dc6a679cf52fa68cd9298ecfb9bfa72cb |
| Runtime sdist | 550927bb0412eb0b80cf1ccbabae4cd695827e2f28062bf68dbd8b052fd1bb41 |
| Five-wheel candidate manifest | 99a14eff66b49f3235f58ba67f7e9cf82512ffab764a9131b9e56657bfa7ed6f |
| Consumer 0.5.0+finalize.2 wheel | bbbebf2ee44ab5e2ba2301c99aee1a65e39d458fc33d21d488af6530259a9a95 |
| Consumer sdist | d055500f77054eb51ef68e767fcf4f5de6559467c8d77d0cf8850ddd0ed1a5cd |

Only Runtime is replaced in the five-wheel SDK train. Core 0.4.1,
Runtime-postgres 0.3.0, Harness 0.8.2 and Harness-postgres 0.3.0 remain
byte-identical to their released wheels. Candidate manifest is
`/private/tmp/prosaic-finalize2-sdk.json`.
The candidate consumer was built from a source sdist snapshot with explicit
candidate SDK provenance. All 17 benchmark source/resource files match source
except the intentionally replaced sdk-provenance.json. Source default provenance
and existing release environments/evidence are preserved.

## Verification

- Feature regressions observed failing before implementation; 27 focused cases
  pass, including both transports, streaming, defaults, thresholds, acquisition,
  public turns, noncompliance, missing usage and exhausted budgets/cancellation.
- Fresh review identified finalization rejection after conversation validation;
  the corrected two-transport regression fails on old ordering and passes with
  the guard moved ahead. No second handler executes.
- Preliminary full suite: 1102 passed, two expected skips, one archive-version
  failure because HEAD still referenced the released base. Local candidate
  commit makes the archive input explicit; authoritative rerun is recorded below.
- Lab source suite: **1034 passed**, one existing Starlette warning, 116.21s.
- Runtime and consumer wheel/sdist builds passed. Separate Python 3.11 Runtime
  and Python 3.12.14 consumer environments use locked dependencies and exact SDK
  wheels. Installed ownership, CLI/admission/recorder construction, metadata gate,
  pip check and five-wheel payload audits passed.
- Installed consumer smoke passes with real synthetic HTTP and correct/wrong
  grading. With finalization enabled: **10/10 fixture cases**, **3/3 recovery
  probes**, 24 main-case provider requests, 12 tools, 3600 tokens; **16**
  final-only payloads across cases and probes have no tools or tool_choice.
- No database/service acceptance lane was rerun for this local Runtime
  candidate. This is bounded execution/consumer qualification, not operational
  or database release qualification.

## Residual-budget live study

Fresh directory: `reports/quality-live-20261016-finalize-candidate`.
Schedule: ten cases × one repetition × two existing profiles = **20** samples.
The instruction-only baseline used three repetitions; do not merge the schedules
or present this as an identical baseline. Prose, schemas, grading, model IDs and
512-output-token settings remain unchanged; SDK provenance and endpoint feature
are explicit changed inputs. Case deadline remains 300 seconds; batch 10800.

Before launch, authenticated local catalogue GET confirmed both profiles,
installed identity matched the candidate manifest, and the fresh allowance was
absent. All five prior ledgers reconcile to retained **423 requests /91 tools /
378164 reported tokens**. Candidate ceilings are exactly the residual **57 /
149 /604876** under cumulative **480 /240 /983040**. All three historical
unknown reservations remain charged at full maximum.

Authoritative Runtime suite: **1105 passed, two expected skips**, 367.76s.
The skipped installed-wheel check passed separately; the other skip requires
a framework Python build.
An initial relative-output CLI invocation was rejected before dispatch; the
absolute private directory invocation created the fresh allowance and is the
only inference process.

Live session 56784 completed with exit 1 because the smaller profile failed
its tasks; **baselineComplete and usageComplete are both true**, with all
**20/20** scheduled samples measured. Total **44 requests /12 tools /40645
reported tokens**, 916.11 seconds summed sample time (15.27 minutes), maximum
164.59 seconds; no timeouts or unknown usage.

| Metric | Instruction-only study | Runtime candidate |
| --- | ---: | ---: |
| Larger task passes | 16/30 | 10/10 |
| Larger ordinary first-pass | 11/24 | 8/8 |
| Seeded critic detections | 5/6 | 2/2 |
| Corrected-draft passes | 5/6 | 2/2 |
| Failed tool-round-limit invocations | 13 | 0 |
| Smaller task passes | 0/30 | 0/10 |
| Smaller native tools | 0 | 0 |

These are distinct interventions and sample counts, not a statistical claim.
The previous study's first repetition alone passed 5/10 larger cases and 2/2
drafts; the new single repetition passed 10/10 and 2/2. The instruction correction
had already enabled draft repairs; the Runtime transition removes the remaining
repeated-round failure in this observed candidate run.

Larger: 24 requests /12 tools /24771 tokens, median 72.51s, eight ordinary
and four critic/author invocations, all twelve exit 0, no schema/task retries.
There are no excess tool calls. Four duplicate records are expected critic/author
reads across repair cases; one irrelevant record remains, so lookup precision
is not perfect. Smaller: 20 requests /0 tools /15874 tokens, median 2.61s,
ten schema repairs and no successful tasks. Finalization does not solve its
failure to emit native tool calls.

Offline audit passed: all twenty verdicts, evidence digests, known settlements
and counts match saved receipts; exact report rebuilding and replay with socket
and provider execution forbidden leave summary, allowance and all canonical
sample files byte-identical. Only sdkVersions/sdkManifestDigest changed in the
benchmark identity; endpoint fingerprints explicitly bind the new host feature.

All six ledgers retain **467 requests /103 tools /418809 tokens**, below
480/240/983040. Remaining **13 /137 /564231**. The three historical unknown
reservations remain intact. No further inference was started.
Candidate archives, manifest and qualification scripts are preserved under
`dist/quality-finalization/`; live evidence and audit JSON remain private.

## Decisions and practical limits

- Manual sibling worktree because the native chat worktree tool targets Core;
  cost: manual lifecycle. Existing Runtime main/example/context work is preserved.
- Local candidate version because v0.9.4 exists on unrelated work; cost: narrow
  local-version report admission, covered by a failing-then-passing regression.
  Strict SDK provenance matching remains intact.
- Existing user approval covers native execution of the written proposal;
  cost: routine implementation choices are made without repeated approval gates.
- Tool-free OpenAI calls have no tool phase; feature validation stays at the
  shared tool-loop entry specified in the plan. Cost: irrelevant invalid feature
  values are ignored in tool-free calls.
- Preserve this isolated candidate and historic evidence for review. No shared
  branch, package index, database or model-server configuration is changed.
