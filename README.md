# Prosaic integration lab

Lab **0.9.13** adds safe tool events and captured citations with Runtime **0.9.20**,
Harness **0.9.14** and store **0.4.3**. See [release notes](docs/release-0.9.13.md).

Release train: **0.9.13**, with Runtime **0.9.20**, Harness **0.9.14** and Harness PostgreSQL **0.4.3**. See [release notes and compatible SDK versions](docs/releases.md).

[Context-pack acceptance](docs/context-packs.md) now runs in the normal released-SDK
matrix. It checks per-agent defaults, workflow-node overrides, accepted-record
evidence, deferred reads and recovery using owned synthetic fixtures.

Write an agent in Markdown, run it with a model, and put it inside a workflow
that your application can authorize, pause for review and resume. This Lab shows
how the Prosaic ecosystem fits together through runnable examples and tests.

Lab **0.9.11** adopted **Core0.5.0, Runtime0.9.18 and Harness0.9.12**,
with the original recorder0.3.0/store0.4.1 public bytes. The copyable
[sent-effort blueprint](docs/sent-reasoning-effort.md) reports exact encoded HTTP
controls or launched native effort argv, separately from artifact requests and
profile defaults. Retries and fallback keep bounded evidence; sent never proves
provider compliance. Earlier blueprints and input identities stay unchanged.
See [all feature blueprints](docs/feature-blueprints.md),
[release scope](docs/release-0.9.11.md) and
[qualification](docs/verification/sent-effort-2026-11-08.md).

Lab **0.9.10** added [accounting metadata](docs/accounting-request-metadata.md):
trusted run/variant labels reach `prepare(intent)` before dispatch and remain
frozen on resume. Existing workflow enforcement, per-call headers, versioned
review V1, fee guards and conversation-cap blueprints remain available.

Lab **0.9.4** keeps the compact Qwen/shared
[reasoning-effort blueprints](docs/reasoning-effort.md) and adds a separate,
simpler Gemma prompt with the tested JSON rules. The example Gemma workflow
selects that file explicitly; native effort mappings and prompt bytes are unchanged.
See [release scope and qualification](docs/release-0.9.4.md).

**Start here: [the guided quickstart](docs/quickstart.md).** Your first result
needs Python 3.12 and internet access for installation. It needs no model
account, API key, local model or Docker.

## What can I try?

For the unpublished optional audit candidate, see
[host-resolved evidence fixtures and application boundaries](docs/answer-span-resolved.md).
Memory and SUE remain disabled by default.

