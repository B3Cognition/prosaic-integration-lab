const guide = (path: string) =>
  `https://github.com/B3Cognition/prosaic-integration-lab/blob/main/docs/${path}.md`;
export type LessonNode = {
  id: string;
  title: string;
  kind: string;
  summary: string;
  input: string;
  output: string;
  boundary: string;
  code: string;
  guide: string;
};
const node = (
  id: string,
  title: string,
  kind: string,
  summary: string,
  input: string,
  output: string,
  boundary: string,
  code: string,
  path: string,
): LessonNode => ({
  id,
  title,
  kind,
  summary,
  input,
  output,
  boundary,
  code,
  guide: guide(path),
});
const markdown = node(
  "markdown",
  "Canonical Markdown",
  "Source",
  "A task travels as readable instructions, tool declarations and named inputs.",
  "Task Markdown + packet.json",
  "A portable agent contract",
  "Text describes intent. It cannot grant host filesystem or provider authority.",
  "---\nname: release-brief\ntools: write\n---\nRead packet.json and correct brief.json.\nApprove only current passing evidence.",
  "realistic-runtime-benchmark",
);
const core = node(
  "core",
  "Core artifact",
  "Core 0.4.1",
  "Core parses, validates and distributes canonical prose to target adapters.",
  "Canonical Markdown",
  "Inspected, rendered task artifact",
  "Core never executes a model or orchestrates a workflow. Catalogue discovery is read-only.",
  "python -m lab_runner.native_eval --help",
  "reference-guide",
);
const runtime = node(
  "runtime",
  "Permitted execution",
  "Runtime 0.9.8",
  "Runtime chooses an eligible provider under the explicit host policy.",
  "Inspected agent + policy + workspace",
  "Execution result and provider observations",
  "Runtime owns safe pre-work fallback. Partial or uncertain work stops further dispatch.",
  'from prosaic_runtime import UnifiedRuntime, UnifiedRuntimeConfig\nruntime = UnifiedRuntime(\n    UnifiedRuntimeConfig.load("/private/unified.yml")\n)\n# Supply explicit PoolPolicy and a private workspace.',
  "unified-runtime-pools",
);
const harness = node(
  "harness",
  "Durable workflow",
  "Harness 0.9.4",
  "Harness keeps workflow state, pauses and exact human decisions across workers.",
  "Admitted workflow + trusted owner",
  "Paused or completed workflow",
  "The host derives identity. Approval binds the exact revision, owner and interaction.",
  "python -m lab_runner demo --open-report",
  "native-workflows",
);
const host = node(
  "host",
  "Host permission boundary",
  "Host policy",
  "The application admits one invocation and supplies independent native and API grants.",
  "Trusted operator configuration",
  "Bounded, explicit execution authority",
  "A task cannot supply credentials, endpoints, identity or arbitrary filesystem grants.",
  'NativePolicy(permission_mode="workspace-write", timeout_s=60)\n# API: read workspace; write only the named output.',
  "unified-runtime-pools",
);
const receipt = node(
  "receipt",
  "Inspectable receipt",
  "Evidence",
  "Execution, grading and usage are separate facts; preserve each when another fails.",
  "Filtered terminal result + independent grader",
  "Output, task checks and known/unknown usage",
  "Usage is evidence, never consent to retry or proof of task success. Unknown is not zero.",
  "python -m lab_runner.native_eval unified-fallback-test --help",
  "realistic-runtime-benchmark",
);
const packet = node(
  "packet",
  "Seeded task packet",
  "Input",
  "Current evidence and an intentionally flawed draft make correctness testable.",
  "packet.json + existing output draft",
  "A corrected brief, handoff or SQL query",
  "The packet must remain unchanged. No invented evidence and no extra files are allowed.",
  "release-brief: candidate 2.8.0 / c42 / h42\nunit-current: PASS\nmigration-current: FAIL\nreview-previous: c41 / h41 — stale",
  "realistic-runtime-benchmark",
);
const grader = node(
  "grader",
  "Independent task grader",
  "Validation",
  "The host checks factual contracts after a successful execution.",
  "Named output + unchanged input packet",
  "passed / failed; separate from execution state",
  "Model-written Python or shell is never executed. SQL checks use read-only in-memory fixtures.",
  "invoice-sql: one read-only query\nGROUP BY customer_id\nClamp each invoice balance before aggregation.",
  "realistic-runtime-benchmark",
);
const review = node(
  "review",
  "Exact human decision",
  "Review gate",
  "Pause at a decision and inspect precisely what the next action would authorize.",
  "Owner + revision + interaction",
  "One accepted or rejected decision",
  "A stale, quoted or mismatched approval cannot resume a workflow. Playback grants no real authority.",
  "python -m lab_runner demo --open-report\n# Existing authenticated workflow demo; separate service.",
  "tool-approval",
);
const profiles = node(
  "profiles",
  "Ordered profiles",
  "Provider pool",
  "Claude Code, Codex CLI and a configured local/API profile are considered in host order.",
  "Host-approved profile configuration",
  "An eligible profile, or capacity unavailable",
  "Aliases do not create new quota. Cooldown is an eligibility hint, not a reservation.",
  "PoolPolicy(timeout_s=300, max_attempts=3,\n           max_native_attempts=2, ...)",
  "unified-runtime-pools",
);
const cooldown = node(
  "cooldown",
  "Pre-work eligibility",
  "Cooldown",
  "Persisted cooldowns skip unavailable profiles on later requests.",
  "Availability + persisted cooldown",
  "Eligible profile or a controlled skip",
  "Only concrete proof of rejection before model/tool work can permit fallback. No automatic wait/replay.",
  "Native timeout: 60 s\nLocal timeout: 180 or 240 s\nPool deadline: 300 s",
  "unified-runtime-pools",
);
const stop = node(
  "stop",
  "Stop on uncertainty",
  "No replay",
  "Partial text, tools, ambiguous acceptance and missing terminal evidence stop the pool.",
  "Partial or uncertain provider observations",
  "Retained evidence + admission blocker",
  "Reconciliation is offline and receipt-bound. It cannot refund unknown usage or rerun the old request.",
  "python -m lab_runner.explore --help\n# Inspect retained receipt before offline acknowledgment.",
  "recovery",
);
export const chapters = [
  {
    id: "ecosystem",
    title: "Ecosystem",
    question: "From Markdown to a permitted execution",
    description:
      "Follow the handoff. Core distributes the task; Runtime executes it; Harness owns the durable workflow.",
    nodes: [markdown, core, runtime, harness, host, receipt],
    links: [
      ["markdown", "core"],
      ["core", "runtime"],
      ["runtime", "harness"],
      ["host", "runtime"],
      ["runtime", "receipt"],
    ],
  },
  {
    id: "agent",
    title: "Run an agent",
    question: "What may this agent do?",
    description:
      "A seeded packet, one exact output and an independent grader make a bounded task inspectable.",
    nodes: [markdown, packet, host, runtime, grader, receipt],
    links: [
      ["markdown", "runtime"],
      ["packet", "runtime"],
      ["host", "runtime"],
      ["runtime", "grader"],
      ["grader", "receipt"],
    ],
  },
  {
    id: "workflow",
    title: "Review a workflow",
    question: "Which decision permits the next step?",
    description:
      "A durable pause binds the human decision to the exact owner and revision. Explore this contract without approving a real workflow.",
    nodes: [host, harness, runtime, review, receipt],
    links: [
      ["host", "harness"],
      ["harness", "runtime"],
      ["runtime", "review"],
      ["review", "receipt"],
    ],
  },
  {
    id: "pool",
    title: "Provider pool",
    question: "Why was this profile selected?",
    description:
      "Switching providers requires pre-work rejection proof. Partial or uncertain work ends the attempt.",
    nodes: [host, profiles, cooldown, runtime, stop, receipt],
    links: [
      ["host", "profiles"],
      ["profiles", "cooldown"],
      ["cooldown", "runtime"],
      ["runtime", "stop"],
      ["runtime", "receipt"],
    ],
  },
  {
    id: "results",
    title: "Results & live run",
    question: "What evidence supports completion?",
    description:
      "A completed process, a correct task and known usage are independent claims. Inspect the receipt before taking another action.",
    nodes: [packet, host, runtime, grader, receipt, stop],
    links: [
      ["packet", "host"],
      ["host", "runtime"],
      ["runtime", "grader"],
      ["grader", "receipt"],
      ["runtime", "stop"],
    ],
  },
];
export const tasks = [
  {
    id: "release-brief",
    title: "Release brief",
    output: "brief.json",
    preview:
      "Candidate 2.8.0, commit c42, fingerprint h42. Unit PASS; migration FAIL. Previous approval is stale. Correct the draft to HOLD with the failed check, evidence and platform follow-up.",
  },
  {
    id: "incident-handoff",
    title: "Incident handoff",
    output: "handoff.json",
    preview:
      "Errors elevated 09:06–09:22; rollback completed 09:15. Aggregate impact: 216 / 1,200 requests. Root cause unconfirmed. Correct the draft to MITIGATED, preserve uncertainty and include assigned follow-ups.",
  },
  {
    id: "invoice-sql",
    title: "Invoice SQL",
    output: "report.sql",
    preview:
      "As of 2026-10-23, count OPEN invoices due strictly before that date. Sum all payments per invoice, clamp at zero, exclude zero balances, aggregate by customer. Keep packet.json unchanged.",
  },
] as const;
export type Step = { node: string; label: string; explanation: string };
export type Scenario = {
  id: string;
  title: string;
  chapter: string;
  steps: Step[];
};
const step = (node: string, label: string, explanation: string): Step => ({
  node,
  label,
  explanation,
});
export const scenarios: Scenario[] = [
  {
    id: "complete",
    title: "Normal agent completion",
    chapter: "agent",
    steps: [
      step(
        "packet",
        "Input seeded",
        "The private workspace receives packet.json and the flawed draft.",
      ),
      step(
        "host",
        "Authority reviewed",
        "The host permits workspace-write for native or the exact API output path.",
      ),
      step(
        "runtime",
        "Execute once",
        "One eligible provider completes the bounded task.",
      ),
      step(
        "grader",
        "Grade independently",
        "The host checks the task contract, not the model’s claim.",
      ),
      step(
        "receipt",
        "Receipt retained",
        "Illustrative completion: inspect output, grading and usage independently.",
      ),
    ],
  },
  {
    id: "fallback",
    title: "Native rejection → local completion",
    chapter: "pool",
    steps: [
      step(
        "profiles",
        "Claude rejected before work",
        "A positive native rejection proof permits considering the next profile.",
      ),
      step(
        "profiles",
        "Codex rejected before work",
        "The next native profile also reports safe pre-work rejection.",
      ),
      step(
        "runtime",
        "Local profile selected",
        "Only now may the configured local/API profile execute.",
      ),
      step(
        "receipt",
        "Local completion",
        "This illustrates actual fallback rather than a cooldown skip.",
      ),
    ],
  },
  {
    id: "cooldown",
    title: "Later request skips cooldowns",
    chapter: "pool",
    steps: [
      step(
        "cooldown",
        "Persisted cooldown read",
        "A later independently authorized request reads the existing cooldown.",
      ),
      step(
        "profiles",
        "Native profiles skipped",
        "A controlled skip performs no provider attempt.",
      ),
      step(
        "runtime",
        "Eligible local selected",
        "The eligible profile may execute under its own policy.",
      ),
    ],
  },
  {
    id: "unavailable",
    title: "All providers unavailable",
    chapter: "pool",
    steps: [
      step(
        "cooldown",
        "Eligibility checked",
        "Every configured profile is unavailable or cooled.",
      ),
      step(
        "stop",
        "Capacity unavailable",
        "Return promptly with no automatic wait, dispatch or replay.",
      ),
    ],
  },
  {
    id: "partial",
    title: "Partial work stops the pool",
    chapter: "pool",
    steps: [
      step(
        "runtime",
        "Partial work observed",
        "Text or tool work has already occurred.",
      ),
      step(
        "stop",
        "Do not fall back",
        "Partial effects make another dispatch unsafe; retain uncertainty.",
      ),
      step(
        "receipt",
        "Evidence preserved",
        "Unknown usage stays unknown and the admission blocker survives restart.",
      ),
    ],
  },
  {
    id: "waiting",
    title: "Workflow awaiting review",
    chapter: "workflow",
    steps: [
      step(
        "harness",
        "Workflow admitted",
        "Trusted host identity and workflow state are durable.",
      ),
      step(
        "runtime",
        "Execution reaches gate",
        "A proposed action needs a separate human decision.",
      ),
      step(
        "review",
        "Awaiting exact decision",
        "The workflow pauses. Simulation cannot authorize the real action.",
      ),
    ],
  },
  {
    id: "stale",
    title: "Stale approval rejected",
    chapter: "workflow",
    steps: [
      step(
        "review",
        "Decision references old revision",
        "The decision does not match the current owner/revision/interaction.",
      ),
      step(
        "harness",
        "Approval rejected",
        "No resume or model dispatch occurs; the durable pause remains.",
      ),
    ],
  },
  {
    id: "resume",
    title: "Successful exact resume",
    chapter: "workflow",
    steps: [
      step(
        "review",
        "Exact decision accepted",
        "A trusted human decision matches the current interaction and revision.",
      ),
      step(
        "harness",
        "Resume once",
        "Harness resumes only the accepted durable workflow.",
      ),
      step(
        "receipt",
        "Retain outcome",
        "This is illustrative. Use the separate authenticated workflow demo for real review.",
      ),
    ],
  },
];
export function stepScenario(s: Scenario, index: number) {
  return Math.max(0, Math.min(index, s.steps.length - 1));
}
