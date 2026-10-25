# Prosaic Explorer

Explorer explains how Markdown, execution policy, provider pools, workflows and
receipts fit together. It is a local Integration Lab application consuming public
SDKs. This checkout adds it after Lab 0.6.2; published 0.6.2 artifacts do not
contain it. SDK versions remain Core 0.4.1, Runtime 0.9.8 and Harness 0.9.4.

## Open the visual guide

Complete [quickstart setup](quickstart.md#setup-once), then run:

```sh
"$LAB_PY" -m lab_runner.explore
```

The launcher opens a loopback page. Default documentation and playback require
no model credentials, Docker or Node. Fonts, scripts and styles are bundled;
guide links open GitHub and need internet. The graph and list contain the same
material. Select a component to read its inputs, outputs and authority boundary;
**Developer** exposes copyable public commands and references. Commands shown
in documentation are text, never executed by selecting them.

Five chapters cover the ecosystem, one agent, a reviewed workflow, provider pools
and execution receipts. **Simulation** contains eight deterministic scenarios:
completion, pre-work quota fallback, persisted cooldowns, all profiles unavailable,
partial work, waiting for review, stale approval rejection and exact resume. Play, pause,
step or reset them. They make no model requests, change no real cooldowns and
consume no allowance. These are explanations, not benchmark observations.

On phones the list opens first; **Graph view** switches to the overview. Graph
nodes are keyboard selectable and the list offers ordinary buttons. Motion
respects reduced-motion preferences.

The interface uses locally bundled **Instrument Sans**, with **Geist Mono** for
code and identifiers. Chapters share a window-sized frame: Previous/Next stay
anchored at the bottom while longer content scrolls inside. Each new chapter
opens at the start of its content. The content pane can receive keyboard focus
for scrolling, and no model work starts during navigation.

Selecting a chapter opens its documentation and stops illustrative playback.
Returning to **Live** retains the current request and selected receipt. After a
request reaches an observed terminal state, status polling leaves your selected
historical receipt in view. A lost submission response still recovers the exact
admitted request rather than authorizing another dispatch.

Use **Appearance** at the top right to choose **System**, **Light** or **Dark**.
System follows your device, including changes while the page is open. Light
uses the Taste v2 Framed sheet direction; Dark uses neutral black surfaces and
teal graph highlights inspired by its True-black flat direction. Both retain
the same content, navigation and execution controls.

Only this appearance preference is saved in local storage for the current
browser origin; using a new launcher port starts a fresh preference. Credentials
remain in memory. If storage is restricted, switching still works for the current
page. Switching appearance preserves the selected component and playback
position, and never connects to a model or starts a run.

## Enable one bounded live task

Live execution is a separate opt-in. Configure authenticated profiles using
[Connect real models](quickstart.md#4-connect-real-models-explicit-opt-in). Copy
all three example configuration files together; edit model names, profile
directories, quota identities and local endpoint/key references. Files must be
owned by your user and private (0600); configuration paths cannot use symlinks.
The launcher audits installed SDK payloads against the manifest and wheel cache.

Keep the quickstart's `LAB_PY`, `WHEEL_DIR` and configured `PRIVATE_DIR`. Create
one unused durable evidence directory, then start:

```sh
umask 077
EVIDENCE_ROOT="$HOME/prosaic-explorer-evidence"
mkdir -m 700 "$EVIDENCE_ROOT"
"$LAB_PY" -m lab_runner.explore --live \
  --config "$PRIVATE_DIR/unified-runtime.example.yml" \
  --manifest "$PWD/dependencies/releases.json" \
  --wheel-dir "$WHEEL_DIR" \
  --evidence-root "$EVIDENCE_ROOT" --max-units 20
```

Use an absolute, canonical, owned directory (0700). Keep it across restarts;
reuse its allowance ceiling. Do not replace evidence to bypass retained usage
or an uncertainty blocker. The host config fixes profile order; the browser
cannot supply configuration paths, credentials, endpoints, commands or grants.
Changing a frozen config after launch blocks new admission; stop and review it
before restarting.

Open **Live**, select release brief, incident handoff or invoice SQL, and choose
180s or 240s for local/API execution. These are the unchanged neutral Markdown,
seeded inputs and independent graders used by the realistic benchmark. Review
the actual configured profile order, permissions, policy and remaining allowance.
Check the one-invocation authorization box and press **Run once**. Connecting,
changing a chapter, reading status or playing a scenario never starts work.

| Boundary | Fixed authority |
| --- | --- |
| Concurrency | One admitted invocation at a time; at most 64 retained admissions per evidence root |
| Profile attempts | 3 total; at most 2 native attempts |
| Deadlines | Pool 300s; native 60s; local/API 180s by default or explicit 240s |
| Native grant | `workspace-write` in a fresh owned task workspace; native internal work/spend is opaque |
| API grant | `read_file`, `write_file`, `edit_file`; workspace reads, writes only to the task's named output |
| API limits | 8 requests, 7 tool calls, 8 rounds, 65,536 reported tokens |
| Durable allowance | Up to 10 mixed units reserved per invocation: 2 native attempts + 8 API requests; default ceiling 20, host range 1–256 |

Mixed units are not money or tokens. A new request needs 10 remaining units for
worst-case reservation. Known native/API dispatch counts settle the reservation;
unknown usage stays retained. API reported-token caps do not bound native
subscription spend or unreported usage. Profile aliases sharing a real quota
must share quota identity.

Runtime owns selection and cooldowns. Confirmed quota rejection before work can
switch to the next eligible profile. Partial work, timeout, ambiguous acceptance
or missing final evidence stops execution; Explorer never replays it. All
profiles unavailable returns a failed capacity result without waiting for quota.
The receipt separates invocation outcome, task grader, selected profile, filtered
events, elapsed time, known/unknown usage and retained output. Valid output alone
does not establish successful execution. Output is displayed as text.

## Retry, cancel and recover

A transport retry retains the same request ID and returns the original admission.
It does not dispatch again. **Prepare a new explicit request** appears only after
that request has a terminal receipt. **Refresh status** can recover an admission
whose POST response was lost. Do not submit new identities to resolve uncertain
responses.

**Cancel owned run** interrupts the owned Runtime process group and retains
evidence. It cannot undo effects or claim zero usage. Closing the launcher also
interrupts owned work. Cancellation, timeouts and uncertain effects block further
admissions across restarts. Inspect the private receipt/workspace before deciding
what to do next.

Stop the launcher before offline inspection. Copy the exact run ID from its
receipt and inspect without opening profiles or contacting providers:

```sh
"$LAB_PY" -m lab_runner.explore --inspect \
  --evidence-root "$EVIDENCE_ROOT" --run-id YOUR_RUN_ID
```

After investigating the effects, an operator can record an acknowledgment bound
to the returned `receiptSha256`. Write the decision in a private 0600 UTF-8 file
(at most 2048 bytes), then:

```sh
"$LAB_PY" -m lab_runner.explore --acknowledge \
  --evidence-root "$EVIDENCE_ROOT" --run-id YOUR_RUN_ID \
  --receipt-sha256 EXACT_RECEIPT_SHA256 --note-file /absolute/private/note.txt
```

This permits new explicit requests only when all blockers are acknowledged. It
never reruns the old request, changes its outcome or refunds unknown usage.
Acknowledgments and private workspaces are retained. Keep real profile names,
outputs and evidence private; the launcher does not make them public artifacts.

## Connection and workflow limits

The launch URL carries a single-use connection code in its fragment, removed
immediately by the UI. It expires after ten minutes. The bearer token stays in
memory; reloading loses it. Restart for a new private launch link. An already
admitted run continues until completion/cancellation, and restart never replays
it. Plain loopback URLs still open documentation and simulation.

If browser opening fails, use `--no-open` and read the printed private connection
file locally. Its `url` field is the connection link; do not share it. A custom
`--launch-file` must be a new file in an owned private directory. `--port` defaults
to a free numeric-loopback port. Stop with Ctrl+C when finished.

The workflow chapter explains Harness and plays review scenarios. Real Harness
pause/resume remains in the [separate service/browser demo](quickstart.md#3-run-the-service-or-open-the-browser).
Explorer's live control runs individual agent tasks through Runtime; it does not
wire unified pools into the conversation service or control workflow resumes.

## Developing the interface

End users run the bundled Python assets. Contributors need Node 22+ only to
change/rebuild the UI:

```sh
npm ci --prefix frontend/explorer --ignore-scripts
npm test --prefix frontend/explorer
npm run build --prefix frontend/explorer
npm exec --prefix frontend/explorer -- playwright install chromium
EXPLORER_PYTHON="$LAB_PY" npm run test:browser --prefix frontend/explorer
```

Commit both `frontend/explorer` source/lock and `lab_runner/explore/web` generated
assets, including local fonts, OFL licenses and bundled JavaScript notices. Python packaging does not execute
Node. Required acceptance rebuilds the locked frontend and rejects changed or
untracked generated assets. One Linux acceptance cell runs real Chromium
regressions against a documentation-only launcher and intercepted synthetic
live responses. No model calls are made. Clean-distribution qualification runs
`scripts/explorer_smoke.py` with each installed consumer's isolated Python.
