# Experimental audit with host-resolved evidence

Use this profile to check whether a frozen answer leaves out requirements from
the sources it was given. It produces an advisory sidecar; it never edits the
answer or changes its score. It does not enable Castle memory, SUE or SOAR.
The canonical critic remains the normal review workflow.

The new `consumer-answer-span-audit-refs-v2` profile gives the model short proof
IDs instead of asking it to reproduce hashes and character offsets. The trusted
host resolves those IDs to exact immutable source spans. The original strict
ledger and audit validators still decide whether the result is admissible.
A valid reference proves an address, not that the model's interpretation is true.
Review quality still needs a controlled comparison.

## Try the synthetic examples

This is unpublished candidate functionality. Use the qualified Lab wheel with
the exact Runtime candidate pinned in `dependencies/answer-span-runtime.json`;
ordinary released Runtime installations do not qualify this profile. CI builds
that candidate and checks installed direct and sdist-rebuilt wheels on Linux
AMD64 and ARM64. No PyPI publication is authorized.

Running the module without a command executes nothing:

```sh
python -I -m lab_runner.answer_span_refs
```

To run one credential-free loopback fixture, choose a fresh output directory:

```sh
python -I -m lab_runner.answer_span_refs fixture --case omitted --output /tmp/refs-omitted-001
```

Other cases are `complete`, `unavailable` and `unknown-usage`. Expected outcomes
are `findings`, `clear`, `clear` and `unresolved`, respectively. An unavailable
case contains an explicit supported limitation; missing sources are not invented.
The unknown-usage case retains its entire 65,536-token reservation. All cases
verify that the original answer is unchanged and resume makes zero provider
requests. The CLI offers no live-model switch and needs no real credentials.

## Embed it in a trusted application

Use `freeze_refs(review)` from `lab_runner.answer_span_refs.contracts` with the
same frozen `ReviewPacket` accepted by the existing audit. Then call
`run_audit(config, packet, directory, accounting=...)` from
`lab_runner.answer_span_refs.workflow`. Supply an explicitly authorized installed
Runtime config and a fresh private absolute directory owned by the current user.
Do not accept tenant, billing scope, endpoints, file permissions or budgets from
model output. Resume with the same frozen packet, config and directory.

The host owns authorization, lossless source projection and proof resolution.
Runtime owns constrained generation and native usage. Harness owns workflow
state and resume. The source stage sees the full frozen source bodies without
the draft; the audit stage receives the accepted ledger and the original draft.
Repeated source text is displayed once with aliases and ordered occurrence
records; every original body remains exactly reconstructable, including CRLF
and Unicode. Selected citations remain tied to their original frame.

The limits are two requests, 120 seconds per request, 270 seconds overall,
65,536 reported tokens, 4,096 output tokens and no tools or retries. Each wire
response, expanded canonical result and bound envelope must fit 16,384 bytes.
Envelope overhead counts inside that limit: a large valid-looking response can
still fail; it is never truncated or accepted with weaker checks.

Native results are captured before adaptation under `transport/`. Accepted
envelopes bind their raw records, catalogs, schemas and inputs. A separate seal
preserves unaccepted native failures when Runtime strips callback metadata.
Mutation refuses resume before dispatch. Unknown usage retains the full hold
and does not authorize retry. Raw run state is operator-only evidence and must
not be returned in public API responses or committed to Git.

The legacy benchmark, v1 audit and critic packages retain their original bytes.
Memory and SUE remain disabled by default. This profile adds no automatic audit,
retrieval, repair, release or model-provider authorization.
