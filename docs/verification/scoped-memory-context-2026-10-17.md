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
tests; independent review added three capacity regressions and expanded the
distribution test to nine scenarios. The final
source command was:

```text
PATH=/private/tmp/prosaic-counter-test-env/bin:$PATH /private/tmp/prosaic-counter-test-env/bin/python -m pytest -q
1289 passed, 1 existing Starlette deprecation warning, 190.05 seconds
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

Candidate `0.5.1+context.2` wheel and source archive built with
`python -m build --no-isolation`. Wheel SHA256:
`4bd4804dcf4b89fd9e5d5d6c473bd8cb6a07a1d53fc6b904f0d65ba246e56e8d`.
All 119 installed payload files matched the wheel; all 115 non-metadata payload
files also matched reviewed source. The separate candidate environment was
populated with hash-locked Lab dependencies and the five verified SDK wheels.
The SDK audit matched every payload from all five wheels.

```text
/private/tmp/prosaic-context-installed-env-2/bin/python -I -B /private/tmp/prosaic-lab-release-050/scripts/scoped_memory_smoke.py --source-root /private/tmp/prosaic-lab-release-050 --output /private/tmp/prosaic-context-installed-evidence-2
9 scenarios / 15 synthetic provider requests / 7 tools
pure preflight; network-denied replay; unchanged trace bytes
```

The smoke script's absolute source path was used from outside the checkout.
Scenarios are hostile eligible recall, populated irrelevant scope, trajectory
recall exclusion, mandatory refusal, disabled memory, repair, unknown usage,
optional context-capacity exclusion and mandatory context-capacity refusal.
Actual receipts/recorder snapshots and frozen plans are retained privately under
the output directory. Original candidate environments and historic evidence were
not overwritten.

The candidate consumer image built on Linux aarch64 from public build inputs and
verified SDK wheels, image ID
`sha256:1955026b0ea35e27a590720af3125beb6e931c62743570d2a857bd4402f79f4d`.
Imports, frozen preflight and all nine native loopback fixture scenarios passed
in its intended environment with `--network none --read-only`. The full external
database/auth/billing service acceptance lane was not rerun and is not claimed.

Private logs and build artifacts are retained under
`/private/tmp/prosaic-context-*` and `/private/tmp/prosaic-scoped-*`.
Candidate `context.1`, its environment and evidence were preserved separately.

## Independent review and decisions

The fresh whole-change review of `6044ce0..14f8987` found no Critical or Minor
issues and one Important issue: valid quotes over per-request context capacity
raised instead of producing admission refusals. Two unit regressions and a
native zero-call regression were watched failing, then passing. Assembly now
excludes oversized optional episodes and tries smaller later ones; mandatory
capacity overflow preserves evidence with a rejected frozen plan. Malformed
quotes still raise. Plan validation reconstructs the same capacity decision.
The one fix pass passed all 1,289 tests and the rebuilt installed/image checks.
No second review was substituted for those regressions.

One implementation ruling expanded assembly inputs from counter name to full
counter descriptor plus quotation identity. This detects provenance changes
under the same name; its cost is two explicit trusted host inputs.

The reviewer set aside three boundaries, retained deliberately:

- Live efficacy/refusal rates remain unmeasured in this slice. Offline contract
  readiness stands; the cost is that model benefit remains unknown until a
  fresh comparison.
- Distributed claims, malicious-host rewriting and financial-grade recorder
  durability remain outside the documented local trusted-host reference. The
  cost is no distributed, tamper-proof or billing-durability assurance.
- Full external database/auth/billing acceptance remains unclaimed. No service
  behavior changed; installed native fixtures and isolated image checks cover
  this policy. External service interactions are not newly qualified.

No deferred minor findings remain. The local branch is preserved for subsequent
comparison; no merge, push or release is included.

## Readiness

These controls are ready for a fresh comparison after review and its fix pass. They
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

The subsequent maintainer-authorized evaluation is now complete. Read the
[fresh 24-sample live result](scoped-memory-live-2026-10-17.md) for actual outcomes,
updated charged usage and next-milestone readiness. The allowances and proposed
schedule above retain this offline checkpoint's original state.
