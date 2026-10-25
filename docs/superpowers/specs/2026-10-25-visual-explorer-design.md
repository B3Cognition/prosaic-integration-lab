# Prosaic Explorer — visual documentation, playback and live controls

Date:2026-10-25. Status: proposed design for review.

## Intent and approved direction

The maintainer requested visual ecosystem documentation, suggested React Flow
and strong visual design, and explicitly requested all three capabilities:
documentation, scenario playback and live execution controls. The audience is a
newcomer discovering Prosaic and a developer integrating its public SDKs.

One local application should explain a capability, demonstrate its behavior and
let an operator run the relevant bounded example. Documentation/playback require
no credentials, Docker or model. Live single-agent execution requires explicitly
configured host profiles and allowances. The existing Docker service demos and
browser conversation retain their own execution/authentication contracts.

## Experience

Launch `python -m lab_runner.explore` and open a local browser. Default mode is
documentation/playback, with live controls visibly unavailable until the operator
restarts with explicit live configuration. No account setup is needed to learn.

Five chapters share a graph canvas, explanation panel and contextual actions:

1. **Ecosystem:** canonical Markdown → Core artifact → Runtime execution →
   Harness workflow, with host policy and storage shown as separate relationships.
   Explain responsibilities without implying an unsupported engine binding.
2. **Run an agent:** task, seeded inputs, permissions, model selection, tools,
   final output and independent grading. Show what a developer supplies.
3. **Review a workflow:** admit → execute → pause → exact human decision → resume.
   Explain revision/owner checks and durability. Playback first; link to existing
   authenticated workflow/browser demo rather than claim new unified-Harness support.
4. **Provider pool:** ordered profiles, availability, pre-work quota rejection,
   persisted cooldowns, local completion and stop after partial/uncertain work.
5. **Results:** sample output, task success, latency, profile attempts, controlled
   skips versus actual fallback, known/unknown usage and links to reproducible tasks.

Each view offers a plain-language explanation and a developer tab with public
API names, minimal code/configuration, copyable commands and matching guide links.
Select a node to inspect its role, inputs/outputs, boundaries and a concrete next
action. Graph operations are navigation/selection; this is not a workflow editor.

```
 Prosaic Explorer                   Documentation / Simulation / Live
 ┌─────────────────┬──────────────────────────────┬───────────────────────┐
 │ Ecosystem       │ Chapter title + explanation  │ Selected component    │
 │ Run an agent    │                              │ What it does          │
 │ Review workflow │     Interactive flow         │ Inputs / outputs      │
 │ Provider pool   │     + status on nodes        │ Host permissions      │
 │ Results         │     + viewport controls      │ User / developer tabs │
 │                 │                              │ Runnable example      │
 │ Prerequisites   │ Previous / Next / Reset      │ Contextual action     │
 └─────────────────┴──────────────────────────────┴───────────────────────┘
```

On narrow screens, chapter navigation becomes a compact menu and details stack
below the canvas. A list/text rendition exposes the same educational material
without requiring graph interaction. Keyboard selection, focus visibility,
screen-reader announcements and reduced-motion support are required.

## Visual direction — Taste v2

The maintainer selected Leonxlnx/taste-skill v2. Use `design-taste-frontend`
from stable v2.1.5, pinned upstream commit
`12af471f627f866411b4bd785b19646d3672784c`. It is installed locally at
`~/.codex/skills/design-taste-frontend`; it is design tooling, not a Lab runtime
dependency. Its app-screen workflow and `inspect.mjs --app` apply to this
interactive explorer. The page/marketing workflow does not apply.

Before choosing the direction, inventory the real product data and jobs:

- Objects: canonical Markdown agents, inputs, admitted workflows, provider
  profiles, execution policies, review interactions and execution receipts.
