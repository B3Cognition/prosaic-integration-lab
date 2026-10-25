import { test as base, expect, type Page } from "@playwright/test";
import { spawn } from "node:child_process";
import { mkdtemp, chmod, readFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";

// Every test owns a docs-only Python launcher: never configure an actual model.
const test = base.extend<{ launcher: { url: string; origin: string } }>({
  launcher: async ({}, use) => {
    const directory = await mkdtemp(
      join(tmpdir(), "prosaic-explorer-browser-"),
    );
    await chmod(directory, 0o700);
    const file = join(directory, "launch.json");
    const child = spawn(
      process.env.EXPLORER_PYTHON || "python3",
      ["-m", "lab_runner.explore", "--no-open", "--launch-file", file],
      { cwd: resolve("../.."), stdio: "ignore" },
    );
    let exit = false;
    const closed = new Promise<void>((done) =>
      child.once("exit", () => {
        exit = true;
        done();
      }),
    );
    child.on("error", () => {
      exit = true;
    });
    try {
      let url = "";
      for (let i = 0; i < 100; i++) {
        if (exit)
          throw new Error(
            "Owned documentation launcher exited before readiness",
          );
        try {
          const record = JSON.parse(await readFile(file, "utf8"));
          if ((await fetch(new URL("/healthz", record.url))).ok) {
            url = record.url;
            break;
          }
        } catch {
          /* Private launch file and loopback socket may not yet exist. */
        }
        await new Promise((done) => setTimeout(done, 100));
      }
      if (!url)
        throw new Error(
          "Documentation launcher readiness timed out; set EXPLORER_PYTHON to the installed test environment",
        );
      await use({ url, origin: new URL(url).origin });
    } finally {
      if (!exit) child.kill("SIGTERM");
      await Promise.race([
        closed,
        new Promise((done) => setTimeout(done, 3000)),
      ]);
      if (!exit) {
        child.kill("SIGKILL");
        await closed;
      }
      await rm(directory, { recursive: true });
    }
  },
});

async function connect(page: Page, url: string) {
  const bootstrap = page.waitForResponse((response) =>
    response.url().endsWith("/api/bootstrap"),
  );
  await page.goto(url);
  expect((await bootstrap).status()).toBe(200);
  await expect(
    page.getByText("Host session connected", { exact: true }),
  ).toBeVisible();
  expect(new URL(page.url()).hash).toBe("");
  expect(
    await page.evaluate(() => [localStorage.length, sessionStorage.length]),
  ).toEqual([0, 0]);
}

test("all eight scenarios, playback and keyboard selection stay mounted without dispatch", async ({
  page,
  launcher,
}) => {
  const errors: string[] = [],
    mutations: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  page.on("request", (request) => {
    if (request.method() !== "GET") mutations.push(request.method());
  });
  await page.goto(launcher.origin);
  await page.getByRole("button", { name: "Simulation", exact: true }).click();
  const select = page.getByRole("combobox", { name: "Scenario", exact: true });
  await expect(select).toBeVisible();
  const choices = await select
    .locator("option")
    .evaluateAll((nodes) => nodes.map((node) => node.value));
  expect(choices).toHaveLength(8);
  for (const value of choices) {
    await select.selectOption(value);
    const progress = page.locator(".step-title > span:last-child");
    await expect(progress).toHaveText(/^1 \/ /);
    for (let count = 0; count < 10; count++) {
      const next = page.getByRole("button", { name: "Next", exact: true });
      if (await next.isDisabled()) break;
      const [step, total] = (await progress.innerText()).split("/").map(Number);
      await next.click();
      await expect(progress).toHaveText(`${step + 1} / ${total}`);
    }
    await page.getByRole("button", { name: "Previous", exact: true }).click();
    await page.getByRole("button", { name: "Reset", exact: true }).click();
    await page.getByRole("button", { name: "Play", exact: true }).click();
    await page.getByRole("button", { name: "Pause", exact: true }).click();
    await expect(page.locator("h1")).toHaveCount(1);
  }
  await page
    .getByRole("button", { name: "Documentation", exact: true })
    .click();
  const node = page.locator(".react-flow__node").last();
  await expect(node.locator("strong")).toBeVisible();
  await expect(node.locator("strong")).toHaveText(/\S/);
  const title = await node.locator("strong").innerText();
  await node.focus();
  await node.press("Enter");
  await expect(
    page
      .getByRole("complementary", { name: "Selected component" })
      .getByRole("heading", { name: title, exact: true }),
  ).toBeVisible();
  expect(errors).toEqual([]);
  expect(mutations).toEqual([]);
});

function receipt(requestId: string, state = "running") {
  return {
    runId: requestId,
    requestId,
    task: "release-brief",
    state,
    passed: null,
    durationMs: null,
    selectedProfile: "fixture-local",
    events: [{ event: "selected", profile: "fixture-local" }],
    output: '<img src=x onerror="window.injected=true">',
    failureReason: null,
    recoveryRequired: false,
    usage: {
      nativeAttempts: 0,
      apiRequests: 1,
      apiToolCalls: 0,
      knownTokens: null,
    },
    startedAt: 1,
    receiptSha256: "fixture-digest",
  };
}
function status() {
  return {
    liveEnabled: true,
    profiles: [{ name: "fixture-local", backend: "api", model: "synthetic" }],
    policy: {
      nativeTimeoutSeconds: 60,
      localTimeoutSeconds: 180,
      poolTimeoutSeconds: 300,
      maxAttempts: 3,
      maxNativeAttempts: 2,
      maxApiRequests: 8,
      maxToolCalls: 7,
      maxToolRounds: 8,
      maxReportedTokens: 65536,
      nativePermissions: "workspace-write",
    },
    allowance: { maximum: 20, retained: 0, remaining: 20, unknown: 0 },
    blocked: false,
    activeRunId: null as string | null,
    runs: [] as ReturnType<typeof receipt>[],
  };
}
async function authorize(page: Page) {
  await page
    .getByRole("button", { name: "Review execution authority", exact: true })
    .click();
  await expect(
    page.getByRole("button", { name: "Run once", exact: true }),
  ).toBeDisabled();
  await page.getByRole("checkbox").check();
  await page.getByRole("button", { name: "Run once", exact: true }).click();
}

test("real bootstrap enables only explicitly reviewed synthetic execution, escaping output and preserving cancel uncertainty", async ({
  page,
  launcher,
}) => {
  const host = status(),
    bodies: any[] = [],
    errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.route("**/api/status", (route) => {
    expect(route.request().headers().authorization).toMatch(/^Bearer .+/);
    return route.fulfill({ json: host });
  });
  await page.route("**/api/runs", async (route) => {
    const body = route.request().postDataJSON();
    bodies.push(body);
    const row = receipt(body.requestId);
    host.runs.push(row);
    host.activeRunId = row.runId;
    await route.fulfill({ json: row });
  });
  await page.route("**/api/runs/*", (route) =>
    route.fulfill({
      json: host.runs.find(
        (row) => row.runId === route.request().url().split("/").pop(),
      ),
    }),
  );
  await page.route("**/api/runs/*/cancel", (route) => {
    expect(route.request().method()).toBe("POST");
    const row = host.runs[0];
    row.state = "uncertain";
    row.recoveryRequired = true;
    host.activeRunId = null;
    host.blocked = true;
    host.allowance.unknown = 1;
    return route.fulfill({ json: row });
  });
  await connect(page, launcher.url);
  await page.getByRole("button", { name: "Live", exact: true }).click();
  await page
    .getByRole("combobox", { name: "Local/API deadline", exact: true })
    .selectOption("240");
  expect(bodies).toHaveLength(0);
  await authorize(page);
  await expect(
    page.getByRole("button", { name: "Cancel owned run", exact: true }),
  ).toBeVisible();
  expect(bodies).toHaveLength(1);
  expect(bodies[0]).toEqual({
    requestId: expect.stringMatching(/^[0-9a-f]{32}$/),
    task: "release-brief",
    localTimeoutSeconds: 240,
    confirmed: true,
  });
  await expect(page.locator(".output")).toHaveText(host.runs[0].output);
  expect(await page.locator(".output img").count()).toBe(0);
  expect(await page.evaluate(() => (window as any).injected)).toBeUndefined();
  await page
    .getByRole("button", { name: "Cancel owned run", exact: true })
    .click();
  await expect(page.getByText(/Admission blocked:/)).toBeVisible();
  await page
    .getByRole("button", {
      name: "Prepare a new explicit request",
      exact: true,
    })
    .click();
  await expect(
    page.getByRole("button", {
      name: "Review execution authority",
      exact: true,
    }),
  ).toBeDisabled();
  expect(bodies).toHaveLength(1);
  expect(errors).toEqual([]);
});

test("response loss retains request identity, pending historical receipts cannot reset it, and polling recovers the terminal receipt", async ({
  page,
  launcher,
}) => {
  const host = status(),
    bodies: any[] = [];
  let attempts = 0,
    release: (() => void) | undefined;
  await page.route("**/api/status", (route) => route.fulfill({ json: host }));
  await page.route("**/api/runs/*", (route) =>
    route.fulfill({
      json: host.runs.find(
        (row) => row.runId === route.request().url().split("/").pop(),
      ),
    }),
  );
  await page.route("**/api/runs", async (route) => {
    const body = route.request().postDataJSON();
    bodies.push(body);
    attempts++;
    if (attempts === 2) {
      await new Promise<void>((done) => {
        release = done;
      });
      await route.abort();
      return;
    }
    const row = receipt(body.requestId, "completed");
    host.runs.push(row);
    if (attempts === 4) await route.abort();
    else await route.fulfill({ json: row });
  });
  await connect(page, launcher.url);
  await page.getByRole("button", { name: "Live", exact: true }).click();
  await authorize(page);
  await page
    .getByRole("button", {
      name: "Prepare a new explicit request",
      exact: true,
    })
    .click();
  await authorize(page);
  await expect.poll(() => bodies.length).toBe(2);
  await expect(
    page.getByRole("button", {
      name: "Prepare a new explicit request",
      exact: true,
    }),
  ).toHaveCount(0);
  release!();
  const retry = page.getByRole("button", {
    name: "Retry same request",
    exact: true,
  });
  await expect(retry).toBeEnabled();
  await retry.click();
  await expect.poll(() => bodies.length).toBe(3);
  expect(bodies[1]).toEqual(bodies[2]);
  await page
    .getByRole("button", {
      name: "Prepare a new explicit request",
      exact: true,
    })
    .click();
  await authorize(page);
  await expect.poll(() => bodies.length).toBe(4);
  await expect(page.locator(".receipt-column code")).toHaveText(
    bodies[3].requestId,
  );
  await expect(
    page.getByRole("button", {
      name: "Prepare a new explicit request",
      exact: true,
    }),
  ).toBeVisible();
  expect(bodies).toHaveLength(4);
});
