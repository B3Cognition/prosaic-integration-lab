import React, {
  useEffect,
  useRef,
  useState,
  useMemo,
  useCallback,
} from "react";
import { createRoot } from "react-dom/client";
import {
  ReactFlow,
  Handle,
  Position,
  Controls,
  MarkerType,
  type NodeProps,
  type Node,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import "@fontsource/ibm-plex-sans/latin-400.css";
import "@fontsource/ibm-plex-sans/latin-500.css";
import "@fontsource/ibm-plex-sans/latin-600.css";
import "@fontsource/ibm-plex-mono/latin-400.css";
import "./style.css";
import {
  chapters,
  scenarios,
  tasks,
  stepScenario,
  type LessonNode,
} from "./content";
import {
  ExplorerApi,
  RunIntent,
  takeBootstrap,
  canRun,
  allowanceLabel,
  canResetIntent,
  receiptToRefresh,
  type Status,
  type Receipt,
} from "./contracts";

// Consume the single-use launch secret before rendering or starting any request.
let launchSecret = takeBootstrap(
  window.location,
  window.history.replaceState.bind(window.history),
);
const api = new ExplorerApi();
type HandoffNode = Node<
  { lesson: LessonNode; active: boolean; stepLabel: string },
  "handoff"
>;
function Handoff({ data, selected }: NodeProps<HandoffNode>) {
  return (
    <div
      className={`handoff ${selected ? "selected" : ""} ${data.active ? "in-flight" : ""}`}
    >
      <Handle type="target" position={Position.Left} />
      <span className="node-kind">{data.lesson.kind}</span>
      <strong>{data.lesson.title}</strong>
      <span>{data.active ? data.stepLabel : data.lesson.output}</span>
      <Handle type="source" position={Position.Right} />
    </div>
  );
}
const nodeTypes = { handoff: Handoff };
function Code({ value }: { value: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <div className="code-wrap">
      <pre>
        <code>{value}</code>
      </pre>
      <button
        onClick={async () => {
          try {
            await navigator.clipboard.writeText(value);
            setCopied(true);
          } catch {
            setCopied(false);
          }
        }}
      >
        {copied ? "Copied" : "Copy"}
      </button>
    </div>
  );
}
function App() {
  const [chapterId, setChapterId] = useState("ecosystem"),
    [mode, setMode] = useState("Documentation"),
    [selected, setSelected] = useState("markdown"),
    [tab, setTab] = useState("User"),
    [textView, setTextView] = useState(
      () => window.matchMedia("(max-width: 740px)").matches,
    );
  const [scenarioId, setScenarioId] = useState("complete"),
    [index, setIndex] = useState(0),
    [playing, setPlaying] = useState(false),
    [menu, setMenu] = useState(false);
  const [connected, setConnected] = useState(false),
    [connecting, setConnecting] = useState(Boolean(launchSecret)),
    [status, setStatus] = useState<Status | null>(null),
    [error, setError] = useState(""),
    [lastUpdated, setLastUpdated] = useState("");
  const [taskId, setTaskId] = useState<string>("release-brief"),
    [timeout, setTimeoutChoice] = useState(180),
    [reviewing, setReviewing] = useState(false),
    [confirmed, setConfirmed] = useState(false),
    [pending, setPending] = useState(false),
    [intent, setIntent] = useState<RunIntent | null>(null),
    [receipt, setReceipt] = useState<Receipt | null>(null);
  const submitting = useRef(false),
    mounted = useRef(true),
    intentRef = useRef<RunIntent | null>(null);
  const chapter = chapters.find((c) => c.id === chapterId)!,
    scenario = scenarios.find((s) => s.id === scenarioId)!,
    current = scenario.steps[index],
    lesson = chapter.nodes.find((n) => n.id === selected) ?? chapter.nodes[0],
    task = tasks.find((t) => t.id === taskId)!;
  const refresh = async () => {
    try {
      const next = await api.status();
      if (!mounted.current) return;
      setStatus(next);
      setLastUpdated(new Date().toLocaleTimeString());
      setError("");
      const id = receiptToRefresh(next, intentRef.current, receipt);
      if (id) {
        const requestId = intentRef.current?.requestId;
        const r = await api.receipt(id);
        if (mounted.current && requestId === intentRef.current?.requestId)
          setReceipt(r);
      }
    } catch (e) {
      if (mounted.current) setError((e as Error).message);
    }
  };
  useEffect(() => {
    mounted.current = true;
    const secret = launchSecret;
    launchSecret = null;
    if (secret) {
      api
        .connect(secret)
        .then(() => {
          if (mounted.current) {
            setConnected(true);
            void refresh();
          }
        })
        .catch((e) => setError(e.message))
        .finally(() => setConnecting(false));
    }
    return () => {
      mounted.current = false;
    };
  }, []);
  useEffect(() => {
    if (!connected) return;
    const timer = window.setInterval(() => void refresh(), 2000);
    return () => window.clearInterval(timer);
  }, [connected, receipt?.runId, receipt?.state, intent?.requestId]);
  useEffect(() => {
    if (!playing || mode !== "Simulation") return;
    const timer = window.setInterval(
      () =>
        setIndex((i) => {
          if (i >= scenario.steps.length - 1) {
            setPlaying(false);
            return i;
          }
          return i + 1;
        }),
      1800,
    );
    return () => window.clearInterval(timer);
  }, [playing, mode, scenario]);
  useEffect(() => {
    if (
      mode === "Simulation" &&
      chapter.nodes.some((n) => n.id === current.node)
    )
      setSelected(current.node);
  }, [mode, index, scenarioId]);
  function changeChapter(id: string) {
    setChapterId(id);
    setSelected(chapters.find((c) => c.id === id)!.nodes[0].id);
    setPlaying(false);
    setMenu(false);
  }
  function chooseScenario(id: string) {
    const next = scenarios.find((s) => s.id === id)!;
    setScenarioId(id);
    setIndex(0);
    setPlaying(false);
    setMode("Simulation");
    changeChapter(next.chapter);
    setSelected(next.steps[0].node);
  }
  async function submit() {
    if (submitting.current || !confirmed || (!intent && !canRun(status)))
      return;
    const request = intent ?? new RunIntent(taskId, timeout);
    intentRef.current = request;
    setIntent(request);
    if (receipt?.requestId !== request.requestId) setReceipt(null);
    submitting.current = true;
    setPending(true);
    setError("");
    try {
      const result = await api.run(request);
      setReceipt(result);
      setReviewing(false);
      void refresh();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      submitting.current = false;
      setPending(false);
    }
  }
  async function cancel() {
    if (!receipt || pending) return;
    setPending(true);
    try {
      setReceipt(await api.cancel(receipt.runId));
      void refresh();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setPending(false);
    }
  }
  const nodes = useMemo<HandoffNode[]>(
    () =>
      chapter.nodes.map((n, i) => ({
        id: n.id,
        type: "handoff",
        position: { x: (i % 3) * 276, y: Math.floor(i / 3) * 200 },
        data: {
          lesson: n,
          active: mode === "Simulation" && current.node === n.id,
          stepLabel: current.label,
        },
        selected: lesson.id === n.id,
        draggable: false,
        connectable: false,
        ariaLabel: `${n.title}. ${n.summary}`,
      })),
    [chapter, mode, current.node, current.label, lesson.id],
  );
  // Inspector selection is explicit; never feed React Flow selection-store notifications
  // back into the controlled node list while playback changes the selected handoff.
  const inspectClick = useCallback(
    (_: React.MouseEvent, node: HandoffNode) => setSelected(node.id),
    [],
  );
  const inspectKeyboard = useCallback(
    (event: React.KeyboardEvent<HTMLDivElement>) => {
      if (event.key !== "Enter" && event.key !== " ") return;
      const id = (event.target as HTMLElement).closest<HTMLElement>(
        ".react-flow__node",
      )?.dataset.id;
      if (id && chapter.nodes.some((node) => node.id === id)) {
        event.preventDefault();
        setSelected(id);
      }
    },
    [chapter],
  );
  const edges = useMemo(
    () =>
      chapter.links.map(([source, target], i) => ({
        id: String(i),
        source,
        target,
        type: "smoothstep",
        markerEnd: { type: MarkerType.ArrowClosed, width: 16, height: 16 },
        style: {
          stroke: (
            mode === "Simulation"
              ? current.node === target
              : lesson.id === target || lesson.id === source
          )
            ? "#1b6c80"
            : "#bcc1c4",
          strokeWidth: (
            mode === "Simulation"
              ? current.node === target
              : lesson.id === target || lesson.id === source
          )
            ? 2
            : 1.3,
        },
      })),
    [chapter, mode, current.node, lesson.id],
  );
  return (
    <div className="app">
      <a href="#workspace" className="skip">
        Skip to chapter
      </a>
      <aside className={`sidebar ${menu ? "open" : ""}`} aria-label="Chapters">
        <a
          className="brand"
          href="#"
          onClick={(e) => {
            e.preventDefault();
            changeChapter("ecosystem");
          }}
        >
          <svg width="26" height="30" viewBox="0 0 26 30" aria-hidden="true">
            <path
              d="M4 3h13l5 5v19H4zM17 3v6h5M8 14h10M8 18h10M8 22h6"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.5"
            />
          </svg>
          <span>
            Prosaic <small>Explorer</small>
          </span>
        </a>
        <div className="nav-label">Learn the handoff</div>
        <nav>
          {chapters.map((c, i) => (
            <button
              key={c.id}
              aria-current={chapterId === c.id ? "page" : undefined}
              onClick={() => changeChapter(c.id)}
            >
              <span className="nav-number">0{i + 1}</span>
              {c.title}
            </button>
          ))}
        </nav>
        <div className="sidebar-foot">
          <strong>Local learning workspace</strong>
          <p>
            Core 0.4.1 · Runtime 0.9.8
            <br />
            Harness 0.9.4
          </p>
          <a
            href="https://github.com/B3Cognition/prosaic-integration-lab/blob/main/docs/quickstart.md"
            target="_blank"
            rel="noreferrer"
          >
            Prerequisites & setup ↗
          </a>
          <p>Documentation and simulation need no credentials or Docker.</p>
        </div>
      </aside>
      <div className="work-area">
        <header className="topbar">
          <button
            className="menu"
            onClick={() => setMenu(!menu)}
            aria-expanded={menu}
          >
            Chapters
          </button>
          <span className="breadcrumb">
            Integration lab <span>/</span> {chapter.title}
          </span>
          <span className="connection">
            {connecting
              ? "Connecting…"
              : connected
                ? "Host session connected"
                : "Documentation available offline"}
          </span>
        </header>
        <main className="sheet" id="workspace">
          <div className="title-row">
            <div>
              <h1>{chapter.question}</h1>
              <p>{chapter.description}</p>
            </div>
            <button
              onClick={() => setTextView(!textView)}
              aria-pressed={textView}
            >
              {textView ? "Graph view" : "List view"}
            </button>
          </div>
          <div className="mode-tabs" aria-label="Explorer mode">
            {["Documentation", "Simulation", "Live"].map((m) => (
              <button
                key={m}
                aria-pressed={mode === m}
                onClick={() => {
                  setMode(m);
                  setPlaying(false);
                  if (m === "Live") changeChapter("results");
                  if (m === "Simulation")
                    chooseScenario(
                      chapterId === "workflow"
                        ? "waiting"
                        : chapterId === "pool"
                          ? "fallback"
                          : "complete",
                    );
                }}
              >
                {m}
              </button>
            ))}
            <span>
              {mode === "Simulation"
                ? "Illustrative · no execution"
                : mode === "Live"
                  ? "One deliberately authorized invocation"
                  : "Read-only component map"}
            </span>
          </div>
          {mode === "Live" ? (
            <section className="live-surface">
              <div className="live-column">
                <div className="section-heading">
                  <h2>Bounded agent execution</h2>
                  {connected && (
                    <button onClick={() => void refresh()}>
                      Refresh status
                    </button>
                  )}
                </div>
                {!connected ? (
                  <div className="empty">
                    <strong>
                      {connecting
                        ? "Connecting to the launcher…"
                        : "Live execution is not connected"}
                    </strong>
                    <p>
                      Restart the launcher with explicit live configuration,
                      private evidence root and a durable allowance. Open its
                      private launch URL to connect this browser session.
                    </p>
                    <Code value="python -m lab_runner.explore --help" />
                    <p>
                      Learning and playback remain available. A connection never
                      starts a task.
                    </p>
                  </div>
                ) : !status ? (
                  <p role="status">Loading host policy…</p>
                ) : (
                  <>
                    <p className="freshness">
                      Host status{" "}
                      {lastUpdated ? `updated ${lastUpdated}` : "loading"}
                    </p>
                    {!status.liveEnabled && (
                      <div className="notice">
                        The launcher has live execution disabled. Restart with
                        explicit host configuration to enable it.
                      </div>
                    )}
                    {status.blocked && (
                      <div className="notice" role="alert">
                        Admission blocked: retained uncertain effects require
                        offline, receipt-bound operator reconciliation.
                        Documentation and receipts remain available.
                      </div>
                    )}
                    <label className="field">
                      Task
                      <select
                        aria-label="Task"
                        value={taskId}
                        disabled={
                          Boolean(intent) ||
                          pending ||
                          Boolean(status.activeRunId)
                        }
                        onChange={(e) => {
                          setTaskId(e.target.value);
                          setReviewing(false);
                          setConfirmed(false);
                        }}
                      >
                        {tasks.map((t) => (
                          <option key={t.id} value={t.id}>
                            {t.title}
                          </option>
                        ))}
                      </select>
                    </label>
                    <p>{task.preview}</p>
                    <dl>
                      <dt>Seeded inputs</dt>
                      <dd>packet.json + {task.output} draft</dd>
                      <dt>Exact API output grant</dt>
                      <dd>
                        <code>{task.output}</code> inside a new, server-owned
                        workspace
                      </dd>
                      <dt>Native permission</dt>
                      <dd>
                        workspace-write; separate from the exact API grant
                      </dd>
                    </dl>
                    <label className="field">
                      Local/API deadline
                      <select
                        aria-label="Local/API deadline"
                        value={timeout}
                        disabled={Boolean(intent) || pending}
                        onChange={(e) => {
                          setTimeoutChoice(Number(e.target.value));
                          setReviewing(false);
                          setConfirmed(false);
                        }}
                      >
                        <option value={180}>180 seconds</option>
                        <option value={240}>
                          240 seconds (host permitted)
                        </option>
                      </select>
                    </label>
                    <h3>Configured profile order</h3>
                    {status.profiles.length ? (
                      <ol className="profiles">
                        {status.profiles.map((p) => (
                          <li key={p.name}>
                            <strong>{p.name}</strong>
                            <span>
                              {p.backend} · {p.model}
                            </span>
                          </li>
                        ))}
                      </ol>
                    ) : (
                      <p>
                        No profiles configured. Live execution remains
                        unavailable.
                      </p>
                    )}
                    <h3>Host policy & allowance</h3>
                    <dl className="policies">
                      {Object.entries(status.policy).map(([key, value]) => (
                        <React.Fragment key={key}>
                          <dt>{key}</dt>
                          <dd>{String(value)}</dd>
                        </React.Fragment>
                      ))}
                    </dl>
                    <dl>
                      {status.allowance ? (
                        Object.entries(status.allowance).map(([key, value]) => (
                          <React.Fragment key={key}>
                            <dt>{allowanceLabel(key)}</dt>
                            <dd>{value ?? "Unknown"}</dd>
                          </React.Fragment>
                        ))
                      ) : (
                        <>
                          <dt>Allowance</dt>
                          <dd>Unavailable</dd>
                        </>
                      )}
                    </dl>
                    <p className="fine">
                      One run reserves up to 10 mixed units: two native attempts
                      + eight API requests. This is not a token or currency cap.
                      Native internal loops and subscription spend remain
                      opaque.
                    </p>
                    {!reviewing ? (
                      <button
                        className="primary"
                        disabled={
                          !canRun(status) ||
                          !status.profiles.length ||
                          Boolean(intent)
                        }
                        onClick={() => {
                          setReviewing(true);
                          setConfirmed(false);
                        }}
                      >
                        Review execution authority
                      </button>
                    ) : (
                      <section className="review">
                        <h3>Authorize one invocation</h3>
                        <p>
                          Run <strong>{task.title}</strong> against the seeded
                          packet with the profile order and policy above.
                          Local/API deadline {timeout}s; native 60s; pool 300s.
                          Caps: 3 profile attempts, 2 native; 8 API requests, 7
                          tool calls, 8 tool rounds; 65,536 API reported tokens.
                          API tools: read_file, write_file, edit_file; read only
                          this workspace, write only {task.output}.
                        </p>
                        <p>
                          Cancel interrupts owned work and preserves evidence.
                          It cannot undo effects. Unknown reservations remain
                          charged; uncertainty blocks new runs pending offline
                          reconciliation.
                        </p>
                        <label className="check">
                          <input
                            type="checkbox"
                            checked={confirmed}
                            disabled={pending}
                            onChange={(e) => setConfirmed(e.target.checked)}
                          />
                          I authorize this one bounded invocation.
                        </label>
                        <div className="actions">
                          <button
                            className="primary"
                            disabled={
                              !confirmed ||
                              pending ||
                              (!intent && !canRun(status))
                            }
                            onClick={() => void submit()}
                          >
                            {pending
                              ? "Submitting…"
                              : intent
                                ? "Retry same request"
                                : "Run once"}
                          </button>
                          <button
                            disabled={pending || Boolean(intent)}
                            onClick={() => setReviewing(false)}
                          >
                            Back
                          </button>
                        </div>
                      </section>
                    )}
                  </>
                )}
                {error && (
                  <div className="notice" role="alert">
                    <p>{error}</p>
                    {intent && reviewing && (
                      <p>
                        Retry preserves request ID{" "}
                        <code>{intent.requestId}</code>. Do not create another
                        request to resolve an uncertain response.
                      </p>
                    )}
                  </div>
                )}
              </div>
              <div className="receipt-column">
                <h2>Execution receipt</h2>
                {receipt ? (
                  <>
                    <div className="receipt-state">
                      <strong>{receipt.state}</strong>
                      <span>
                        Task grader:{" "}
                        {receipt.passed === true
                          ? "passed"
                          : receipt.passed === false
                            ? "failed"
                            : "not established"}
                      </span>
                    </div>
                    <dl>
                      <dt>Run</dt>
                      <dd>
                        <code>{receipt.runId}</code>
                      </dd>
                      <dt>Profile</dt>
                      <dd>{receipt.selectedProfile ?? "Not selected"}</dd>
                      <dt>Duration</dt>
                      <dd>
                        {receipt.durationMs === null
                          ? "Unknown"
                          : `${(receipt.durationMs / 1000).toFixed(1)} seconds`}
                      </dd>
                    </dl>
                    {receipt.state === "running" && (
                      <>
                        <p>
                          Waiting for actual host observations. Final-only
                          events appear after completion.
                        </p>
                        <button
                          disabled={pending}
                          onClick={() => void cancel()}
                        >
                          Cancel owned run
                        </button>
                      </>
                    )}
                    {receipt.failureReason && (
                      <p role="alert">{receipt.failureReason}</p>
                    )}
                    {receipt.recoveryRequired && (
                      <p className="notice">
                        Offline reconciliation required. No replay or allowance
                        refund.
                      </p>
                    )}
                    <h3>Observed events</h3>
                    {receipt.events.length ? (
                      <ol className="events">
                        {receipt.events.map((e, i) => (
                          <li key={i}>
                            <strong>{e.event}</strong>
                            {e.profile && <span>{e.profile}</span>}
                            {e.reason && <p>{e.reason}</p>}
                          </li>
                        ))}
                      </ol>
                    ) : (
                      <p>No provider observations available yet.</p>
                    )}
                    <h3>Usage evidence</h3>
                    <dl>
                      {Object.entries(receipt.usage).map(([key, value]) => (
                        <React.Fragment key={key}>
                          <dt>
                            {key === "knownTokens"
                              ? "Known tokens (coverage may be partial)"
                              : key}
                          </dt>
                          <dd>
                            {value === null
                              ? "Unknown"
                              : value.toLocaleString()}
                          </dd>
                        </React.Fragment>
                      ))}
                    </dl>
                    <h3>Retained task output</h3>
                    <pre className="output">
                      {receipt.output || "No output retained."}
                    </pre>
                    <p className="fine">
                      Output is rendered as text. Failed invocation output is
                      evidence, not a successful task.
                    </p>
                    {canResetIntent(intent, receipt, pending) && (
                      <button
                        onClick={() => {
                          if (
                            submitting.current ||
                            !canResetIntent(intentRef.current, receipt, pending)
                          )
                            return;
                          intentRef.current = null;
                          setIntent(null);
                          setReviewing(false);
                          setConfirmed(false);
                        }}
                      >
                        Prepare a new explicit request
                      </button>
                    )}
                  </>
                ) : (
                  <div className="empty">
                    <strong>No live run selected</strong>
                    <p>
                      Review the task and its host authority before Run. No
                      measured latency, output or usage exists yet.
                    </p>
                  </div>
                )}
                {status?.runs.length ? (
                  <>
                    <h3>Retained runs</h3>
                    <ul className="run-list">
                      {status.runs.map((r) => (
                        <li key={r.runId}>
                          <button
                            onClick={async () => {
                              try {
                                setReceipt(await api.receipt(r.runId));
                              } catch (e) {
                                setError((e as Error).message);
                              }
                            }}
                          >
                            {r.task} · {r.state}
                            <small>{r.runId}</small>
                          </button>
                        </li>
                      ))}
                    </ul>
                  </>
                ) : null}
              </div>
            </section>
          ) : (
            <>
              <div className="lesson-layout">
                <section
                  className="graph-column"
                  aria-label="Component handoff"
                >
                  {textView ? (
                    <ol className="lesson-list">
                      {chapter.nodes.map((n) => (
                        <li key={n.id}>
                          <button
                            onClick={() => setSelected(n.id)}
                            aria-pressed={lesson.id === n.id}
                          >
                            <span>{n.kind}</span>
                            <strong>{n.title}</strong>
                          </button>
                          <p>{n.summary}</p>
                          <p>
                            Input: {n.input} → Output: {n.output}
                          </p>
                        </li>
                      ))}
                    </ol>
                  ) : (
                    <div
                      className="graph"
                      onKeyDown={inspectKeyboard}
                      role="region"
                      aria-label={`${chapter.title} read-only graph. Tab through nodes, press Enter to inspect, or use List view.`}
                    >
                      <ReactFlow
                        key={chapter.id}
                        nodes={nodes}
                        edges={edges}
                        nodeTypes={nodeTypes}
                        onNodeClick={inspectClick}
                        nodesDraggable={false}
                        nodesConnectable={false}
                        edgesFocusable={false}
                        fitView
                        fitViewOptions={{ padding: 0.1 }}
                        minZoom={0.2}
                        maxZoom={1.4}
                        proOptions={{ hideAttribution: false }}
                      >
                        <Controls showInteractive={false} />
                      </ReactFlow>
                    </div>
                  )}
                  <div className="graph-caption">
                    <span>Markdown → permission → receipt</span>
                    <span>Read-only graph · select to inspect</span>
                  </div>
                  {mode === "Simulation" ? (
                    <section
                      className="playback"
                      aria-label="Scenario playback"
                    >
                      <label className="field">
                        Scenario
                        <select
                          aria-label="Scenario"
                          value={scenarioId}
                          onChange={(e) => chooseScenario(e.target.value)}
                        >
                          {scenarios.map((s) => (
                            <option key={s.id} value={s.id}>
                              {s.title}
                            </option>
                          ))}
                        </select>
                      </label>
                      <div className="step-title">
                        <span className="state-label">Simulation</span>
                        <strong>{current.label}</strong>
                        <span>
                          {index + 1} / {scenario.steps.length}
                        </span>
                      </div>
                      <p aria-live="polite">{current.explanation}</p>
                      <div className="actions">
                        <button
                          disabled={index === 0}
                          onClick={() => {
                            setPlaying(false);
                            setIndex((i) => stepScenario(scenario, i - 1));
                          }}
                        >
                          Previous
                        </button>
                        <button
                          onClick={() => {
                            if (index === scenario.steps.length - 1)
                              setIndex(0);
                            setPlaying(!playing);
                          }}
                        >
                          {playing ? "Pause" : "Play"}
                        </button>
                        <button
                          disabled={index === scenario.steps.length - 1}
                          onClick={() => {
                            setPlaying(false);
                            setIndex((i) => stepScenario(scenario, i + 1));
                          }}
                        >
                          Next
                        </button>
                        <button
                          onClick={() => {
                            setPlaying(false);
                            setIndex(0);
                          }}
                        >
                          Reset
                        </button>
                      </div>
                      <p className="fine">
                        Illustrative states only. Playback makes no network
                        requests, changes no real cooldowns and spends no
                        allowance.
                      </p>
                    </section>
                  ) : (
                    <section className="under-graph">
                      <h2>Trace the contract</h2>
                      <p>
                        {chapterId === "ecosystem"
                          ? "The Markdown describes the task. The host supplies permission. Runtime chooses a safe execution path; the receipt preserves what is known."
                          : "Select any component to inspect its inputs, outputs and authority boundary. The list view exposes the same material with standard keyboard controls."}
                      </p>
                      <button
                        onClick={() =>
                          chooseScenario(
                            chapterId === "workflow"
                              ? "waiting"
                              : chapterId === "pool"
                                ? "fallback"
                                : "complete",
                          )
                        }
                      >
                        Explore a scenario →
                      </button>
                    </section>
                  )}
                </section>
                <aside className="inspector" aria-label="Selected component">
                  <div className="inspector-heading">
                    <span className="node-kind">{lesson.kind}</span>
                    <h2>{lesson.title}</h2>
                  </div>
                  <div className="inspector-tabs">
                    {["User", "Developer"].map((t) => (
                      <button
                        key={t}
                        aria-pressed={tab === t}
                        onClick={() => setTab(t)}
                      >
                        {t}
                      </button>
                    ))}
                  </div>
                  <p>{lesson.summary}</p>
                  {tab === "User" ? (
                    <>
                      <h3>Receives</h3>
                      <p>{lesson.input}</p>
                      <h3>Produces</h3>
                      <p>{lesson.output}</p>
                    </>
                  ) : (
                    <>
                      <h3>Public contract / runnable reference</h3>
                      <Code value={lesson.code} />
                      <p className="fine">
                        Commands are copyable reference text. They are never
                        executed by this page.
                      </p>
                    </>
                  )}
                  <div className="boundary">
                    <h3>Authority boundary</h3>
                    <p>{lesson.boundary}</p>
                  </div>
                  <a
                    className="guide-link"
                    href={lesson.guide}
                    target="_blank"
                    rel="noreferrer"
                  >
                    Read the matching guide ↗
                  </a>
                  {chapterId === "workflow" && (
                    <p className="fine">
                      The existing browser/workflow demo has its own
                      authenticated service. This launcher does not resume
                      Harness workflows.
                    </p>
                  )}
                </aside>
              </div>
              <footer className="chapter-footer">
                <span>
                  {chapters.findIndex((c) => c.id === chapterId) + 1} of{" "}
                  {chapters.length} chapters
                </span>
                <div className="actions">
                  <button
                    disabled={chapterId === "ecosystem"}
                    onClick={() =>
                      changeChapter(
                        chapters[
                          chapters.findIndex((c) => c.id === chapterId) - 1
                        ].id,
                      )
                    }
                  >
                    Previous chapter
                  </button>
                  <button
                    disabled={chapterId === "results"}
                    onClick={() =>
                      changeChapter(
                        chapters[
                          chapters.findIndex((c) => c.id === chapterId) + 1
                        ].id,
                      )
                    }
                  >
                    Next chapter →
                  </button>
                </div>
              </footer>
            </>
          )}
        </main>
      </div>
    </div>
  );
}
createRoot(document.getElementById("root")!).render(<App />);
