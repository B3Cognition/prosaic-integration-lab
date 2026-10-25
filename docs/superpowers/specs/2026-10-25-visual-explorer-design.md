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

## Visual direction (design choice)

Use a technical field-guide aesthetic: a pale blue-gray drafting surface,
deep navy typography, precise connections and restrained colored state markers.
The signature interaction is a clearly visible handoff of control between
Markdown, host policy and execution—not a decorative animated background.

Tokens: paper #F3F6FA, surface #FFFFFF, ink #142D4E, muted #51647A,
action #215DCE, boundary #A75B12. Success/failure use labels/icons as well as
color. Typography: restrained Georgia display titles, system sans body text and
system monospace for contracts/receipts. No network font dependency.

Custom React Flow nodes should look like useful parts of this ecosystem:
Markdown document, host permission boundary, provider profile, review gate and
receipt. Information density stays modest; reveal detail through selection.
Use short transitions for actual step changes, with manual Next always available.

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

Taste was suggested as an optional skill; no installed Taste skill was found.
The available local frontend-design skill supplies the visual design guidance.

## Builder review

A fresh implementation-readiness review asked whether the uncertainty blocker
survives restart and what reconciliation permits. The durable blocker/offline
acknowledgment rules above settle that question while preserving unknown
reservations and denying replay of the original request. No human product
preference is needed to choose this conservative host behavior.
