# Explorer frontend verification

From this directory, with the repository's Python dependencies installed:

```sh
npm ci --ignore-scripts
npm test
npm run build
npx playwright install chromium
EXPLORER_PYTHON=/absolute/path/to/lab/.venv/bin/python npm run test:browser
```

`EXPLORER_PYTHON` defaults to `python3`; use an absolute executable path.
`EXPLORER_NODE` optionally selects the Node executable used for Playwright;
otherwise the runner uses its current Node executable. On Linux CI, install
browser system libraries with `npx playwright install --with-deps chromium`.

The browser suite starts and stops its own loopback documentation launcher per
test, with a private temporary launch file. It tests the actual single-use HTTP
bootstrap and browser-native fetch. Live UI tests intercept only status/run
responses using synthetic receipts after the real bootstrap. No model is
configured and no real execution is authorized. Python HTTP/coordinator tests
remain the authority-boundary coverage. Playwright tests live in `browser-tests/`;
Vitest's explicit `src` filter keeps the suites separate.
