# Current delivery status

Checkpoint: 2026-10-10. The released application remains Lab **0.2.0**. The
`codex/ecosystem-production` branch implements the next ecosystem milestones;
public SDK publication and Lab 0.3.0 adoption are pending.

Start with [native workflow usage](native-workflows.md), [persistence and
migration](persistence.md), [required release gates](release-gates.md) and
[bounded operational qualification](qualification.md). The
[2026-10-09 release ledger](verification/release-train-2026-10-09.md) records
the historical published baseline; its versions and measurements are preserved.

## Qualified SDK candidates

These runs qualify the original wheel and source bytes. They are candidate
artifacts, and the public package index is not yet verified available.

| SDK | Distribution version | Successful native qualification |
| --- | --- | --- |
| Core | `b3-prosaic` 0.4.0 | [38047286885](https://github.com/B3Cognition/prosaic/actions/runs/38047286885) |
| Runtime and recorder | `b3-prosaic-runtime` 0.8.0, `b3-prosaic-runtime-postgres` 0.2.0 | [38054282584](https://github.com/B3Cognition/prosaic-runtime/actions/runs/38054282584) |
| Harness and store | `b3-prosaic-harness` 0.7.0, `b3-prosaic-harness-postgres` 0.2.0 | [38055081837](https://github.com/B3Cognition/prosaic-harness/actions/runs/38055081837) |

Core ran Linux AMD64/ARM64 on Python 3.11–3.13 and Windows ownership checks.
Runtime also ran macOS on all three Python versions. Runtime and Harness ran
owned PostgreSQL 16/18 on both Linux architectures. Their required source,
installed-wheel and dependency-floor gates passed with exact receipt lineage.
Five original candidate wheels were independently installed into fresh Python
3.11 environments and passed public CLI/factory/tool smokes, payload ownership
audit, declared direct dependency floors and `pip check`.

Imports and CLI commands retain their existing names. The future normal index
channel uses the `b3-prosaic` family; migrate with a fresh environment or image.
The old and new distributions share import paths. The active manifest remains
`dependencies/releases.json`; the immutable 0.2.0 baseline remains
`dependencies/releases-lab-0.2.0.json`. No predicted release URL or checksum has
been inserted into either manifest.

For a checkout of this candidate branch, the supported pre-publication path
curates those exact successful runs into a separate manifest. Use Python 3.12
and an environment containing the hash-locked third-party dependencies; the
`gh` CLI must be authorized to read the public Actions artifacts:

```sh
python3.12 -m venv .venv-candidate
.venv-candidate/bin/python -m pip install --require-hashes -r dependencies/requirements.lock
.venv-candidate/bin/python scripts/prepare_sdk_candidates.py \
  --core-run-id 38047286885 --core-source aad4bf45ae1c242f4451700ca59b27280010573a \
  --runtime-run-id 38054282584 --runtime-source da3b43e12027b78d60b846c427021559b4927ba4 \
  --harness-run-id 38055081837 --harness-source 5b1e2bc0f56041122014a70e5865ff925e6559ab \
  --manifest .cache/sdk-candidate/manifest.json
.venv-candidate/bin/python scripts/install_dependencies.py --manifest .cache/sdk-candidate/manifest.json
.venv-candidate/bin/python scripts/audit_install.py --manifest .cache/sdk-candidate/manifest.json
.venv-candidate/bin/python -m pip check
export PATH="$PWD/.venv-candidate/bin:$PATH"
```

With Docker running, build the immutable candidate consumer and run a required
owned stack cell:

```sh
.venv-candidate/bin/python scripts/build_consumer.py \
  --manifest .cache/sdk-candidate/manifest.json --dependency-mode candidate \
  --tag prosaic-integration-lab:candidate
.venv-candidate/bin/python scripts/prepare_dependencies.py --manifest dependencies/releases-lab-0.2.0.json
.venv-candidate/bin/python -c 'from lab_runner.legacy_upgrade import build_baseline; build_baseline()'
.venv-candidate/bin/python scripts/required_acceptance.py \
  --candidate --candidate-manifest .cache/sdk-candidate/manifest.json \
  --postgres-version 16 --export reports/candidate-pg16.json
```

Repeat with PostgreSQL 18 on the actual host architecture. The four-cell CI
matrix separately verifies both Linux architectures. The private owned outputs
remain under `.lab`; only the sanitized gate summary is suitable for sharing.

## Implemented application behavior

The service can admit generated graphs composed from approved specialists,
retain exact host bundles and expose owner-authorized catalogue, proposal,
native-run and human-resume routes. SDK admission, input snapshots and human
validation happen through public installed APIs. Host credentials, asset paths,
tool implementations and journal namespaces stay private. Composition, inline
instructions and tool use require separate current grants.

Schema v3 adds immutable owned proposals, native references and a fenced business
operation journal. Migration uses a separate authorized role. Recovery retains
original billing and bundle identity; an uncertain start or effect needs explicit
operator reconciliation. The native fixture tests also cover incurred usage,
provider/tool budgets, receipt adoption and independent SQL effect uniqueness.

The complete local candidate source suite passed **497 tests** after the final
choice-transport correction. The corrected installed application and an exact
committed source archive each passed **89 focused tests** with the five original
qualified SDK wheels. The subsequent CI PATH correction has its own real
installed-CLI regression. Source/archive/wheel/installed parity covers 50 Python
modules, 78 public build inputs and the five original retained legacy assets.

The initial four-cell candidate run
[38055696518](https://github.com/B3Cognition/prosaic-integration-lab/actions/runs/38055696518)
verified all five SDK artifacts but failed before container testing because CI
had not selected the installed `prosaic` command. The corrected run
[38055931623](https://github.com/B3Cognition/prosaic-integration-lab/actions/runs/38055931623)
is the current qualification attempt. A started run is not a successful result.
Required cells are Linux AMD64/ARM64 × PostgreSQL 16/18, using the original Lab
0.2.0 implementation to generate upgrade fixtures. Local Docker preflight timed
out at its 15-second bound; no local native success is inferred.

## Publication and deployment boundaries

The GitHub `pypi` environments and tag restrictions are configured. An authorized
PyPI owner must register all five pending publishers using owner `B3Cognition`,
workflow `publish.yml` and environment `pypi`: Core in repository `prosaic`,
Runtime and its adapter in `prosaic-runtime`, Harness and its adapter in
`prosaic-harness`. Follow the
[SDK package-channel guide](https://github.com/B3Cognition/prosaic/blob/codex/ecosystem-production/docs/package-index.md).
No long-lived token is needed in chat.

After the candidate lab gate and owner registration succeed, promotion publishes
the original qualified bytes in dependency order: Core, Runtime/recorder,
Harness/store. Both GitHub and index downloads must match the receipts. Lab
0.3.0 then adopts verified public pins, builds a fresh consumer and reruns all
four cells against those published bytes before release.

Synthetic fixture success does not certify a live provider, customer billing,
deployment identity/TLS, long soak capacity, HA or PITR. Those qualifications
require their explicit profiles, private deployment inputs and actual evidence.