- Ecosystem scope: Core0.4.1, Runtime0.9.8, Harness0.9.4 and their existing stores.
- Providers: Claude Code, Codex CLI and one configured local/API profile.
- Live tasks: release brief, incident handoff and invoice SQL; their real seed
  packets and graders already exist in the Lab.
- Limits: native60s, local180/240s, pool300s; attempts3/native2/API requests8,
  tools7/rounds8/reported tokens65,536; mixed units remain distinct from tokens.
- Evidence: actual attempt/skip/fallback observations and known/unknown usage;
  simulated state is never presented as a live measurement.
- People: a newcomer learning the system and an integrator testing host policies,
  on desktop or a narrow screen.
- Jobs: inspect a component, step a scenario, review execution authority, run one
  allowed task, inspect its output and reconcile uncertainty deliberately.
- Product identity: Markdown instructions travel through host-controlled
  execution and end in an inspectable receipt. The handoff is the main visual.
- First-run state: real docs/scenarios are available, live results are absent;
  show setup actions rather than invented successful runs or metrics.

The first screen's question is: "How does this Markdown task become a permitted
execution, and where is control now?" Its biggest element is the graph answering
that question, beside its selected artifact/policy/receipt. The signature element
is the Markdown-to-receipt handoff, with genuine provider transitions in live
mode and clearly labelled transitions in simulation.

Taste dealt two suitable light builder styles: Achromatic ledger and Framed
sheet. Select **Framed sheet**, seed `1548770335`: the graph and its inspector
need a coherent work surface across documentation, simulation and live receipts.
No redraw was needed. The local generated sheet is
`.taste-skill/explorer/direction.json` (ignored design scratch).

Keep its defining move: a quiet tinted L-frame, a white sheet inset8px with
16px corners and a faint edge, no resting shadows. Sidebar228px, top bar48px,
content padding/gap24px; narrow layouts collapse navigation into a48px bar.
The selected chapter and mode use neutral selection/ink underlines rather than
colored navigation blocks. The same shell names Prosaic and its current scope.

Core tokens from the sheet: ground `#f9fbfc`, surface `#ffffff`, raised `#f4f6f8`,
active `#ebedee`, edge `#e8eaec`, ink `#131416`, secondary `#5d5f60`, accent
`#1b6c80`. Primary buttons are near-black. Spend color on the active handoff,
meaningful status and evidence, with text/icons as well as color; no rainbow
per provider and no decorative dot-grid behind the graph.

Load the dealt IBM Plex Sans at400/500/600, plus IBM Plex Mono for IDs and code.
Package the licensed font files locally so the installed explorer needs no
Google Fonts/CDN connection. Use22px view titles,16px section titles/graph
content,14px body/control text,12px secondary labels and tabular figures.
Use font licenses alongside packaged assets. This replaces the earlier Georgia
display-type and navy/blue sketch.

The product-specific face is the **Markdown-to-receipt handoff**: readable
Markdown, an explicit permission boundary, the eligible provider, a review gate
where relevant and the resulting evidence. Custom React Flow nodes represent
these objects. The graph takes the visual lead; real code, task packets and
receipts fill its inspector rather than generic metric cards or filler photos.

The library's builder pattern informs the graph canvas, not an editable workflow
palette: this product needs five labelled chapters, selection and a read-only
flow, so no insert/drag-to-create controls, search, account switcher or Save
button are added merely because a reference screen has them. This is a required
content adaptation, not a style redraw. Each view answers one question:

| View | First question | Main action |
| --- | --- | --- |
| Ecosystem | Which component owns this part of the task? | Inspect a component |
| Agent execution | What may this agent do with this input? | Review its contract |
| Workflow review | What decision is needed before execution can continue? | Step the review scenario / open existing demo |
| Provider pool | Why was this profile selected, skipped or stopped? | Play the fallback scenario |
| Results/live run | Did this task complete, and what evidence supports it? | Review authority and run / inspect the receipt |

