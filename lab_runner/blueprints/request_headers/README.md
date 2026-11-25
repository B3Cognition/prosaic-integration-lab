# Per-call benchmark headers

Copy with `python -m lab_runner.blueprints copy request-headers /private/project`.
Use published Core 0.5.0 and Runtime 0.9.16. The complete Lab 0.9.8 train is
listed in its checksum-pinned release manifest. The example uses public SDK APIs.

`host.run_benchmark(runtime, agent, arguments)` and
`host.turn_benchmark(runtime, agent_or_prepared, message=...)` send
`x-tokenproxy-no-cache: 1` on this invocation's OpenAI-compatible requests.
The same option follows tool continuations. It is host configuration, never a
model-supplied field or a run tag inserted into the inputs. Ordinary calls to
the same runtime do not inherit it; supply the desired option on every call.

The installed acceptance compares actual HTTP bodies, artifact identities and
subsequent calls. Header values are not persisted as prompt/result/accounting
data. Runtime owns header validation, credentials, framing, correlation,
deadlines and call limits. The endpoint may ignore a cache hint; wire delivery
does not certify a proxy's caching behavior. Native/unified CLI and Anthropic
entry points do not support this per-call option.

To inspect the agent without a model call, run
`prosaic inspect subagents/benchmark.md --source .prosaic --json` from this folder.
The default endpoint is inert loopback port 9. Put the real model/endpoint and
credential environment reference in private `runtime.yml`, then explicitly run
`python host.py --live`. Without `--live`, the runner refuses before dispatch.
Tests use owned loopback fixtures only, with no live providers.

Tools are disabled by default. Registering a callback alone grants nothing:
the operator configuration, agent declaration and per-call policy must each
authorize a tool before it can run. Adapt this application host rather than
relaxing those SDK boundaries.