| I want to… | Start here | Requirements / what happens |
| --- | --- | --- |
| Copy accounting labels, headers, cross-step review and cap hosts | [Feature blueprints](docs/feature-blueprints.md) | Published SDKs, offline copy and synthetic acceptance; live calls require opt-in |
| Check reasoning effort and copy provider/workflow blueprints | [Reasoning-effort lab](docs/reasoning-effort.md) | Separate control-test lane on Runtime 0.9.20; fixtures need no key; bounded live calls require opt-in |
| Enforce workflow tags over accepted first-review/revision outputs | [Workflow enforcement](docs/workflow-enforcement.md) | Content-versioned Guard, bounded repair, human acceptance and no-call recovery |
| Enforce tagged prose rules directly or through Harness and copy the blueprint | [Rule-admission blueprint](docs/rule-admission.md) | Complete Core 0.5.0, Runtime 0.9.20 and Harness 0.9.14 train; both synthetic provider wires, no live calls |
| Explore the ecosystem visually | [Prosaic Explorer](docs/explorer.md) | Interactive component maps, user/developer explanations and eight offline playback scenarios; bounded live runs opt-in |
| Understand how an agent becomes a workflow | [First workflow](docs/quickstart.md#1-build-your-first-workflow) | Public SDKs validate a workflow and prepare inputs; no execution |
| See Claude → Codex → local fallback | [Fallback walkthrough](docs/quickstart.md#2-see-safe-fallback-without-model-accounts) | Owned fake CLIs and loopback HTTP fixtures; no real providers or Docker |
| See a workflow execute, pause and resume | [Service demo](docs/quickstart.md#3-run-the-service-or-open-the-browser) | Docker, owned PostgreSQL and synthetic model responses |
| Chat and approve a workflow in a browser | [Browser demo](docs/quickstart.md#3-run-the-service-or-open-the-browser) | Docker; scripted by default, local Qwen optional |
| Run my Markdown through real providers | [Connect models](docs/quickstart.md#4-connect-real-models-explicit-opt-in) | Authenticate your profiles, choose permissions and set budgets |
| Compare providers on the same work | [Benchmark](docs/quickstart.md#5-compare-your-models) | Explicit live opt-in; same tasks/inputs; default 180s or explicit 240s local deadline |
| Embed this in my application | [Integration map](docs/quickstart.md#6-integrate-the-pieces-in-your-application) | Minimal example, public SDK APIs and host responsibilities |

The chat browser demo currently uses scripted or local/API responses. Unified
Claude/Codex/local pools are available through the Runtime Python API and CLI,
with separate Lab tests and benchmarks. Explorer adds dedicated single-agent
pool controls; the chat/workflow browser remains a separate service.

## Which package does what?

| Component | Responsibility | Your benefit |
| --- | --- | --- |
| **Core** | Parse, inspect and distribute canonical Markdown | Keep agent instructions separate from execution bindings |
| **Runtime** | Execute agents, enforce execution policies and select eligible profiles | Use Claude Code, Codex CLI or local/API models through explicit policies |
| **Harness** | Execute admitted workflows, pause and resume | Add structured human review and retained workflow state |
| **PostgreSQL adapters** | Store workflow state and usage evidence | Resume across replicas and inspect attributed usage |
| **Integration Lab** | Example application, fixtures, acceptance and benchmarks | See executable integration patterns before building your own |

Your application owns identity, authorization, tools, endpoints and billing
attribution. A Markdown instruction is not permission to access a tool or file.

## Current releases and what is new

Lab **[0.9.13](docs/release-0.9.13.md)** supplies the current SDK train with
a [feature-to-blueprint map](docs/feature-blueprints.md). Use
`python -m lab_runner.blueprints list` and `copy NAME DESTINATION` to obtain
complete examples from an installed wheel. Both active manifests retain exact
public URLs, SHA256 hashes and source commits. Prior manifests, provenance and
freezes are archived unchanged; partial mixtures still refuse admission.
The full ordinary, guarded/feature and reasoning matrix remains mandatory.
Historical release artifacts and live evidence keep their original bytes.

After the [quickstart installation](docs/quickstart.md#setup-once), open the
visual guide with `python -m lab_runner.explore`. The default launches documentation
and playback without Docker, Node or model credentials. See the
[Explorer guide](docs/explorer.md) to enable explicit, budgeted live controls.

- Unified ordered pools combine native Claude/Codex profiles and local/API
  profiles. Eligible members are selected before work starts.
- Confirmed pre-work quota rejection can switch providers; cooldowns persist.
  Partial/uncertain work, authentication errors and timeouts stop instead of
  automatically replaying work. If all members are cooling down, Runtime returns
  `capacity_unavailable` and the earliest retry time.
- Permissions and budgets stay explicit. Native permissions and API tool/file
  grants are separate; API token limits do not bound native subscription spend.
- The standalone evaluation CLI works from installed wheels without repository
  `scripts`. The unified benchmark local timeout remains configurable
  within 1–300s, default 180s; native 60s/pool 300s ceilings remain fixed.

[Release 0.7.0 verification](docs/verification/release-0.7.0-2026-10-25.md)
records four green CI cells, original CI artifacts and matching anonymous
downloads. Clean public-wheel and rebuilt-source installs with Runtime 0.9.8
each passed 51 standalone fixtures, 3 deadline checks and 10 browser checks.
Installed visual docs/playback and bounded synthetic live controls passed,
including duplicate protection, cancellation and blocked admission across
restart, with cleanup verified and zero real model calls.

The latest [live study](docs/verification/unified-cli-lab061-local240-2026-10-25.md)
passed 9/9 tasks per backend, with median latencies Claude 10.86s, Codex 21.73s
and local 62.37s. It used identical neutral Markdown/inputs and a disclosed
Lab 0.6.1 private 240s driver. It is separate from release fixture qualification;
small studies do not establish general model quality rankings.

## Troubleshooting and deeper examples

The source-only [execution Observatory](prototypes/observatory/README.md) adds a
3D Flow view and an Inspect timeline for actual conversation/provider/tool events.
Use its owned-stack launcher from a checkout or complete source archive. The
Observatory was introduced in 0.8.0; 0.9.0 adds actual output arrivals, generation
charts and pause/replay in both views. Version 0.9.1 starts idle, discovers your
captured Lab runs automatically, restores the exact browser principal, and makes
scripted demos explicit. Published earlier artifacts remain unchanged.

Start with [common first-run problems](docs/quickstart.md#when-something-goes-wrong).
Then use the [consumer guide](docs/consume-native-workflows.md),
[unified pool contracts](docs/unified-runtime-pools.md),
[conversation API](docs/conversations.md) or
[benchmark protocol](docs/realistic-runtime-benchmark.md).
The [optional capability guide](docs/quickstart.md#optional-capabilities) links
memory, tool approval, failure isolation and evaluation examples with their limits.

For the independent Prosaic Castle fork, start with the
[enable/use guide](docs/prosaic-castle.md). Memory and SUE are independently
opt-in and remain disabled by default. The [Castle quickstart](docs/castle-quickstart.md)
retains the historical package profile and evidence.

The experimental [own-data memory benchmark](docs/memory-benchmark.md) adds
frozen datasets, file-search/FTS/expanded comparisons, optional bounded
completeness review, strict external adjudication and offline replay. Larger
corpora do not increase per-task context; fixture success is not quality evidence.
Memory and review remain disabled by default, and live constrained generation
requires the separately qualified SDK candidate described in that guide.

The optional [answer-span audit](docs/answer-span-audit.md) checks actual answer
wording against frozen source requirements, citations and status. Its explicit
loopback fixture covers omissions, complete answers, unavailable context and
unknown usage. It preserves the original answer and adds no automatic repair.

The separately opt-in [SUE review guide](docs/sue-review.md) shows a
credential-free requirements-review walkthrough, frozen sources, approval and
recovery with the lightweight engine. Review stays **off by default**, independent
of Castle memory; its reports are advisory and do not certify correctness.
The separate [requirements comparison](docs/requirements-review-eval.md) exercises
direct, critic-author and SUE strategies against frozen synthetic cases while
preserving the original hackathon grader and retrieval checks.

## Install packages for an embedding service

See [the integration map](docs/quickstart.md#6-integrate-the-pieces-in-your-application)
and [the detailed package recipe](docs/reference-guide.md#install-packages-for-an-embedding-service).

## Try the native workflow

See [the guided service demo](docs/quickstart.md#3-run-the-service-or-open-the-browser).
Here "native workflow" means a Harness workflow admitted by the host, not a
Claude Code or Codex CLI backend.

## Try a conversation and an approved workflow

### Converse in the browser

See [the browser walkthrough](docs/quickstart.md#3-run-the-service-or-open-the-browser).

### Retained candidate recipe

See [the historical candidate recipe](docs/reference-guide.md#retained-candidate-recipe).

## Follow the integration

See [host and SDK responsibilities](docs/quickstart.md#6-integrate-the-pieces-in-your-application).

## Other demonstrations

See [optional capabilities](docs/quickstart.md#optional-capabilities) and
[the retained demonstration index](docs/reference-guide.md#other-demonstrations).

## Run the required acceptance gates

See [the complete acceptance recipe](docs/reference-guide.md#run-the-required-acceptance-gates).
First-run fixtures do not replace the required Linux/database matrix.

## Historical release and operations

The [retained operational reference](docs/reference-guide.md) preserves previous
README recipes and historical release checkpoints. [Current status](docs/current-status.md)
and individual verification ledgers identify their exact versions and scope.

## License

Apache-2.0. See [LICENSE](LICENSE).

## Experimental agent quality and retrieval memory

See [the optional capability guide](docs/quickstart.md#optional-capabilities).
Memory and correction remain experimental and opt-in.

The `tool-evidence` lane demonstrates safe tool events and
captured citations with exact paired Runtime/Harness artifacts. It runs 12 logical
cases on both provider protocols (24 required cases), with separately owned
PostgreSQL 16/18 storage. See the [copyable host](lab_runner/blueprints/tool_evidence/README.md).
The released lane joins every ordinary architecture/database cell. See the
[tool-evidence guide](docs/tool-evidence.md); archived candidates retain separate lineage checks.