No ornamental motion, fake results or decorative KPI row. Show honest missing,
zero, disabled, loading, blocked and failed states. Preserve manual playback
stepping and reduced motion. Use Taste's app lint/inspector on the final production
build at1440/768/390px, inspect every screenshot, and record the app-screen
critique/fixes. No browser inspection or visual-quality pass is claimed for
this design-only checkpoint.

## Scenario playback

Ship deterministic educational scenarios with an explicit Simulation label:
normal agent completion, native providers reject before work then local succeeds,
cooldown skips on a later request, all providers unavailable, partial work stops,
workflow awaiting human review, stale approval rejected and successful resume.

Play/pause, previous/next and reset affect only the local illustration. They do
not launch processes, contact model endpoints, reserve live allowance, change
real cooldowns or manufacture evidence. Playback values are labelled illustrative,
not measured. Existing verified fixture commands remain the correctness proof;
the animation is an explanation of their contracts.

## Live execution scope

Provide host-run single-agent examples for release brief, incident handoff and
invoice SQL, using the existing neutral Markdown, seeded packets and graders.
The UI chooses an allowlisted task and one of the host-approved configurations.
It does not accept arbitrary executable paths, source paths, endpoints, API keys,
environment variables, shell commands, filesystem grants or user-written agents.
Supporting arbitrary registered applications is a later integration.

Native CLIs run on the operator host through the released Runtime CLI, using
the operator's authenticated private profiles. They do not run in a browser or
assume vendor authentication exists inside the Lab Docker service. The existing
Lab service/chat is not silently switched to `UnifiedRuntime`.

The launcher requires explicit live opt-in, an owned private configuration,
private evidence root and a durable allowance. The host maximum is20mixed units
by default when live is explicitly enabled; one run reserves its worst-case10
(two native attempts plus eight API requests). This is not a token/currency cap.
An operator may choose a smaller/larger explicit maximum within the existing
allowance implementation's supported bound; the browser cannot increase it.

Before execution show the task/input preview, configured profile order, native
workspace permission, exact API output grant, all request/tool/token/attempt
caps, local/native/pool deadlines and remaining mixed-unit allowance. A deliberate
Run action authorizes one invocation only. No automatic run on page load,
selection, playback, refresh, websocket reconnect, report viewing or approval
simulation. No batch benchmark launch is included in this first live controller.

Defaults/caps reuse the established bounded protocol: pool300s, native60s,
local180s with explicit240s choice permitted by the host; three total profile
attempts, two native, eight API requests, seven tools, eight tool rounds and
65,536 API reported tokens. Native workspace-write and exact API output grants
stay independent. Native internal loops/subscription spend remain opaque.

Show actual filtered selection/fallback events and elapsed time while a run is
active; if the transport only provides final observations, display them as a
completed timeline rather than invent real-time progress. Grade success only
after successful execution plus the independent existing task grader. Preserve
valid output from failed/timed-out invocations as failed-run evidence.

Stop/cancel requests interrupt the owned worker/process group and preserve
unknown reservations and partial-work evidence. Do not promise effect rollback.
Once partial effects, ambiguous dispatch or missing terminal receipts occur,
persist an admission blocker in the evidence root. It survives launcher/browser
restart and blocks further live runs against that root pending operator reconciliation.
No UI button clears unknown usage or real cooldowns. Runtime remains the sole
authority for deciding whether pre-work provider fallback is safe.

Reconciliation is an offline operator action: inspect the retained run, then
explicitly acknowledge uncertain effects through a launcher CLI command bound
to the exact run ID and current receipt digest, with a bounded private note.
Record that acknowledgment durably. It may release the admission blocker for
new independently authorized requests; it never reruns the old request, marks
unknown usage as zero/known, releases its allowance reservation or claims an
effect completed. Reusing the old request identity still returns its original
uncertain receipt. Missing/stale acknowledgments leave the blocker intact.
Documentation/playback and receipt inspection remain available while blocked.
This conservative reconciliation rule is a design choice, not a new SDK facility.

