# Operator and owner recovery

Inspect a run from the terminal using a secret-managed bearer token environment
variable. The CLI prints only filtered owner views and accounting summaries:

```sh
.venv/bin/python -m lab_runner recover --url https://service.example \
  --token-env LAB_API_TOKEN --run-id "$LAB_RUN_ID" --action inspect
```

For an owned loopback fixture, explicitly add `--lab-http` and its printed A/B
URL. A private TLS CA can use `--ca-file`. Tokens never belong in command-line
arguments or saved reports. Origins cannot contain credentials/query/fragment,
responses are bounded, and HTTP redirects are never followed with a token.

Inspect the result/question and copy its exact reviewed revision. Apply one
explicit choice, with no automatic retry or revision refresh:

```sh
.venv/bin/python -m lab_runner recover --url https://service.example \
  --token-env LAB_API_TOKEN --run-id "$LAB_RUN_ID" --action approve \
  --expected-revision "$LAB_REVIEW_REVISION"
```

Use `reject` for the other available choice. A changed revision aborts before
mutation. Another owner cannot inspect or act on the run. Deferred approval after
capacity rejection retains the measured call and waiting review; inspect later
and explicitly apply the still-current revision. Approval adds no inference.

## Receipt and lease recovery

A killed worker can leave a lease until expiry. Preserve the run and wait for
the configured lease window, then inspect. For a running checkpoint, one explicit
`--action resume --expected-revision ...` lets Harness recover its durable receipt.
The CLI never polls/retries a mutation. A missing HTTP response does not mean an
operation failed to execute. Failed mutation requests include `mutation_outcome`
unknown or confirmed where known; inspect before deciding any further action.

If the SDK reports `retry_consent_required`, receipt evidence is missing and an
external effect may already have happened. First reconcile provider/tool evidence
using trusted operator context. Only then consider `--action retry` with both
the reviewed revision and `--acknowledge-effect-risk`. This is explicit consent,
not proof of no previous effect, and cannot bypass the SDK's durable token/call
budget. Unknown usage remains unknown after recovery and is never billed as zero.

## Uncertain starts and accounting

`start_uncertain` means ownership/start intent exists but no readable checkpoint.
The CLI allows inspection only. Never delete/reset the reservation or reuse a new
key as an automated workaround: that could redispatch an already completed effect.
Preserve frozen owner/scope/assets and inspect trusted durable ledger/receipt and
provider/tool evidence with an operator. Missing evidence does not establish
absence of an effect. If authority cannot establish a safe path, keep the run
uncertain, document the incident and escalate for human disposition. This interface
does not invent a checkpoint or attach an unrelated receipt.

Unknown or quarantined usage needs separate reconciliation from trusted provider
evidence and the recorder's public contract. Usage evidence cannot authorize
approval/retry, and known estimates are not customer invoices. The recovery CLI
does not edit observations or replace unknown coverage with zero.

## Credential delivery and fixture incidents

The offline privileged delivery job stages complete private generations. Each
contains runtime JSON and its pinned CA. Files sync after final ownership/mode,
then child and generation-parent directories sync before one atomic pointer
publication; the volume root syncs after replacement. The existing LAB_CONFIG
path and JSON contract remain compatible. A process killed before publication
leaves the previous generation active. A later delivery uses a fresh staging name.
Prior and orphan generations remain private for reviewed retirement; nothing
automatically deletes unexplained credential evidence. Retention qualification
is tracked separately. Replicas cannot mutate these read-only mounts.

Owned tests inject abrupt process loss before publication and after staging a
different CA, then restart B and prove the old matching configuration still
authorizes against real Keycloak TLS. Filesystem syscall-order regressions verify
required sync ordering. These do not simulate physical storage/host power loss.

An engine create timeout/failure can leave ownership outcome uncertain. Preserve
the original failed receipt and ownership intention. Inspect exact-owner engine
inventory and immutable labels before any cleanup; never prune unrelated resources.
Later empty inventories are separate evidence, not a rewritten successful run.

```sh
.venv/bin/python -m lab_runner test --candidate --mode operations --postgres-version 16
.venv/bin/python -m lab_runner test --candidate --mode operations --postgres-version 18
```

The full audit includes terminal recovery and delivery-abort coverage. Identity
mode adds the real Keycloak CA-generation interruption test. No provider credits
are consumed by these synthetic fixtures.
