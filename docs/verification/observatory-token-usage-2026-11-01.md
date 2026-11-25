# Observatory real-model token usage — 2026-11-01

Unreleased follow-up on `codex/observatory-token-usage`, based on merged 0.9.0
main `9879e108c9fb77a892dae998fe0f449abf027f88`. The maintainer requested actual
token counts in both views. Published 0.9.0 artifacts and tags remain immutable.

## Root cause and fix

Two explicitly bounded local wire probes confirmed final usage objects with
actual integer counts. A completed pre-fix demo retained 533 input / 111 output / 644 total
tokens in its recorder, but its measurement was `quarantined` and usage status
`untrusted`. oMLX prepends a zero-content SSE heartbeat whose model is
`keepalive`, then emits the actual model name. The installed recorder correctly
detects conflicting model metadata. The installed oMLX `server.py` heartbeat
implementation and the second wire probe (two distinct model names, one response
ID and one usage event) independently identified that cause.

The Lab-owned local gateway now translates only the closed, empty oMLX
heartbeat shape into an SSE comment. It preserves other frames byte-for-byte,
including actual model changes, usage, content, tool calls, unknown fields,
duplicate keys and malformed events. It supports fragmented UTF-8 and LF/CRLF,
emits complete events incrementally and retains the original raw 8 MiB / 30-second
bounds, shared request cap and no-retry behavior. SDK code, recorder trust rules,
old observations and model-server configuration are unchanged.

## Regression evidence

- Real loopback provider → gateway → released Runtime → actual MemoryRecorder
  reproduced the bug before implementation: two known-heartbeat cases failed
  because valid unsupported usage became untrusted; six controls passed.
- After the fix, 51 focused gateway/recorder/projection tests passed. They cover
  byte fragmentation, Unicode, line endings, early delivery and adversarial
  heartbeat lookalikes. Genuine metadata/usage conflicts stay untrusted and are
  excluded from diagnostic counts.
- All 25 Observatory JavaScript regressions and the source guard passed; the
  existing 23 vendor files and GLB digest are unchanged.
- A read-only focused review found no Critical/Important blockers or material
  Minor findings; 43 gateway/new usage tests passed independently.
- `.venv/bin/python -m pytest -q`: 2,072 passed, one existing Starlette/httpx
  deprecation warning, 590.71 seconds. This run used the loopback access required
  by the fixtures. `git diff --check` passed.

## Actual local-model verification

An immutable consumer built from this fix has ID
`sha256:889e830e00c5970178fbed83250063709f326563d7ae696e8a2ebdd4681b459b`.
The unchanged SDK train is Core 0.4.1, Runtime 0.9.8, recorder 0.3.0, Harness 0.9.4
and store 0.4.0; manifest SHA-256 remains
`36eec99280acb8688d2496f704f4445b59c3ff269fc506a83d6e7fe83bc92698`.

A fresh owned PostgreSQL 16 preview used the existing local
`ThinkingCap-Qwen3.8-27B-MLX-4bit-DWQ` with a hard four-request gateway allowance
and no retries. One request completed: 36 ordinary output chunks, 71 characters,
first output 4.77 seconds after provider start, largest gap 616 ms, invocation 14.6 s.
The public recorder API and owner-authorized observations agree exactly:

| Evidence | Result |
| --- | --- |
| Input tokens | 533 |
| Output tokens | 98 |
| Total tokens | 631 |
| Cached input / reasoning output | 528 / 28 |
| Recorder measurement / usage status | unsupported / unsupported |
| Provider diagnostic unknown calls | 0 |
| Qualified accounting totals | remain unknown |

Live shows 631† reported tokens and 98† output tokens. Inspect shows 533 input,
98 output and 631† total. Pausing at 8 seconds changes visible chunks to 11 while
the latest actual token totals stay 631. Both views were inspected in the real
browser; Replay consumes no new model request. The dagger remains explicit:
oMLX timing extensions are unsupported for accounting, so these are actual
provider-reported diagnostic counts, not newly qualified billing evidence.

The preview is retained at `http://127.0.0.1:57304/observatory/`, owned by
`4bc4b6047a504528b4548196afe3c171`, run `e5678ce62c6746ea8fef62368a357ec8`.
Three requests remain for the maintainer. Its launcher owns exact resource
cleanup on Ctrl+C; it is intentionally left running. The earlier 0.9.0 preview
and its quarantined record were preserved. Two diagnostic probes plus this
preview request made three real calls for this fix; there was no automatic retry.

This local verification is not the four-cell Linux release qualification. No
new release or SDK upgrade is included in this follow-up.
