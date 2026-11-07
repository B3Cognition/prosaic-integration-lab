# Reasoning-effort blueprints

Current published release: **0.9.7**. See [release notes and compatible SDK versions](../../../docs/releases.md). Lab 0.9.7 qualifies Runtime 0.9.14 and Harness 0.9.10; newer SDK releases require separate Lab adoption.

Lab 0.9.4 keeps the compact shared Qwen agents and the separate Gemma medium
variant described here. The live comparisons below retain their original
0.9.3 runner/private-candidate identity; package qualification is separate.

Copy this whole directory into your project. It contains seven shared effort agents,
an explicit Gemma medium variant,
an API configuration, a native configuration and an API-backed Harness workflow.
Models and credentials belong in operator configuration, never agent Markdown.

The Lab 0.9.7 pinned SDK family uses Runtime 0.9.14 and Core 0.5.0 to inspect
and run the source. Harness 0.9.10 admits the workflow. Prose runs directly
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
prosaic-runtime subagents/gemma-medium.md --source . --config api.yml --profile gemma
prosaic-runtime subagents/none.md --source . --config api.yml --profile qwen-local
prosaic-runtime subagents/high.md --source . --config native.yml --profile claude
prosaic-runtime subagents/xhigh.md --source . --config native.yml --profile codex
prosaic-harness run workflow.yml --run-dir ./.lab/reasoning-run --input '{}'
```

Native permissions remain vendor-owned. Read-only mode is not an exact path
sandbox or a cap on vendor-internal model requests/subagents. Do not grant prose
extra tools just to enable effort. Keep ultra out of API/Claude profiles.

The default API-backed workflow uses `gemma-medium.md` with the default Gemma
profile. The seven shared effort agents retain the compact constructive CRT
prompt tested with Qwen. The Gemma variant removes the CRT procedure and uses
only the task, the full tested JSON instructions (including no fences) and the
tool prohibition. Select this
file explicitly; Runtime profiles and the Lab's multi-effort `live` command do
not automatically substitute prompts based on a model name. Its qualification
is a separate experiment; the compact shared-prompt results below do not
establish this variant's behavior.
Its completed 36-request comparison recovered all three fenced baseline answers:
usable correct JSON improved from 9/18 to 12/18, with six caps for both prompts.
All twelve completed variant answers were correct strict JSON. Earlier shared
C3 had thirteen caps, but that is historical context rather than a simultaneous
comparison. The source qualification records the failed positive-only attempt
and the final variant's limits; this is reused regression evidence.
For a Qwen workflow, select `qwen-local` as `api.yml`'s default profile and
`subagents/xhigh.md` as the workflow agent.

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

The agents constrain the returned JSON without prohibiting native thinking.
Lab 0.9.3 clarifies this wording; the change is not an established accuracy fix.
Validate task correctness independently of response shape and effort settings.

The seven shared compact effort agents supply the constructive Chinese
Remainder Theorem formula for smallest-positive solutions of pairwise-coprime
congruences, including the modular-inverse condition and positive zero handling.
It specifies that the final response starts with `{` and ends with `}`, with
exactly one integer `answer` key. These are prompt instructions, not enforced
validation or a guarantee of accuracy, completion or JSON compliance. Native
thinking still comes from the selected effort and provider capabilities.
The earlier, longer candidate improved Qwen's CRT answer and recovered two fenced
Gemma answers. Gemma also produced more capped outputs, so its usable correct
JSON rate fell from 10/18 to 9/18 at the 4,096-token limit. The compact revision
removes the general check/correct loop and duplicate verification instructions;
its shared body is 95 words instead of 169. Treat these prompts as experimental;
a smaller input does not guarantee shorter reasoning output or better accuracy.
In the compact revision's completed Gemma comparison, caps rose from 7/18 for
fresh 0.9.3 to 13/18, and usable correct JSON fell from 8/18 to 5/18. Completed
compact answers were strict JSON, but the cap-reduction goal was not met.
The source repository's `docs/verification/reasoning-prompt-compaction-2026-11-04.md`
records the exact sample and its limits.
The same compact study retained Qwen's CRT fix and corrected all three knapsack
trials, improving usable correct JSON from 9/18 to 15/18. Both Qwen prompts still
capped on all three digit-counting attempts; this is reused regression evidence,
not a general accuracy claim.
