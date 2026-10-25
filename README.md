# Prosaic integration lab

Write an agent in Markdown, run it with a model, and put it inside a workflow
that your application can authorize, pause for review and resume. This Lab shows
how the Prosaic ecosystem fits together through runnable examples and tests.

**Start here: [the guided quickstart](docs/quickstart.md).** Your first result
needs Python 3.12 and internet access for installation. It needs no model
account, API key, local model or Docker.

## What can I try?

| I want to… | Start here | Requirements / what happens |
| --- | --- | --- |
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

**Lab [0.7.0](docs/release-0.7.0.md)** consumes **Runtime 0.9.8**, Core 0.4.1,
Harness 0.9.4, Runtime recorder 0.3.0 and Harness store 0.4.0. It includes Explorer,
the guided onboarding and the first-workflow example. Earlier release artifacts
retain their original bytes.

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

Start with [common first-run problems](docs/quickstart.md#when-something-goes-wrong).
Then use the [consumer guide](docs/consume-native-workflows.md),
[unified pool contracts](docs/unified-runtime-pools.md),
[conversation API](docs/conversations.md) or
[benchmark protocol](docs/realistic-runtime-benchmark.md).
The [optional capability guide](docs/quickstart.md#optional-capabilities) links
memory, tool approval, failure isolation and evaluation examples with their limits.

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
