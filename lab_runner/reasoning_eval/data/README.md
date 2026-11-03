# Reasoning-effort blueprints

Copy this whole directory into your project. It contains seven canonical agents,
an API configuration, a native configuration and an API-backed Harness workflow.
Models and credentials belong in operator configuration, never agent Markdown.

The required Runtime version is 0.9.12 or later in the 0.9 series. Core 0.4.1
inspects the source. Harness 0.9.4 can admit the workflow. Prose runs directly
through Runtime; these examples do not copy files into Claude/Codex directories.

| Profile | Efforts supported by the exact example model |
| --- | --- |
| Gemma | none, low, medium, high, xhigh, max; positive levels share one on switch |
| Local ThinkingCap Qwen / Qwen 3.8 Max | none, low, medium, xhigh |
| DeepSeek V4 Pro | none, low, high, max |
| Nemotron NIM | low, medium, high |
| Claude native | detected from the selected model/client; no canonical none/ultra |
| Codex native | detected from the selected model/client; ultra only when advertised/supported |

Profile labels are examples, not hosted endpoints. Set each API URL/model to the
server that actually serves it. The verified local model was **Gemma 4**, served
as `gemma-4-31B-it-oQ4e-mtp`; a server called "Gemma 4.1" needs its actual model ID
or an explicit trusted capability declaration. Never infer tiers from its label.

Set `REASONING_API_KEY` privately if authentication is required; for a server
without authentication remove `api_key_env`. Do not insert the key in YAML.

From the copied directory, inspect without execution:

```sh
prosaic inspect subagents/medium.md --source . --json
prosaic-harness validate workflow.yml
```

These commands make real inference calls after configuration and authentication:

```sh
prosaic-runtime subagents/medium.md --source . --config api.yml --profile gemma
prosaic-runtime subagents/none.md --source . --config api.yml --profile qwen-local
prosaic-runtime subagents/high.md --source . --config native.yml --profile claude
prosaic-runtime subagents/xhigh.md --source . --config native.yml --profile codex
prosaic-harness run workflow.yml --run-dir ./.lab/reasoning-run --input '{}'
```

Native permissions remain vendor-owned. Read-only mode is not an exact path
sandbox or a cap on vendor-internal model requests/subagents. Do not grant prose
extra tools just to enable effort. Keep ultra out of API/Claude profiles.

Keep `.lab/` ignored in the consuming project's Git configuration before running
the workflow; run state is private host data. The Integration Lab already ignores
that directory. Use a fresh run directory when changing admitted prose/config.

Omitting `effort` uses the profile default. Explicit prose overrides that default;
unavailable efforts fail rather than being silently lowered. Unknown aliases may
need a trusted `supported_efforts` or `reasoning_effort_format` declaration.

For bounded multi-effort runs and sanitized receipts, follow the Integration Lab
[reasoning guide](https://github.com/B3Cognition/prosaic-integration-lab/blob/main/docs/reasoning-effort.md).
A correct arithmetic response alone does not establish that a server honored its
thinking setting. Gemma has no distinct positive effort budgets; model quality
and request-control verification must be evaluated separately.
