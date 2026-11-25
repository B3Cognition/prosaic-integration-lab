# Lab 0.6.1 / Runtime 0.9.8 live benchmark with local240s — 2026-10-25

All **27/27 assignments passed**: release brief, incident handoff and invoice
SQL, three trials per model through the unified Claude → Codex → local pool.
Success required both CLI completion and the unchanged factual/workspace grader.

## Protocol and release boundary

The study used the public **Lab 0.6.1** wheel and released **Runtime 0.9.8**.
The published Lab driver fixes its local deadline at 180s, so this authorized
240s study used a private copy of that consumer driver with **seven local
deadline literals changed from 180 to 240**. Both drivers and their exact diff
are retained. Installed Lab and SDK payloads passed audits before and after
inference; they were not patched.

This measurement predates the configurable CLI implementation now described in
the [benchmark recipe](../realistic-runtime-benchmark.md). It is not evidence
that published 0.6.1 accepts `--local-timeout 240`, nor a live validation of the
new implementation. This code/documentation follow-up performs no new live calls.

Paired audits verified the same neutral Markdown, seeded inputs, graders and
native/local profile bytes as the [preceding 180s study](unified-cli-released-2026-10-24.md).
Native/pool deadlines stayed **60s/300s**. API output-token cap remained 2048;
native workspace-write and API read/write/edit with an exact output write path
were unchanged. Caps remained three profile attempts, two native attempts,
eight API requests, seven tools, eight rounds and 65,536 reported API tokens.

## Success and latency

Each model completed nine assignments. All-attempt and successful-only latency
distributions coincide because every assignment passed.

| Configured model | Success | Median (range) | Prior 180s median | Median change |
| --- | --- | --- | --- | --- |
| Claude Code `sonnet` | 9/9 (100%) | 10.86s (9.66–12.24s) | 11.37s | −4.5% |
| Codex `gpt-6.1-sol`, low effort | 9/9 (100%) | 21.73s (16.89–26.88s) | 23.07s | −5.8% |
| Local ThinkingCap-Qwen3.8-27B-MLX-4bit-DWQ | 9/9 (100%) | 62.37s (38.80–160.33s) | 60.69s | +2.8% |

Per-task medians, three trials per model/task:

| Task | Claude | Codex | Local |
| --- | ---: | ---: | ---: |
| Release brief | 10.86s | 21.27s | 69.55s |
| Incident handoff | 11.11s | 21.03s | 62.37s |
| Invoice SQL | 10.61s | 26.28s | 49.08s |

There were **zero timeouts**, and all local runs finished within the former
180s limit. The larger deadline did not rescue an observed timeout. Timed
assignments totaled 994.98s. No deliberate warmup or concurrent test suite was
run by this task; host/cache/provider conditions were uncontrolled. The model
aliases do not establish immutable weights, and these small samples do not
isolate timeout effects, rank models generally, measure narrative elegance or
support a p95 claim.

## Selection, accounting and cleanup

Every assignment selected its expected eligible profile. Controlled exclusions
produced **27 profile skips**; there were **zero provider-triggered fallback
events**, zero multi-profile assignments and no replay. No live quota exhaustion
was induced. The retained [provider-rejection/no-replay fixture tests](unified-provider-fallback-2026-10-23.md)
remain separate evidence of that behavior.

The durable allowance retained **45/243 mixed units**: 18 native CLI attempts
and 27 API requests, with **zero unknown reservations**. All 27 admissions were
joined to their known ledger entries. These units are not tokens or cost
equivalents. No timed assignment was discarded, restarted or retried.

All temporary workspaces were removed and controlled native marks restored.
The local bucket retained its original absent/`unknown` capacity state; this is
separate from unknown dispatch accounting. The cleanup checker was corrected
after confirming that SDK status semantics and every pre-assignment snapshot
reported the same original state; capacity data was not rewritten to pass it.
The owned server's PID, listener and private log descriptors were verified before
SIGTERM; it exited and port 8001 closed. The separate desktop server on 8000 was
left untouched. The server used the preceding thinking-disabled profile and an
owned link to the existing weights after the cache adopted an organization
subdirectory layout. API profile bytes and endpoint port were unchanged.

## Provenance and retained evidence

- Lab wheel SHA-256:
  `4c2fcd63c9b151e5007292670dbcb1a2e6a578be1710f2b37fa6eea3b79e7d13`.
- Runtime wheel SHA-256:
  `d9d416baf9a7f4b87328532d41b281a2f6dbc9bafc744f973661a5cf6015a540`.
- SDK manifest SHA-256:
  `36eec99280acb8688d2496f704f4445b59c3ff269fc506a83d6e7fe83bc92698`.
- Grader SHA-256:
  `69a3409789223154cadb4894d670efb874d81bef439f638c2f924e482e58661a`.
- Current `report.json` SHA-256:
  `5a5d848b71c5a67052ad47496d0c58eae24bacd64a767ec6092d91850d8114ad`.
- Preceding `report.json` SHA-256:
  `100f176e6b833b4a955f1f4f0c9738e3680b171a879c4b20778ec1d324f25e1f`.

The audit paired all 27 current/prior assignments, recomputed metrics, verified
Markdown/input/output hashes, permissions and budgets, and regraded all **54
current/prior saved outputs**. Core 0.4.1, Runtime recorder 0.3.0, Harness 0.9.4
and Harness store 0.4.0 retain their released pins. The clean installed consumer
used Python 3.12.15 on macOS ARM64.

Private evidence remains under the gitignored
`reports/unified-cli-lab061-runtime098-local240-live-2026-10-25/`: plan, source
snapshot/diff, samples, synthetic outputs, admissions, allowance/capacity,
comparison audit and cleanup receipt. Preparation guard corrections preceded
the allowance and first timed assignment. Credentials and raw vendor streams
are excluded; previous reports and release artifacts remain unchanged.
