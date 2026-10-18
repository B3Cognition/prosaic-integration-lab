# Provider-neutral response diagnostics and fault qualification — 2026-10-18

Runtime now retains bounded response and usage classifications alongside the
primary failure status. Lab qualifies the installed public contracts through
both OpenAI-compatible and native Anthropic JSON/SSE fixtures. Unknown usage
remains fenced and charged; diagnostics never grant retry authority. Memory
remains experimental. No live comparison, push or release is part of this task.

## Behavior

The additive `response_diagnostics_v1` Result metadata reports response kind,
usage state, observed HTTP status and, for fully read non-stream bodies, byte
length and SHA256. It never copies response prose, arbitrary error fields,
headers, tool arguments or response identifiers into the new contract. At most64
requests are retained per invocation: first63 plus latest, with an omission
count. RuntimeAdapter retains each delegate's diagnostics in its attempt record;
public turns and Harness receipts preserve the metadata under existing bounds.
Existing whole Result operator metadata/stderr is not made publicly safe.

An HTTP200 provider error can now remain visible as `providerError/missing`
even when the primary budget failure is `usage_unknown`. Missing, incomplete,
invalid, unsupported and conflicting usage are distinguishable observations;
the recorder remains the usage authority. Normalized known usage is retained;
missing usage stays unknown rather than zero. Encoding/response-size faults
that bypass parsing cannot silently retain a complete usage flag.

Contradictory error+tool envelopes fail before tool release. Error observations
are sticky across later stream events and include native message_start.message
envelopes. Bounded Runtime rejects invalid SSE UTF-8 before compatibility reader
replacement; the base legacy provider parser is unchanged. This intentionally
rejects malformed streams that could previously survive replacement.

Harness required no code change: installed receipt and network-denied recovery
checks demonstrate preservation through its existing Result contract. Core and
both database adapters are unchanged.

## Frozen candidates and evidence

- Runtime `0.9.8+diagnostics.1`, executable source
  `21cca3f6cdcebb1d264a31e209af70b2c9249ec2`; later qualification commit
  `2148b08` changes four private-version gate expectations only. The installed
  payload matches both the immutable source and current executable files.
- Lab `0.5.1+diagnostics.1`, source
  `d7fe9097278db714d98a33d8695cd3678929e258`. Memory policy/prose remains unchanged.
- `dependencies/response-diagnostics-candidate.json`, SHA256
  `0d204d48743b456f82571cb85f8027d0e8589bd1ab7e777307395e5510d4396f`,
  pins the private Runtime wheel plus four unchanged public SDK wheels. Packaged
  experimental provenance binds it. Active releases and all prior candidate
  manifests/evidence remain unchanged. Private wheels require the operator's
  verified local wheel cache; this is not a public-index release manifest.
- Runtime wheel SHA256
  `43f29698a503f867e5d39b3ef6c31cdb066dc0ae0d4712d3ec67e0561603eb7e`;
  Lab wheel SHA256
  `6a7f42f5cf5da399f5b46a8d6d1cdd0149db080c8f7662a1cb712bd46444684e`.

The [structured qualification](data/response-faults-2026-10-18.json) records source
suite counts, skips, artifact hashes, review closure and earlier failed test
names. The [private preservation receipt](data/response-fault-preservation-2026-10-18.json)
records the immutable archive hash without publishing raw run evidence.

Installed qualification on macOS ARM64/Python3.12.14:

Full source suites: Runtime **1,345 passed, 2 skipped** on Python3.11.15;
Lab **1,333 passed** on Python3.12.14, with one existing Starlette/httpx warning.
The Runtime skips are the framework-Python test and the separately mandatory
installed-wheel metadata gate; that installed gate passed independently below.

- 57 passed: all 56 diagnostic regressions plus installed-wheel ownership/version
  gate. Source Runtime is separately checked on Python3.11.15.
- 36 fault/replay scenarios, 18 per native wire format, under unchanged sample
  caps4requests/2tools/8192tokens/600seconds/output512. Healthy JSON/SSE,
  missing/incomplete/invalid usage, provider errors, contradictory envelopes,
  malformed/duplicate JSON, invalid encoding, rejected redirects/non-2xx and
  unknown usage after a successful lookup are exercised. The36cases make42
  synthetic fixture requests and6tool calls; none is live model inference.
- 14 continuation-budget scenarios and 10 legacy scoped-memory/replay scenarios.
  All use installed SDK/Lab code, synthetic loopback providers and no credentials.
- All five SDK wheel payloads, Runtime's 51 source files and Lab's 115 source files
  match their frozen bytes; dependency consistency and no-Node wheel smoke pass.
- Receipt recovery uses copies with networking denied; copied receipt bytes,
  returned receipt digests and original traces/evidence are unchanged. Unknown
  failures stop without another provider call; known permanent errors stop
  without executing contradictory tools.

To repeat the fault lane in an isolated installed candidate environment:

```sh
python -I scripts/response_fault_smoke.py --source-root "$PWD" \
  --output /absolute/private/fresh-response-fault-output
```

The output must be fresh. Do not reuse historical live evidence or interpret
synthetic counters as qualification of a real provider tokenizer.

## Review and qualification corrections

One independent whole-branch review found no Critical issue, two Important
stream-error variants, and three smaller classification/replay gaps. All five
were addressed within this requested acceptance scope. The Runtime regressions
were observed failing, then passing; replay assertions were strengthened.
The reviewer independently rechecked four
stream regressions and confirmed no remaining finding in the fix pass.

Earlier failed setup/operator/test attempts are retained, not erased. Runtime's
private version needed alignment in module/metadata/conformance/wheel gates;
historical result golden fields remain compared unchanged after excluding only
the new additive metadata. Lab's first45failures combined SDK provenance and
source-environment mismatches; after binding provenance, two source-isolation
tests still rejected an installed-Lab environment. A separate SDK-only source environment and explicit candidate
provenance fixed those setup mismatches. Python3.11 was correctly rejected by
Lab's3.12floor; source build reused the existing qualified build environment.
One targeted Runtime invocation lacked fixture socket permission; the corrected
invocation passed all61tests. Failed setup logs remain part of the archive.
The scripted SSE fixture was corrected to emit delta without a duplicate message
container, and permanent known errors were correctly expected to stop after one
request. None of these corrections tuned a live model, task or held-out case.

## Limits and readiness

Zero new live dispatches. The35canonical live ledgers still charge1,456requests /
595tools /1,752,686tokens against unchanged ceilings1,475 /604 /1,976,623.
Remaining19requests /9tools /223,937tokens; all eight unknown reservations remain
charged. Prior428comparison,282continuation and338latest comparison evidence
files remain unchanged. A future live run must recheck current serving/counter
assets and fit full reservations within that allowance; eight more fully reserved
samples would not fit. This task does not authorize or dispatch another run.

The private archive contains676files, SHA256
`bcdd2f0e7c50fff5fb812f43cf919f757e3a5a9b9893ab24263bf161fa95bc45`.

Offline fault qualification makes the next bounded live comparison reviewable.
It does not certify a live provider, recover the old unknown HTTP200 response,
prove memory efficacy, or constitute cross-platform/database release acceptance.
Keep Lab memory experimental. Broader task families and providers remain later
evaluation work, rather than more tuning for one local backend/model pair.