## Host boundary and persistence

Use a separate loopback-only FastAPI launcher/coordinator, consuming the public
installed Runtime CLI and existing Lab task/grading/allowance components. Keep
one active live invocation per launcher. Use asynchronous HTTP admission with a
bounded host worker; never block the request event loop on inference.

Live mutations require an authenticated launch session, same-origin validation
and a bounded body. Reuse the existing Lab launch-token pattern: private single-use
bootstrap, token held in memory, no credentials in browser storage/URLs/logs or
client-supplied identity. Documentation/compiled assets expose no private host
configuration. This is a local Lab experience, not production multi-tenant login.

An exact request identity prevents duplicate dispatch on double-click/network
retry. Persist admission/reservation before starting work and return an existing
receipt for the same request. Distinct attempts require new explicit authority;
conflicting/revoked identities fail. On launcher restart, interrupted jobs remain
uncertain and are inspectable, never automatically relaunched. Process shutdown
cleans only owned resources and retains durable evidence.

Server-owned workspaces are private and unique per run. Filter browser results
to known structural fields and bounded task output; render all output as text,
never HTML. Do not expose vendor streams, login files, session identifiers,
provider errors, environment data or private configuration paths. Model-written
Python/shell is never executed by graders; SQL retains read-only in-memory checks.

## Implementation and distribution

Use React/TypeScript plus React Flow (`@xyflow/react`) for the browser, and Python
for host execution. Introduce a small dedicated frontend source directory with a
committed dependency lock and checked build output. Serve packaged static assets
locally, without CDN dependencies. Node is needed for frontend development/build
verification, not for an installed Python user to open the explorer.

CI must rebuild and verify the frontend against its source/lock, test the Python
boundary and exercise installed wheel/rebuilt-source static assets. Preserve the
existing SDK pins, legacy release assets, CLI interfaces, native confinement,
accounting and no-replay gates. No SDK implementation changes are part of this
project; upstream defects require separately authorized owning-repo work.

## Verification and completion

- UI: inspect screenshots on wide/narrow screens; verify chapter navigation,
  node inspector, keyboard/text alternative, playback/reset, reduced motion,
  output escaping, accessible errors, prerequisite/setup states and failed runs.
- Host: credential-free fixture subprocesses/endpoints exercise admission/auth,
  CSRF/origin rejection, double clicks/reconnects/restart, allowance overrun,
  capacity unavailable, pre-work fallback, partial text/tools, timeout/cancel,
  unknown evidence, no implicit dispatch and exact-owned cleanup.
- Packaging: fresh Python wheel and rebuilt-source installs serve assets and
  open documentation without Node/Docker/model credentials. Existing full suite
  and mandatory platform acceptance remain required before merge/release.
- Actual live runs need explicit approved profiles and a separately bounded
  allowance. Fixture success must not be reported as live model qualification.

Deliver all three modes in this project, in testable stages: documentation
canvas, scenario playback, bounded live controller, then integrated verification
and guide updates. Do not publish or merge solely because the visual surface
looks complete. A later version/release is separate from design approval.

## References

- Existing Lab: `docs/quickstart.md`, `docs/unified-runtime-pools.md`,
  `lab_runner/native_eval/unified_benchmark.py`, `lab_runner/live_allowance.py`.
- React Flow custom nodes: https://reactflow.dev/learn/customization/custom-nodes
- React Flow accessibility: https://reactflow.dev/learn/advanced-use/accessibility

Taste is now explicitly selected and installed. Its v2 app-screen workflow
replaces the generic frontend-design skill as the visual design authority for
this work; project behavior, safety boundaries and user requirements take precedence.

## Builder review

A fresh implementation-readiness review asked whether the uncertainty blocker
survives restart and what reconciliation permits. The durable blocker/offline
acknowledgment rules above settle that question while preserving unknown
reservations and denying replay of the original request. No human product
preference is needed to choose this conservative host behavior.
