# Local conversation verification — 2026-10-12

The maintainer explicitly authorized local model inference and subsequent bounded
testing/fixes for the conversation candidate. The corrected host binding at
`34f291e8c7f7dd3809767c2fbf518b55e50204d6` passed the complete local journey,
two further independent workflow sessions, quoted-approval denial and duplicate
approval replay. The first failing runs remain recorded below. This is live
diagnostic evidence, not production billing qualification.

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

The prepared local wheel SHA256 was
`f8ba2b0cec0a0aa5e0e07397f4813bc60ef1022acab2e68890d2b768f4ec3051`;
all 64 Lab module payloads matched the exact source. This preparation alone did
not establish that Qwen followed the improved instructions. The maintainer then
authorized further bounded local batches, without resetting earlier allowances.

## Native transport diagnosis and supported local binding

Retesting the clarified native-call instructions still blocked the 7B workflow
with zero effects. A separate public Runtime probe requested an explicit initial
native function, with two provider requests and one tool call allowed. Balanced
returned no native call and failed `tool_choice_not_honored`; strong completed
two requests, one real handler invocation and the exact final entity JSON. The
corrected public full-history `Runtime.turn()` probe likewise did not produce a
native call on the tested balanced profile. This is a result for this model/server
pair, not a claim that all Qwen Coder deployments lack tools.

A read-only audit identified oMLX 0.7.0, app build 2987, with bundled
`mlx-lm 0.31.4.dev132+g94cdcae13`. The approved 7B conversion's cached template
advertises tools and `<tool_call>` envelopes; the installed inferred `json_tools`
parser matches those delimiters. No default template/parser mismatch was found.
The installed non-streaming Chat Completions route accepts named `tool_choice`
but neither forwards nor enforces it; only `none` disables tools. The strong
probe's success therefore demonstrates actual model/native transport behavior,
not server enforcement of that requested choice. No model template, server
settings, process, credentials or SDK was changed.

The supported tested binding uses balanced for ordinary chat and tool-free
selection/confirmation interpretation, with the approved strong tier for the
effecter agent. The private diagnostic recipe explicitly sets
`"workflow_tier": "strong"`. Omission retains the previous balanced default;
there is no automatic fallback. Invalid tiers and extra configuration fields
fail before credential reads or allowance creation. The selected effecter tier
is admitted against its corresponding named `WorkflowPolicy` grant.

Conversation and workflow recorders are separate. Success requires the actual
selected profile/model, frozen attribution, complete observations, exact call IDs,
immutable workflow receipt SHA and matching provider/tool budgets. Routing to
another model or substituting another receipt's call IDs cannot qualify the test.
The host consumer's existing trusted bundle `model_tier` provides the same explicit
selection through public SDK construction; client messages cannot change it.
The installed final-wheel command also passed its documented default preflight,
reporting the explicit strong workflow tier and zero dispatches without a live flag.

## Actual successful closure at `34f291e`

The local wheel SHA256 was
`edf771f8c0f52977654388839c6f9725c064629c1adff9b76dc48f7861e0725b`.
All 64 Lab module payloads matched immutable source and installed bytes. All five
SDK wheels and import origins passed the unchanged original manifest audit.

| Actual live check | Provider requests | Result |
| --- | --- | --- |
| Complete six-case conformance schedule | 8 | Both tiers remembered Prague; balanced selection/current approval; strong native tool and final schema; one effect |
| Fresh independently recorded workflow | 4 | Selection and current approval completed; one strong native tool effect |
| Fresh quoted-approval/current-approval journey | 5 | Valid model approval proposal from quoted text denied with `confirmationRequired`; subsequent literal approval completed; one effect |
| Exact duplicate of the completed approval | 0 | Cached reply; unchanged session/workflow snapshots and receipt; no extra effect |

These successful checks contain 17 verified live requests, including three
independent workflow sessions, each with exactly one local diagnostic effect.
The complete schedule's actual case counts were `1, 1, 1, 1, 1, 3`; confirmation
reconciled one balanced interpreter request with two strong workflow requests.
The quoted case had a valid plain JSON proposal with current copied IDs, choice
`approve`, `confirmed: true` and `ambiguous: false`. The independent whole-current-
message confirmation rule denied that proposal before workflow dispatch. This
demonstrates that valid model output is not human authorization.

The independently recorded successful/guard sessions retained their private
operator snapshots and receipts. Public file-store rereads verified snapshot
integrity, exact workflow receipt equality/SHA, selected strong profile/model,
provider/tool counts and unchanged state after replay, with zero audit dispatches.
The complete standalone schedule used its documented temporary stores and closed
summary; no replacement raw evidence is invented for that removed directory.

The later batches remain distinct: the first retry batch retained its full 12
requests including failed probes; the successful full/repeat batch settled all
12 requests as known with zero unknown reservations; the guard batch retained
seven (five successful requests plus a two-request failed balanced probe), with
five remaining. Earlier failed allowances remain unchanged. Diagnostic-harness
errors (a missing import before dispatch, an unsupported legacy `cwd=None`, and
an incorrect turn-result attribute after dispatch) were corrected and retained
conservatively; they are not SDK or model regressions and supply no passing claim.

Exact-source verification passed 943 candidate tests and 921 applicable published-
baseline tests, zero failures/skips, with the existing Starlette warning. The
final source was pushed and dispatched to
[four-cell candidate run 38212165309](https://github.com/B3Cognition/prosaic-integration-lab/actions/runs/38212165309).
The original receipts and cleanup passed independent verification: all four cells,
943 source tests per cell, 1,395 acceptance executions including 475 conversation
checks, both documented demos per cell and verified cleanup. Read the
[final platform evidence](conversation-adoption-2026-10-11.md#final-source-platform-qualification--2026-10-12).
The earlier `018425b` platform qualification stays historical. CI uses synthetic
providers; the actual local Qwen evidence above is separate.
Public Runtime/Harness publication, Lab release, ordinary public-index adoption
and hosted-provider qualification remain separate pending work.
