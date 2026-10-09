# Safe operational evidence

Set an independent 64-character lowercase hexadecimal `metrics_token` in the
private service config to enable `GET /metrics`. It is not a user bearer token.
Existing credential-generation delivery accepts this field and protects it with
the config/CA generation. Metrics are disabled by default. Production scraping
must use the verified TLS ingress and operator credential; ordinary users cannot
access global metrics. Fixed labels exclude tenant, actor, run, prompt, URL and
credential values. Scrapes use the bounded read-admission pool and check actual
application/Harness/accounting readiness without repairs.

Observe in a separate terminal (credential in environment, never an argument):

```sh
.venv/bin/python -m lab_runner metrics --url https://service.example --token-env LAB_METRICS_TOKEN --samples 100 --interval 2
```

For an explicitly owned loopback fixture, use `--lab-http`; for a private CA,
pass `--ca-file`. TLS verification is mandatory for remote origins, redirects
and environment proxies are disabled, response size is bounded, and the viewer
rejects unknown metric names/labels/nonfinite values instead of printing arbitrary
HTTP data. This command performs no inference. Existing `watch --stream accounting`
continues to show per-user workload accounting evidence.

Request counts and latency buckets, admission occupancy/rejections and readiness
failures are process observations; they reset on restart. Request IDs are host
generated and returned as `X-Request-ID`. Structured logs include a trusted run
UUID only after ownership/reservation lookup and keyed tenant/provider-call
references. The operator credential keys those references across replicas; its
rotation changes references. With metrics disabled, references use an ephemeral
process key. Logs never copy inbound correlation IDs, bodies, tokens, raw provider
payloads or exception text. Admitted worker context preserves the request/run
relationship. Call references are emitted when owner-scoped usage is inspected.

`lab_accounting_unknown_observations_total` counts unknown calls seen in usage
inspection, including repeated inspections. It is not a unique call count,
durable global unresolved balance, zero-cost claim or invoice amount. For recovery,
inspect the run's durable owner-scoped accounting and keep unknown coverage intact.
Application reservation phase gauges are current database aggregate counts scoped
to namespace/environment; both replicas observe the same database, so do not add
them to estimate distinct runs. `started` is a reservation lifecycle marker, not
an active-worker count. A sustained reserved/starting backlog requires inspection;
it does not establish that an effect failed or authorize redispatch.

The [alert example](../configs/alerts.example.yml) covers scrape/readiness loss,
unknown observations, admission rejection and sustained reservation backlog.
Configure the monitoring job name/credential/CA and review thresholds for the
deployment SLO. Alert configuration is prepared; no remote monitor is deployed.
Scrape failure is itself an alert, rather than a green snapshot with missing data.

Engine errors retain only approved operation/phase, return code, timeout/failure
category and unknown outcome. Command arguments, environment, stderr and raw
tracebacks are excluded from receipt/CI exports. A failed network-create result
still requires exact-owned reconciliation and cannot certify cleanup from an
unavailable inventory. Historic failed receipts are retained unchanged.

```sh
.venv/bin/python -m lab_runner test --candidate --mode observability --postgres-version 16
.venv/bin/python -m lab_runner test --candidate --mode observability --postgres-version 18
```

These owned regressions cover terminal viewing, real saturation, actual grant
loss, unknown final usage, safe logs/correlation and a real engine failure. They
are required in the full audit lane.
