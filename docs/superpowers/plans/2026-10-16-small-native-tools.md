# Smaller-model native tool correction implementation plan

> Native inline execution continues under the user's fix-and-rerun request.
> Use systematic debugging, TDD and one final review; no repeated design gate.

**Goal:** Make the unchanged smaller model emit real native calls, then measure
the same benchmark with unchanged scoring and model identities.

**Architecture:** Opt-in Runtime omlx_tool_call_envelope requests a server grammar
during lookup; existing finalization removes tools/grammar for the final answer.
Existing json_mode constrains the final JSON. No assistant-text execution,
silent model substitution, schema relaxation or server mutation.

## Completed diagnosis and implementation

- [x] Classify all20 previous smaller outputs:19fenced/1bare function JSON in text,
  no native envelope; inspect installed template/parser and prior failed probes.
- [x] Test prompt clarification:47focused and1034full consumer tests pass, but
  one-case live diagnostic fails with2requests/1779tokens/0tools. Revert change,
  preserving failed snapshot and evidence.
- [x] Test native grammar on wire:1request/830tokens,1native lookup_records call
  with valid declared IDs,0handler executions. Preserve diagnostic ledger.
- [x] TDD Runtime vendor feature:7RED/1existing safety guard, then35GREEN.
  One fresh review finds tool-free validation gap; four new RED cases, shared
  validator fix,39focused GREEN. No deferred findings.
- [x] Commit reviewed source566d71d;1117full Runtime tests pass, two expected
  skips; installed-wheel gate passes separately. No code changes after test.
- [x] Build/pin Runtime0.9.3+finalize.4 and consumer0.5.0+smallnative.2, four sibling
  wheels unchanged; isolated installed audits/smokes/pipcheck pass. Flag+json_mode
  fixture10/10,recovery3/3,16final payloads checked.
- [x] Publish no release. Save reusable candidate-only YAML and guide; fingerprint
  matches tested profile. Keep released manifests/configs unchanged.
- [x] User approves80additional provider requests: cumulative560requests,
 240tools,983040tokens. All8previous ledgers retain470/103/421418 and three unknown
 reservations. New residual90/137/561622; no resets.

## Measurement and closure

- [x] Finish same10cases x1repetition x2profiles in fresh private
  reports/quality-live-20261016-small-native;300s cases,10800s batch. Session99281.
  Smaller complete6/10,15/15native invocations,zero schema repairs. Larger10/10;all20measuredknown;offline audit passes.
- [x] Rescore every sample, verify event/journal/receipt counts and evidence
  digests, reconcile all9ledgers, and prove socket/provider-denied byte-identical
  replay. Save exact artifacts/scripts and dated verification record.
- [x] Record honest model-quality limitations and preserve isolated branch,
  worktree and evidence without merge, push or publication.

## Decisions

Keep the failed prompt intervention out of the final candidate; cost: the
observed fix depends on explicit oMLX/Qwen support. Host grammar constrains
envelopes, not argument correctness or reasoning; grants/validation remain
authoritative. Named tool_choice is not relied on because the installed server
does not enforce it. The numerical allowance increase is the user's explicit
approval, not an inference from a general request to rerun.
