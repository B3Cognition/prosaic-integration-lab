# Scoped context qualification — 2026-10-17

The opt-in Lab policy selects memory using trusted scope/freshness metadata and
admits whole optional episodes against an enforced trajectory plan. Core,
Runtime and Harness source, model prompts/settings, old history bytes and live
limits are unchanged. This is an offline qualification milestone; it makes no
claim of improved live model accuracy.

Source verification on macOS arm64 / Python 3.12.14 used the existing installed
public SDK candidate family: Core 0.4.1, Runtime 0.9.7+budget.3, Harness 0.9.0,
Runtime PostgreSQL recorder 0.3.0 and Harness PostgreSQL store 0.4.0. SDK manifest
`dependencies/budget-candidate.json` SHA256 is
`a50422bfda63b43ab99d3736f0613b25bb9dd33f298862caa2f14388d6c63e96`.
The released dependency manifest is unchanged.

Watched regressions preceded implementation. Task 1 passed 20 scoped retrieval
tests; Task 2 passed 23 planning/counter tests; Task 3 passed 13 native/recovery
tests; the distribution test exercised seven additional scenarios. The final
source command was:

```text
PATH=/private/tmp/prosaic-counter-test-env/bin:$PATH /private/tmp/prosaic-counter-test-env/bin/python -m pytest -q
1286 passed, 1 existing Starlette deprecation warning, 188.64 seconds
```

Coverage includes populated but irrelevant tenants, exact entity/topic filtering,
foreign-change invariance, current-reference invalidation, expiry/future notes,
hostile eligible prose, owned data, stable whole-episode packing, invalid quotes,
full retry headroom, unchanged mandatory evidence, rejected mandatory plans,
input/output/proposal guards and both OpenAI-compatible/Anthropic native guard
boundaries. These synthetic counters report fixture units, not live tokenizer
qualification. Earlier qualified local counters remain available unchanged.

Real public Runtime/Harness fixtures verify known zero-call mandatory refusal,
shared guard state across repairs, honest unknown usage, interrupted receipt
adoption and receipt-only recovery. The first recorder integration exposed a
missing Harness accounting attachment; attaching the same public recorder to
both products restored validated lineage and accurate native receipt counters.
An oversized continuation is terminal before its HTTP request; the prior paid
request and usage remain in evidence. No proposal count is used as dispatch.

Candidate `0.5.1+context.1` wheel and source archive built with
`python -m build --no-isolation`. Wheel SHA256:
`9696678fb306a79a5d9e4456b3a4b83494c44a8b7f42fad62c0b61a14ee7bf92`.
All 119 installed payload files matched the wheel; all 115 non-metadata payload
files also matched reviewed source. The separate candidate environment was
populated with hash-locked Lab dependencies and the five verified SDK wheels.
The SDK audit matched every payload from all five wheels.

```text
/private/tmp/prosaic-context-installed-env/bin/python -I -B scripts/scoped_memory_smoke.py --source-root /private/tmp/prosaic-lab-release-050 --output /private/tmp/prosaic-context-installed-evidence-1
7 scenarios / 13 synthetic provider requests / 6 tools
pure preflight; network-denied replay; unchanged trace bytes
```

The smoke script's absolute source path was used from outside the checkout.
Scenarios are hostile eligible recall, populated irrelevant scope, trajectory
recall exclusion, mandatory refusal, disabled memory, repair and unknown usage.
Actual receipts/recorder snapshots and frozen plans are retained privately under
the output directory. Original candidate environments and historic evidence were
not overwritten.

The candidate consumer image built on Linux aarch64 from public build inputs and
verified SDK wheels, image ID
`sha256:5826f4551e6aa1edf3c9767d5dd899a31493bfd40e1a24942880c14098402b9d`.
Imports and frozen preflight passed in its intended environment with
`--network none --read-only`. This is an image/preflight check; the full external
database/auth/billing service acceptance lane was not rerun and is not claimed.

Private logs and build artifacts are retained under
`/private/tmp/prosaic-context-*` and `/private/tmp/prosaic-scoped-*`.
The fresh whole-change review is recorded separately after this verification.

## Readiness

These controls are ready for a fresh comparison after final code review. They
address retrieval scope, context admission, portable trajectory evidence and
safe recovery. They do not establish memory benefit for either model, semantic
retrieval quality, distributed write governance or production certification.
A legitimately scoped hostile note remains untrusted model input.

No new live inference occurred. Cumulative charge remains 1,363 provider
requests / 547 tools / 1,621,526 tokens, including all seven unknown reservations.
Ceilings remain 1,475 / 604 / 1,976,623; remaining allowance is 112 / 57 / 355,097.
Case caps remain 4 requests / 2 tools / 8,192 tokens / 600 seconds, output 512.

The next useful evaluation is 24 fresh held-out typed-evidence samples: six
families, both models, memory on/off. Its full reservations are 96 requests /
48 tools / 196,608 tokens, within current allowance. Author fresh current cases
after freezing implementation; include populated irrelevant scope, changed
registry, eligible hostile recall and near-limit mandatory context. Report
selection quality, admitted/refused continuations, task success, repairs and
actual/unknown usage separately. Do not tune on or relabel the previous held-out
set. Broader multi-agent or distributed-memory milestones should follow this
measurement rather than assume that narrower recall improves answers.
