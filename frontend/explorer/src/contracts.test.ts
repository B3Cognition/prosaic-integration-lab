import { describe, it, expect, vi } from "vitest";
import { chapters, scenarios, tasks, stepScenario } from "./content";
import {
  ExplorerApi,
  RunIntent,
  takeBootstrap,
  canRun,
  shouldPoll,
  allowanceLabel,
  canResetIntent,
  receiptToRefresh,
  type Receipt,
  type Status,
} from "./contracts";
describe("educational content", () => {
  it("offers five distinct real lessons with guides and inspectable boundaries", () => {
    expect(chapters).toHaveLength(5);
    for (const c of chapters) {
      expect(c.nodes.length).toBeGreaterThan(3);
      for (const n of c.nodes) {
        expect(n.guide).toMatch(/^https:\/\/github.com\/B3Cognition\//);
        expect(n.boundary.length).toBeGreaterThan(25);
      }
    }
  });
  it("has eight bounded, reversible local scenarios", () => {
    expect(scenarios).toHaveLength(8);
    for (const s of scenarios) {
      expect(stepScenario(s, 999)).toBe(s.steps.length - 1);
      expect(stepScenario(s, -99)).toBe(0);
      expect(s.steps.every((x) => x.explanation && x.node)).toBe(true);
    }
  });
  it("uses the exact task and output allowlist", () =>
    expect(tasks.map((x) => [x.id, x.output])).toEqual([
      ["release-brief", "brief.json"],
      ["incident-handoff", "handoff.json"],
      ["invoice-sql", "report.sql"],
    ]));
});
describe("browser authority", () => {
  it("calls default native fetch with its global receiver", async () => {
    const receivers: unknown[] = [];
    vi.stubGlobal("fetch", function (this: unknown) {
      receivers.push(this);
      if (this !== globalThis) throw new TypeError("Illegal invocation");
      return Promise.resolve({
        ok: true,
        json: async () => ({ token: "session" }),
      });
    });
    try {
      await new ExplorerApi().connect("launch");
      expect(receivers).toEqual([globalThis]);
    } finally {
      vi.unstubAllGlobals();
    }
  });
  it("removes bootstrap before any asynchronous work", () => {
    const replace = vi.fn();
    expect(
      takeBootstrap(
        { hash: "#connect=private%2Bvalue", pathname: "/", search: "?a=1" },
        replace,
      ),
    ).toBe("private+value");
    expect(replace).toHaveBeenCalledWith(null, "", "/?a=1");
  });
  it("never invents credentials for documentation mode", () =>
    expect(
      takeBootstrap({ hash: "", pathname: "/", search: "" }, vi.fn()),
    ).toBeNull());
  it("retains exact request identity for transport retries, and forbids edits", () => {
    const intent = new RunIntent("release-brief", 180, "fixed-id");
    expect(intent.body()).toEqual({
      requestId: "fixed-id",
      task: "release-brief",
      localTimeoutSeconds: 180,
      confirmed: true,
    });
    expect(intent.body()).toEqual(intent.body());
    expect(() => new RunIntent("arbitrary", 180)).toThrow();
    expect(() => new RunIntent("invoice-sql", 241)).toThrow();
  });
  it("generates the HTTP contract request identity as 32 lower-case hex characters", () =>
    expect(new RunIntent("release-brief", 180).body().requestId).toMatch(
      /^[0-9a-f]{32}$/,
    ));
  it("does not dispatch on connection, status, or receipt polling", async () => {
    const send = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ token: "session" }),
    });
    const api = new ExplorerApi(send);
    await api.connect("launch");
    await api.status();
    await api.receipt("r1");
    expect(send.mock.calls.map((c) => [c[0], c[1]?.method ?? "GET"])).toEqual([
      ["/api/bootstrap", "POST"],
      ["/api/status", "GET"],
      ["/api/runs/r1", "GET"],
    ]);
  });
  it("POSTs only the deliberately reviewed intent and retains it on retry", async () => {
    const send = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ token: "session" }),
    });
    const api = new ExplorerApi(send);
    await api.connect("launch");
    const intent = new RunIntent("invoice-sql", 240, "retry-me");
    await api.run(intent);
    await api.run(intent);
    expect(send.mock.calls[1][1].body).toBe(send.mock.calls[2][1].body);
    expect(send.mock.calls[1][1].headers.Authorization).toBe("Bearer session");
  });
  it("blocks absent authority, cooldown/admission blocker, capacity and missing allowance", () => {
    expect(canRun(null)).toBe(false);
    expect(
      canRun({
        liveEnabled: true,
        blocked: true,
        activeRunId: null,
        allowance: { remaining: 20 },
      } as never),
    ).toBe(false);
    expect(
      canRun({
        liveEnabled: true,
        blocked: false,
        activeRunId: "run",
        allowance: { remaining: 20 },
      } as never),
    ).toBe(false);
    expect(
      canRun({
        liveEnabled: true,
        blocked: false,
        activeRunId: null,
        allowance: null,
      } as never),
    ).toBe(false);
    expect(
      canRun({
        liveEnabled: true,
        blocked: false,
        activeRunId: null,
        allowance: { remaining: 9 },
      } as never),
    ).toBe(false);
    expect(
      canRun({
        liveEnabled: true,
        blocked: false,
        activeRunId: null,
        allowance: { remaining: 10 },
      } as never),
    ).toBe(true);
  });
  it("polls only authenticated reads; terminal receipts stop active polling", () => {
    expect(shouldPoll(false, "running")).toBe(false);
    expect(shouldPoll(true, "running")).toBe(true);
    expect(shouldPoll(true, "uncertain")).toBe(false);
    expect(shouldPoll(true, "completed")).toBe(false);
  });
  it("distinguishes unknown reservation counts from mixed-unit allowance", () => {
    expect(allowanceLabel("unknown")).toBe("Unknown reservations");
    expect(allowanceLabel("remaining")).toBe("remaining mixed units");
  });
  it("cannot discard an unresolved identity using an old terminal receipt or while POST is pending", () => {
    const intent = new RunIntent("release-brief", 180, "current");
    const old = { requestId: "previous", state: "completed" } as Receipt;
    const matching = { ...old, requestId: "current" } as Receipt;
    expect(canResetIntent(intent, old, false)).toBe(false);
    expect(canResetIntent(intent, matching, true)).toBe(false);
    expect(
      canResetIntent(intent, { ...matching, state: "running" }, false),
    ).toBe(false);
    expect(canResetIntent(intent, null, false)).toBe(false);
    expect(canResetIntent(intent, matching, false)).toBe(true);
  });
  it("recovers the exact terminal receipt after a lost POST response without another dispatch", async () => {
    const intent = new RunIntent("release-brief", 180, "current");
    const prior = {
      runId: "old-run",
      requestId: "previous",
      state: "completed",
    } as Receipt;
    const terminal = {
      runId: "current-run",
      requestId: "current",
      state: "completed",
    } as Receipt;
    const status = { activeRunId: null, runs: [prior, terminal] } as Status;
    expect(receiptToRefresh(status, intent, prior)).toBe("current-run");
    const send = vi
      .fn()
      .mockResolvedValue({ ok: true, json: async () => terminal });
    await new ExplorerApi(send).receipt(
      receiptToRefresh(status, intent, prior)!,
    );
    expect(send.mock.calls).toHaveLength(1);
    expect(send.mock.calls[0][0]).toBe("/api/runs/current-run");
    expect(send.mock.calls[0][1].method).toBeUndefined();
    expect(
      receiptToRefresh({ ...status, runs: [prior] }, intent, prior),
    ).toBeNull();
  });
});
