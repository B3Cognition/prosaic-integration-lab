# Released Runtime 0.9.8 live CLI benchmarks — 2026-10-24

Two separately authorized live studies each completed **27/27 successful
assignments** through the unified Claude → Codex → local CLI pool. Each study
repeated release brief, incident handoff and invoice SQL three times in each
availability state. Success required both CLI completion and the unchanged
factual/workspace grader. All 54 assignments passed; none timed out.

These are fresh public-wheel measurements, separate from the retained
[0.9.3 candidate benchmark](unified-cli-realistic-2026-10-23.md) and the
[offline release adoption](runtime-unified-release-2026-10-24.md).

## Success rate and latency

Every table entry represents nine assignments per model per study. All-attempt
and successful-only distributions coincide because every assignment passed.
Latency includes CLI startup, inspection, execution and terminal-result handling.

| Selected model | Success in each study | First released study median (range) | Latest rerun median (range) | Historical candidate median |
| --- | --- | --- | --- | --- |
| Claude Code `sonnet` | 9/9 (100%) | 10.38s (9.11–10.82s) | 11.37s (9.64–12.57s) | 12.13s |
| Codex `gpt-6.1-sol`, low effort | 9/9 (100%) | 23.61s (13.41–27.68s) | 23.07s (16.40–28.16s) | 23.99s |
| Local ThinkingCap-Qwen3.8-27B-MLX-4bit-DWQ | 9/9 (100%) | 66.21s (39.44–85.22s) | 60.69s (41.08–85.66s) | 60.58s |

Latest per-task medians, three trials per model/task:

| Task | Claude | Codex | Local | Success per model |
| --- | ---: | ---: | ---: | --- |
| Release brief | 10.99s | 22.88s | 72.82s | 3/3 |
| Incident handoff | 10.32s | 27.97s | 60.69s | 3/3 |
| Invoice SQL | 11.65s | 16.59s | 46.95s | 3/3 |

Relative to the first released study, latest median latency changed approximately
+9.5% for Claude, −2.3% for Codex and −8.3% for local. Success and observed
fallback behavior were unchanged. Host/cache/provider conditions were
uncontrolled; model aliases can resolve differently over time. These differences
do not isolate Runtime effects or establish a general model ranking, narrative
quality equivalence or p95. Graders assess facts and workspace integrity.

## Unchanged protocol and endpoint-only difference

The benchmark driver, neutral Markdown, seeded packets/drafts, graders and native
profiles match the historical study. Paired audits verified all Markdown and
seeded-input hashes across backends, tasks and repetitions. The fixed grader
SHA-256 remains
`69a3409789223154cadb4894d670efb874d81bef439f638c2f924e482e58661a`.

Native deadlines remained **60 seconds**, local/API **180 seconds**, and the
pool total **300 seconds**. The local model retained its 2048 output-token cap
and private oMLX profile with thinking disabled. The latest run's private API
configuration changes only loopback port 8000 → 8001 because the desktop oMLX
server already occupied 8000. A byte comparison verifies that endpoint-only
difference; model/settings, secret file and every other API profile byte match.
The desktop server was left untouched, so external host load is uncontrolled.

Each invocation explicitly granted native workspace-write separately from API
read/write/edit, a workspace read root and the exact output write path. Caps
remained three profile attempts, two native attempts, eight API requests, seven
API tools, eight rounds and 65,536 API reported tokens. Native internal requests
and subscription costs remain opaque.

Each study used a fresh exclusive 0700 report root, fresh workspaces, rotated
task/state order and sequential assignments. No deliberate warmup or concurrent
test suite was run by this task. The first study's setup refusals occurred before
any run directory, allowance or dispatch; no timed assignment was restarted,
discarded or replayed. Assignment times totaled 863.23s and 880.96s respectively.

## Selection, cooldowns and fallback

Every assignment selected the expected first eligible profile in Claude → Codex
→ local order. In **each study**, controlled Claude cooldowns produced nine
skips and controlled native cooldowns produced eighteen: **27 controlled skips**.
Excluded profiles were never attempted. Cleanup restored only owned marks,
preserving real provider marks; final native buckets were available.

Each study recorded **zero provider-triggered fallback events**, zero
multi-profile attempts within an assignment and no replay after work. These
observations validate eligibility selection under controlled cooldowns. No real
quota exhaustion was induced; the existing
[provider-shaped rejection/no-replay tests](unified-provider-fallback-2026-10-23.md)
remain separately labeled fixture evidence.

Each durable allowance retained **45/243 mixed units**: 18 native CLI attempts
and 27 API requests, zero unknown reservations. Each local assignment made three
requests. Every admission was joined to its exact known ledger entry. These
units are not token or cost equivalents. Historical allowances were preserved.

## Public release provenance and audit

- Installed public Runtime **0.9.8**, source
  `a9433a68f60eeecf1946a398267f749c7ff89d8e`.
- Runtime wheel SHA-256:
  `d9d416baf9a7f4b87328532d41b281a2f6dbc9bafc744f973661a5cf6015a540`.
- Five-wheel manifest SHA-256:
  `36eec99280acb8688d2496f704f4445b59c3ff269fc506a83d6e7fe83bc92698`.
- Core 0.4.1, Runtime recorder 0.3.0, Harness 0.9.4 and Harness store 0.4.0
  retain their original public pins. Both installed payload audits and pip checks
  passed before inference; no editable SDK checkout was used.
- Lab driver tree `dcb51fd054dcaaa7a63593a0a1d4b3bf669bb407` is identical to
  merged adoption `8194f6a0f6e64c6186c8aa129bc759e9e3ef3008`.
- SDK-only Python 3.12.15 on macOS ARM64; Claude Code 2.1.308 and Codex CLI
  0.163.0. Configured model aliases/effort are shown above; native alias names
  are not claims of immutable provider model weights.
- Each post-run audit paired 27 samples with its preceding study, regraded all
  **54 current/prior saved outputs**, recomputed metrics and verified
  input/output/source hashes, permissions, deadlines, exclusions and admissions.
  The first released study pairs with the historical candidate; the latest pairs
  with the first released study. This is not a claim of 108 distinct outputs.

Private evidence is retained under these gitignored report roots:

| Study | Report root | `report.json` SHA-256 |
| --- | --- | --- |
| First released study | `reports/unified-cli-release-098-live-2026-10-24/` | `d1823be37b7d323d0fd792698b3ceb8b209c1afdb8c6de4df1cc9a7653044ed4` |
| Latest rerun | `reports/unified-cli-release-098-live-2026-10-24-rerun2/` | `100f176e6b833b4a955f1f4f0c9738e3680b171a879c4b20778ec1d324f25e1f` |

Each root retains its plan, driver, admissions, allowance/capacity, samples,
synthetic outputs, comparison, audit script and cleanup receipt. Raw vendor
streams, credentials and session IDs are not retained. These private reports
are not public downloadable fixtures and are not committed with this ledger.

## Cleanup and reproduction

All temporary workspaces were removed and controlled marks restored. Each owned
local inference process was verified against its loopback listener and both
private log descriptors, then stopped with SIGTERM. The first run's port 8000
and the latest run's port 8001 were confirmed closed after their owned servers
exited; the latest run left the separate desktop server on 8000 untouched.
Native logins, shared model cache, historical reports and dirty workspaces were
preserved. Both private cleanup receipts passed.

Use the [released benchmark recipe](../realistic-runtime-benchmark.md#repeated-unified-cli-pool-study)
with the verified public manifest, explicit live authorization, private profiles,
an unoccupied loopback port and a fresh output leaf under an existing parent.
Missing infrastructure must fail, and uncertain work must not be replayed.
