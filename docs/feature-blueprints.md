# Feature blueprints

Every capability added to a Lab release needs a copyable host example, an
installed-SDK acceptance test and a linked guide. The release checklist and
branch review must cover all three before publication. Blueprints use public
installed APIs; the Lab never supplies a second workflow or model engine.

## Lab 0.9.13 feature map

The checksum-pinned train is Core 0.5.0, Runtime 0.9.20, Harness 0.9.14,
Runtime recorder 0.3.0 and Harness store 0.4.3.

| Capability | Copyable blueprint | What the installed test proves |
| --- | --- | --- |
| Safe tool events and captured citations | `tool-evidence` | Approved bounded display, typed results, captured selections, current permissions, durable reuse and fabricated-citation refusal on both provider protocols. [Guide](tool-evidence.md) |
| Sent reasoning-effort evidence | `sent-effort` | Actual HTTP/native controls and format, requested/default annotations, bounded retries/fallback, failure boundaries and durable file/PG no-call recovery without provider-compliance claims. [Guide](sent-reasoning-effort.md) |
| Accounting request metadata | `accounting-metadata` | Trusted run/variant labels reach prepare before dispatch, stay out of provider payloads, and remain frozen through file/PG resume and no-call receipt recovery. [Guide](accounting-request-metadata.md) |
| Per-call OpenAI-compatible headers | `request-headers` | Real HTTP receives `x-tokenproxy-no-cache: 1`; prompt bytes and artifact identity match the ordinary call; later calls do not inherit it; tool continuations retain it; unsupported transport refuses before dispatch |
| Workflow enforcement tags | `workflow-enforcement` | Content-versioned Guards inspect declared fresh accepted outputs; YAML/native and both wires prove bounded repair, cap1 refusal, human approval, version/freshness checks and file/PG no-call recovery. [Guide](workflow-enforcement.md) |
| Versioned cross-step review V1 | `revision-review` | Accepted first-review/revision dependencies limit findings to current flagged or changed IDs; bounded repair, human approval, version/freshness refusal and no-call recovery |
| Fee-format value enforcement v2 | `rule-admission` | Both synthetic wires retry invented `1.20 EUR`, `1.20 euros`, `120 cents`, then admit the supported EUR 0.40 answer; existing sign, tool and recovery checks remain |
| Effective conversation input caps | `conversation-caps` | Ordinary and interpreter caps are visible independently; real growing history stops at the tighter declared limit before another HTTP request |

```sh
python -m lab_runner.blueprints list
python -m lab_runner.blueprints copy tool-evidence /private/my-tool-host
python -m lab_runner.blueprints copy sent-effort /private/my-effort-host
python -m lab_runner.blueprints copy accounting-metadata /private/my-accounting-host
python -m lab_runner.blueprints copy workflow-enforcement /private/my-workflow-review
python -m lab_runner.blueprints copy request-headers /private/my-header-example
python -m lab_runner.blueprints copy revision-review /private/my-review-example
python -m lab_runner.blueprints copy conversation-caps /private/my-cap-example
python -m lab_runner.blueprints copy rule-admission /private/my-catalogue-example
```

The destination must not exist; copying never overwrites an application folder.
Both wheel and source archive carry the resources, including `.prosaic` files.
Copy into private application storage, then tailor the host policy and endpoint
configuration. Merely copying, inspecting or listing resources makes no model
calls. Header/review runners require explicit `--live` to execute a provider.
That option authorizes calls to the configured endpoint, so configure credentials
and budgets privately before using it. The cap CLI only inspects local bindings.

For credential-free demonstrations, obtain the matching Lab source archive and
install its exact locked dependencies and checksum-pinned SDK manifest, then run:

```sh
python -m pytest -q tests/blueprint_acceptance
```

The tests copy resources outside the package and use real public Core/Runtime/
Harness APIs with owned loopback provider fixtures. Installed qualification runs
with isolated Python on both Linux architectures; distribution checks repeat it
against wheel and rebuilt-source consumers. These are synthetic controls, not
live-provider certification or proof that a cache hint is honored by Tokenproxy.

The review policy and workflow originate in the Apache-2.0 Harness 0.9.11
[released example](https://github.com/B3Cognition/prosaic-harness/tree/v0.9.11/examples/revision-review).
Its validator uses a semantic V1 label plus the actual `checks.py` hash. The Lab
adapts its runner for isolated copy-out execution. It does not copy SDK engines.

Workflow enforcement V2 originates in the separate Harness0.9.12 example and
retains V1 above. Accounting request labels now have their own Runtime0.9.17 host and guide above. Per-call sent-effort results, a
separate repair allowance and remaining identity/publisher guarantees stay in the SDK
[Cerebro backlog](https://github.com/B3Cognition/prosaic-harness/blob/v0.9.12/docs/cerebro-requests.md).

## Existing feature families

- [Reasoning-effort agents and API/native/workflow examples](reasoning-effort.md).
- [Native and unified profile pools](unified-runtime-pools.md), including bounded synthetic fallback and no replay after partial work.
- [Guarded conversations and catalogue tools](rule-admission.md), with file/PG recovery and explicit host guard registration.
- [Conversation, interpretation and recovery](conversations.md), with trusted host identity and explicit uncertain-call handling.
- [Sandboxed tools](sandboxed-tools.md), [typed evidence](typed-handoffs.md) and [scoped memory](scoped-memory-context.md), each retaining its own verification limits.

Use each feature's guide and installed acceptance lane. New SDK versions do not
retroactively qualify historical snapshots or permit a partial upgrade of an
older Lab family. See [release scope](release-0.9.10.md) and
[release gates](release-gates.md).
