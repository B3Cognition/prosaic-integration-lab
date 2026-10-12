# Local conversation verification — 2026-10-12

The maintainer explicitly authorized local model inference for the conversation
candidate. The first bounded run verified memory and routing on both local tiers,
but the complete workflow journey has not yet passed. This is a live diagnostic
result, not a synthetic-provider or production billing qualification.

## Installed inputs and boundaries

The fresh isolated macOS ARM64 consumer used the five original SDK wheels from
the manifest with SHA256
`d5b4678788239ebf090979fcea65ee1c9774376f48b3994a4ad9cd3876b6314b`:
Core 0.4.1, Runtime 0.9.0/recorder 0.3.0 at `a59621c`, and Harness
0.8.0/store 0.3.0 at `f913fa1`. Third-party dependencies were installed from the
hash-locked requirements. Installed SDK bytes and import ownership were audited
before inference and after replacing the Lab wheel. No sibling editable SDK,
private SDK import, patched engine, hosted provider or server restart was used.

The first Lab wheel was the original qualified source `018425b`, SHA256
`b67b3200565c8448347a6d6f8bb2e8312e6269fda06299069bd77ec9c7546084`.
The later local wheel at `b8781d1a8f01fd7c6524aef5ad219b50726b9f39`, SHA256
`b9a34779d7fc10573959f9587a6d1b32628b0cd6927f46020c0842a4ab96c831`,
contained the observed formatting fix and closed failure diagnostics. All 64
Lab Python module payloads matched that immutable source and the installed wheel.
The source suite passed 930 tests, zero failures/skips, with one existing
Starlette deprecation warning. This later source does not inherit the earlier
commit's exact-source Linux qualification.

The host selected these distinct existing profiles:

| Tier | Model | Checks |
| --- | --- | --- |
| balanced | `mlx-community--Qwen2.5-Coder-7B-Instruct-4bit` | Remember Prague, recall Prague, full admitted history and matched receipt/profile/model attribution |
| strong | `ThinkingCap-Qwen3.8-27B-MLX-4bit-DWQ` | The same two-turn memory and attribution checks |

Both tiers passed, one actual provider request per turn. An authenticated model
catalogue read verified the configured names before inference. Credentials stayed
in the existing private host file; no credential, raw prompt, interaction
reference, operator snapshot or provider transcript is published here.

## Observed failures and controlled follow-up

The original fixed six-case command stopped at balanced selection, before
confirmation or any effect. Its safe summary retained four successful ordinary
cases and one failed selection reservation. Its temporary operator stores had
already been removed, so that selection's exact cause cannot be recovered.

A fresh diagnostic session used the same surviving shared allowance. Its two
ordinary turns passed, and selection returned `invalidInterpretation`. The actual
immutable interpretation receipt contained a Markdown-fenced JSON object whose
five fields, current source/reference, second choice, response and ambiguity flag
were otherwise correct. The strict admission boundary correctly rejected it.

The interpreter instructions were clarified to require one plain JSON object,
without fences, preamble or explanation. Validation, tool permissions, human
confirmation and request budgets were unchanged. The installed `b8781d1` wheel
then passed a fresh selection, reaching `confirm-b` after one request and zero
effects. A current literal `approve` was admitted by the interpreter and host
confirmation rule.

The linked workflow then blocked at its single allowed attempt. Qwen 7B returned
two JSON values in a Markdown fence: a simulated function description followed
by the expected entity result. The actual workflow receipt recorded one provider
request and zero tool calls. Harness did not accept that text as a dispatched
operation or completed workflow. The diagnostic effect count remained zero.
This qualifies neither native tool execution by that profile nor the complete
live workflow journey.

The retained fresh-session snapshots and immutable conversation/workflow
receipts were independently reread through public file-store APIs, with zero
additional dispatches. No failed session was automatically resumed, and no raw
operator evidence left the owned private run directory.

## Request accounting and next check

The same durable allowance remained in use throughout: maximum 12, retained 12,
remaining zero, three failed reservations retained as unknown. Successful cases
settled only from matching adopted receipt and recorder evidence. Failed
reservations retained their full maxima, even where a diagnostic response was
available; they were never reset or reclassified to create extra capacity.

Accounting used `MemoryRecorder` and is explicitly nondurable. Effects were
local diagnostic handlers only, with no customer or external business operation.
The first command's missing raw selection evidence and the two subsequent
failures remain part of the result. A safe failure projection now distinguishes
reply, evidence and semantic failures without exporting answers or exception
text. Synthetic regressions prove fenced interpretation fails with zero effects.

The prepared follow-up at `425093c2eddafaaad5ed53164168d094995ef43b`
clarifies that effecter agents must use the native callable interface, wait for
the actual tool result and emit only the final plain JSON object. No response
parser, SDK, validation, grant, retry or model configuration changed. Its actual
synthetic-wire regression reproduces the simulated function text and proves
blocked completion, zero effects and retention of the full unknown reservation.
The native synthetic success case still reconciles eight requests and one effect.

The complete candidate source command passed 931 tests, zero failures/skips, in
59.86 seconds. The published baseline passed 911 applicable tests, zero
failures/skips, in 34.12 seconds, excluding exactly the three functional modules
requiring the new Conversation API. Both retain the existing Starlette warning.
The first baseline command mistakenly excluded a nonexistent limits module
instead of the HTTP module and produced nine expected missing-API setup errors;
the corrected command below supplies the compatibility result.

```sh
.venv-qualified-conversation-f913/bin/python -I -B -m pytest -q -p no:cacheprovider
.venv-baseline/bin/python -I -B -m pytest -q -p no:cacheprovider tests/unit tests/functional \
  --ignore tests/functional/test_conversation_journey.py \
  --ignore tests/functional/test_conversation_conformance.py \
  --ignore tests/functional/test_conversation_http.py
```

The rebuilt local wheel SHA256 is
`f8ba2b0cec0a0aa5e0e07397f4813bc60ef1022acab2e68890d2b768f4ec3051`;
all 64 Lab module payloads match the exact source. This is preparation, not proof
that Qwen follows the improved instructions. The next bounded live check must
verify native dispatch independently of model text, final schema admission and
exactly one approved diagnostic effect. Additional requests require a separately
authorized allowance. Public Runtime/Harness publication, Lab release, ordinary
public-index adoption and hosted-provider qualification remain separate pending work.
