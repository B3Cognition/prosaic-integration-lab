import { defineConfig } from "@playwright/test";

export default defineConfig({
  // CI diff capture fetches the PR base with --depth=1, truncating the history
  // needed by the released-baseline qualification that follows these tests.
  captureGitInfo: { commit: false, diff: false },
  testDir: "./browser-tests",
  testMatch: "**/*.spec.ts",
  fullyParallel: false,
  workers: 1,
  timeout: 45_000,
  expect: { timeout: 8_000 },
  use: { browserName: "chromium", viewport: { width: 1440, height: 1000 } },
  reporter: "list",
});
