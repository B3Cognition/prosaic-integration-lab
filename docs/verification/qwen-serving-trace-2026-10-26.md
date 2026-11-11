# Qwen serving trace — 2026-10-26

The maintainer approved tracing queue, schema setup, prefill and decoding after
the compact-profile timeout. This investigation changes no production code,
SDK, oMLX configuration, source grants, validator, scorer, deadline or defaults.
Memory and SUE remain disabled; no publication or push occurred.

## Measurements

The running installation is oMLX 0.7.2 with the same Qwen2.5-Coder-7B 4-bit model.
Its warning-level logs lack historical per-request timing. Read-only health and
status calls show the model loaded and the server idle before the trace.

First, a credential-free endpoint captured the exact public Runtime HTTP
projection. Its artifact/argument identities and response-schema hash match the
preserved failed run. Runtime already requests streaming, so no transport-mode
change was necessary. A transparent loopback proxy was verified against a
streaming fixture before any real inference; it forwards the payload unchanged.

One separately precommitted trace uses the same prompt, schema, temperature,
4,096 output-token limit and 60-second deadline through the installed public
Runtime/Harness. It reserves one request / 32,768 tokens and permits no retry.

| Observation | Result |
| --- | --- |
| Upstream response headers | 0.031 seconds |
| First nonempty content | 0.912 seconds |
| Runtime end | 60.095 seconds, unknown usage |
| Upstream content observed | 416 chunks / 7,613 characters, including a late chunk during downstream closure |
| Completed usage or terminal event | None |
| Accepted answers / critic calls | 0 / 0 |
| Queue sampling | 120 samples, maximum waiting0 / active1; active returns to0 |

The partial output contains 41 complete claim objects using `quote-1` through
`quote-41` consecutively, and begins a further object. It includes repeated
default-state facts and release/version material beyond the question's requested
default work and enabled public access. It has started only `citations` and
`claims`; required question parts, evidence objects, frame review and the other
sections have not been emitted. This is ordinary continued claim generation,
not an observed end-of-answer/EOS stall. It remains incomplete JSON and is never
accepted or scored as an answer.

This trace is dominated by output generation after first content. It does not
reconstruct the original failures' queue/prefill times: the model was already
loaded and the exact prompt had been used previously; KV cache usage for this
trace is not reported. No token count can be inferred from SSE chunk counts.

## Offline phase checks

Using only cached tokenizer/config files and installed oMLX/xgrammar code in a
separate process, without model weights or inference:

- Exact captured messages tokenize to12,137 prompt tokens under the model chat
  template; tokenization takes0.019s after tokenizer loading.
- Grammar compiler initialization takes0.326s; compact schema compilation0.033s
  and canonical schema compilation0.009s. This is isolated-process evidence,
  not an instrumented timing measurement inside the shared server.
- Runtime's `own_response_schema` serializes with sorted keys, alphabetizing
  `properties`. oMLX calls xgrammar with its default `any_order=False`.
  The observed top-level order is citations, claims, evidence, frameReview,
  missingEvidence, questionParts, sections, status.
- An offline matcher accepts the alphabetically ordered schema-valid fixture
  and rejects the same answer in question-first order. Reordering only the
  schema properties reverses those results, while ordinary JSON Schema validity
  and the canonical schema digest stay identical. Thus question-first planning
  cannot be emitted first under the current wire grammar.

Grammar order is a demonstrated generation constraint, not a demonstrated cause
of the timeout by itself. The concrete output problem is claim fan-out over the
paragraph index; relevance guidance and field order are the next controlled
variables. Input reduction alone has not qualified this model/deadline.

## Recommended next changes, not implemented here

1. Preserve the declared schema property order on Runtime's wire projection.
   Retain bounded deep ownership, canonical hashing and validation. Version and
   freeze the operational wire order explicitly so resume cannot silently change
   constrained generation. Add an upstream regression and installed transport
   verification before adopting a new Runtime candidate.
2. Make question-part planning lead generation. Ask for distinct facts needed
   by those parts, consolidate duplicate support, and omit unrelated corpus
   summaries. Keep all existing evidence available and final completeness/scoring
   strict; avoid a universal small claim cap that could truncate complex tasks.
3. Verify each change separately, then repeat the same bounded Qwen preflight.
   Launch the100-question model comparison only after structural, known-usage
   and strict semantic gates pass. No improvement is assumed from this trace.

## Accounting and preservation

The trace times out with unknown usage and retains its full separate one-request
/32,768-token reservation. All five earlier unknown reservations remain held
unchanged. Partial/late stream content is diagnostic evidence, not accepted
output or completion/usage evidence. No settlement, automatic retry or larger
model comparison occurred.

All15 previous archive copies /32,941 indexed files verify unchanged. Fixture
forwarding, exact payload identity, offline matcher assertions and receipt/
ledger diagnostics were checked. Initial private diagnostic errors are preserved:
the tokenizer returned a BatchEncoding instead of a list, the first proxy writer
used a JSON writer for bytes, and the first grammar-order probe incorrectly
assumed the stored fixture retained question-first order. Corrected results are
separately versioned. No fresh full-suite claim is made for this investigation;
the unchanged compact implementation's prior2,159+73 and installed67+36 results
remain historical verification evidence.

Private payloads, partial stream, receipts, phase events, queue samples, source
snapshots and all failed diagnostic attempts are archived outside Git in
`qwen-serving-trace-20261026`.
