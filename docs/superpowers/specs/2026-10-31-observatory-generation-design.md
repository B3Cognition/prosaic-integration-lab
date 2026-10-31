# Observable generation in the execution Observatory

The maintainer asked to implement visible token generation in both Observatory
views, research what matters, and choose another local model if useful. The
current 0.8.0 scene animates requests but disables streaming and receives only
terminal usage. This work implements actual output arrival, not a decorative
token counter. Implementation proceeds inline in the existing isolated worktree.
No new merge or release is part of this request.

## Research and design decisions

- NVIDIA's [inference guide](https://developer.nvidia.com/blog/llm-benchmarking-fundamental-concepts/)
  separates waiting for the first output from subsequent generation. A stream
  chunk may contain multiple tokens. Input size, first output, output cadence and
  end-to-end duration answer different questions.
- [AIPerf's metrics reference](https://github.com/ai-dynamo/aiperf/blob/main/docs/metrics-reference.md)
  explicitly distinguishes first visible output, inter-chunk intervals and
  token rates. Client arrivals include transport/processing; they cannot isolate
  queue time, prefill, GPU work or internal reasoning.
- [W3C pause/stop/hide](https://www.w3.org/WAI/WCAG22/Understanding/pause-stop-hide/)
  supports a visible pause control and reduced-motion presentation.

The screen's question is: **Is the model producing output, and where is time
being spent?** The largest new element is an output stream with arrival marks
and a cumulative character curve, not another row of numeric tiles. Colour
keeps its existing meaning: teal for provider output, coral for Runtime, gold
for tools. Keep the Blender asset and existing typography and stack. This is a
component extension, not a dashboard redesign; no new frontend dependency.

Live shows request travel toward the provider, then distinct returning bursts
driven by observed text deltas. A generation panel shared by both views shows
the selected provider call, a bounded provisional text ribbon, arrival marks,
a cumulative step curve, first visible output delay, chunk count and largest
gap. Long gaps remain visible. Inspect supports selecting a provider call and
scrubbing/replaying its arrivals. No particles or output increments are emitted
for empty role/usage frames. Finished runs retain a clear Replay action.

Data labels say **chunks**, **characters** and **first output**. Provider-reported
input/output token totals remain separately labelled and recorder-backed. There
is no fabricated per-token precision, tokens/s, server prefill split, cost,
progress percentage or reasoning display. A nonstreaming response explicitly
says generation timing is unavailable. Missing and truncated data remain visible.
Samples are clearly synthetic and use deterministic arrival timestamps.

## Public API and ownership

Use the installed public Harness `Conversation.send(on_event=...)` and Runtime
observer. Do not patch SDKs, copy execution engines, add upstream releases or
change any SDK pin. The Harness forwards ordinary provisional text events and
withholds interpreter output; the existing observer supplies provider start/end
and invocation identity. Correlate a delta only with the single open provider
request in that owner/session's sink. Never guess if zero or multiple are open.

Add an optional boolean `streaming` to host conversation bundle configuration,
default false. Only the Observatory launcher selects true and includes that
choice in its retained binding version. Chat and ordinary service defaults stay
compatible. The local gateway forwards bounded SSE transparently when selected,
preserving its shared 1–128 request allowance, loopback restriction, private key,
no redirects, no retries, browser-dispatch denial and response size/time limits.
The owned synthetic conversation provider supports properly terminated SSE with
tool deltas and final usage. Its default JSON path and accounting counts stay
unchanged. Model execution remains initiated by the Runtime.

Extend the optional in-memory sink with a separate `generation` projection.
Existing `events` remain metadata-only with their original allowlist. Generation
contains provider-call identity, actual monotonic arrival times, counts, a
bounded provisional ordinary-output preview and bounded samples. No prompts,
tool arguments, reasoning, credentials or raw provider envelopes are stored.
Owner/grant filtering applies before returning the projection through the
existing protected observations endpoint. Preview is explicitly provisional and
does not imply acceptance, durable history, successful completion or accounting.

Bounds: at most 32 retained provider streams per run, 512 timing samples and
4,096 preview characters per stream; retain cumulative counters and explicit
truncation when bounds are reached. Overall existing run/event caps remain.
Best-effort generation capture must never fail or redispatch execution. A
finished/failed invocation closes incomplete streams without asserting success.
No preview from a buffered `text` callback is exposed as streamed output.

## Verification and delivery

Tests must first fail for missing capture, actual stream delivery and the UI's
timing derivation. Cover owner isolation, no interpreter/tool/prompt leakage,
buffered responses, empty chunks, multiple provider calls, truncated streams,
single-chunk rates, pause/replay, missing usage and reduced motion. Verify both
views in a real browser at desktop/tablet/phone sizes. Run the full Python suite,
Node regressions, source asset guard, build and isolated source distribution
checks. Exercise the actual owned PostgreSQL stack and a bounded live local
model with public SDKs; retain only sanitized evidence and clean owned resources.
Keep released 0.8.0 bytes and historical evidence untouched.
