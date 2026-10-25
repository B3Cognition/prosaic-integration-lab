export type RunState =
  | "running"
  | "completed"
  | "failed"
  | "uncertain"
  | "cancelled";
export interface Receipt {
  runId: string;
  requestId: string;
  task: string;
  state: RunState;
  passed: boolean | null;
  durationMs: number | null;
  selectedProfile: string | null;
  events: { event: string; profile?: string; reason?: string }[];
  output: string;
  failureReason: string | null;
  recoveryRequired: boolean;
  usage: {
    nativeAttempts: number | null;
    apiRequests: number | null;
    apiToolCalls: number | null;
    knownTokens: number | null;
  };
  startedAt: number;
  receiptSha256: string;
}
export interface Status {
  liveEnabled: boolean;
  profiles: { name: string; backend: string; model: string }[];
  policy: Record<string, string | number>;
  allowance: Record<string, number | null> | null;
  blocked: boolean;
  activeRunId: string | null;
  runs: (Receipt | { runId: string; task: string; state: RunState })[];
}
export function takeBootstrap(
  location: Pick<Location, "hash" | "pathname" | "search">,
  replace: History["replaceState"],
) {
  const hash = location.hash;
  if (!hash.startsWith("#connect=")) return null;
  replace(null, "", location.pathname + location.search);
  try {
    return decodeURIComponent(hash.slice(9));
  } catch {
    return null;
  }
}
export class RunIntent {
  readonly requestId: string;
  readonly task: string;
  readonly localTimeoutSeconds: number;
  constructor(
    task: string,
    timeout: number,
    id: string = crypto.randomUUID().replaceAll("-", ""),
  ) {
    if (
      !["release-brief", "incident-handoff", "invoice-sql"].includes(task) ||
      ![180, 240].includes(timeout)
    )
      throw new Error("Unsupported task or deadline");
    this.task = task;
    this.localTimeoutSeconds = timeout;
    this.requestId = id;
    Object.freeze(this);
  }
  body() {
    return {
      requestId: this.requestId,
      task: this.task,
      localTimeoutSeconds: this.localTimeoutSeconds,
      confirmed: true,
    };
  }
}
export function canRun(status: Status | null) {
  return Boolean(
    status?.liveEnabled &&
      !status.blocked &&
      !status.activeRunId &&
      typeof status.allowance?.remaining === "number" &&
      status.allowance.remaining >= 10,
  );
}
export function shouldPoll(authenticated: boolean, state?: RunState) {
  return authenticated && state === "running";
}
export function allowanceLabel(key: string) {
  return key === "unknown" ? "Unknown reservations" : `${key} mixed units`;
}
export function canResetIntent(
  intent: RunIntent | null,
  receipt: Receipt | null,
  pending: boolean,
) {
  return Boolean(
    !pending &&
      intent &&
      receipt?.requestId === intent.requestId &&
      receipt.state !== "running",
  );
}
export function receiptToRefresh(
  status: Status,
  intent: RunIntent | null,
  receipt: Receipt | null,
): string | null {
  const matching = intent
    ? status.runs.find(
        (run) => "requestId" in run && run.requestId === intent.requestId,
      )
    : undefined;
  return (
    matching?.runId ??
    status.activeRunId ??
    (receipt?.state === "running" ? receipt.runId : null)
  );
}
export class ExplorerApi {
  private token: string | null = null;
  constructor(private send: typeof fetch = globalThis.fetch.bind(globalThis)) {}
  async connect(launch: string) {
    const result = await this.request<{ token: string }>("/api/bootstrap", {
      method: "POST",
      headers: { "X-Explorer-Launch": launch },
    });
    this.token = result.token;
  }
  private async request<T>(url: string, init: RequestInit = {}): Promise<T> {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...(init.headers as Record<string, string>),
    };
    if (this.token) headers.Authorization = `Bearer ${this.token}`;
    let response: Response;
    try {
      response = await this.send(url, {
        ...init,
        headers,
        cache: "no-store",
        credentials: "omit",
        referrerPolicy: "no-referrer",
      });
    } catch {
      throw new Error(
        "Connection lost. A submitted request may still be running. Retry the same request identity.",
      );
    }
    if (!response.ok)
      throw new Error(
        `Explorer request failed (${response.status}). Inspect status before authorizing another request.`,
      );
    return response.json();
  }
  status() {
    return this.request<Status>("/api/status");
  }
  receipt(id: string) {
    return this.request<Receipt>(`/api/runs/${encodeURIComponent(id)}`);
  }
  run(intent: RunIntent) {
    return this.request<Receipt>("/api/runs", {
      method: "POST",
      body: JSON.stringify(intent.body()),
    });
  }
  cancel(id: string) {
    return this.request<Receipt>(`/api/runs/${encodeURIComponent(id)}/cancel`, {
      method: "POST",
      body: "{}",
    });
  }
}
