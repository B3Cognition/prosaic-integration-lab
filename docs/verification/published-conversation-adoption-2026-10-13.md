# Published conversation SDK adoption — 2026-10-13

The Lab 0.5.0 checkout now consumes the five published SDK wheels through
`dependencies/releases.json`. This adoption changes the dependency manifest,
usage documentation and two release expectations; the application engines are
unchanged. The former active manifest is preserved byte-for-byte as
`dependencies/releases-lab-0.4.0.json`. Historical candidate/platform receipts
retain their original identities.

## Exact published family

| Distribution | Version | Qualified source |
| --- | --- | --- |
| b3-prosaic | 0.4.1 | `6ac6cfdfd47dc70ecf68e441aa004f07c3be3822` |
| b3-prosaic-runtime | 0.9.0 | `a59621c5f30d766d1217b37df777d3876075dc34` |
| b3-prosaic-runtime-postgres | 0.3.0 | same Runtime source |
| b3-prosaic-harness | 0.8.0 | `f913fa18820554ffc5eb30a7bc4a8a6e302ed0ce` |
| b3-prosaic-harness-postgres | 0.3.0 | same Harness source |

The manifest records immutable files.pythonhosted.org URLs and original wheel
SHA256 values. Its SHA256 is
`75ecc658c2241e743fa0a075701b057452ee231ca8f507556b6df5c7bfed5534`.
Runtime publication
[38391849639](https://github.com/B3Cognition/prosaic-runtime/actions/runs/38391849639)
and Harness publication
[38393899829](https://github.com/B3Cognition/prosaic-harness/actions/runs/38393899829)
both completed successfully. The initial post-upload metadata checks encountered
PyPI propagation delays; failed-job retries verified actual public bytes and
completed the GitHub releases. Core's published bytes are unchanged.

## Fresh local verification

Host: macOS ARM64, Python 3.12.14. Owned Docker fixtures ran Linux ARM64 with
PostgreSQL 16 and 18. A new `.venv-published` installed the hashed third-party
lock and the five verified SDK wheels. The older `.venv` and prior caches were
preserved; no editable sibling SDK was used.

| Check | Observed result |
| --- | --- |
| Exact provenance and release gate tests | 32 passed |
| Installed wheel payload audit and `pip check` | passed |
| Ordinary PyPI adoption | passed; cache-free resolution/downloads, hashes, payloads, import ownership, CLI and public workflow construction verified |
| Complete unit/functional suite | 948 passed, zero skips; one existing Starlette deprecation warning |
| Released consumer image | built; exact SDK payloads audited |
| Native workflow demo, PostgreSQL 16 | passed, two synthetic calls, verified cleanup |
| Conversation demo, PostgreSQL 16 | passed, nine synthetic calls, one handler effect, verified cleanup |
| Native acceptance, PostgreSQL 18 | 54 passed, zero skips, verified cleanup |
| Conversation acceptance, PostgreSQL 18 | 95 passed, zero skips, verified cleanup |
| Lab wheel and rebuilt sdist consumer smoke | passed; isolated imports, payloads, public conversation construction, SDK capability, source assets and public index verified |

The initial sandboxed suite could not bind loopback fixture sockets. Rerunning
with loopback access exposed one stale CI test expectation (`enabled=false`);
the released manifest now correctly enables conversations. Updating that
expectation produced the complete passing suite. No upstream library change was
needed.

The consumer image used by both demos and acceptance runs was
`sha256:33b4df7afe78d49b924e5afd0a17233d265638c7fb8e8c451b2ec6500978530f`.
Fixture PostgreSQL images:

- 16: `postgres:16@sha256:ca0bd484cb98bf4b24eb1010e73fb3fcbd6714d240fbc1a10eea5b7dbecb641d`
- 18: `postgres:18@sha256:74935e72241653ca55e0414067e6d8763aceb8a810eb51b452253ec3dcfc4336`

Private owned evidence directories remain local under `.lab/`:

- Native demo: `b50a32e0015c4dcc86961337eb889cb7`.
- Conversation demo: `4c8bf89d51f6409ba61f526c7ba54e55`.
- Native acceptance: `de62f420e308481bb78ae2d3bba3dce9`.
- Conversation acceptance: `5ca493d4a58a4a328b2b7f194849db32`.

Safe adoption receipts remain in `reports/public-adoption-2026-10-13.json`
(SHA256 `fb9dc0b84aa0c851e44a08e56ba36126bea3af17c358bfece2ab78a8e78c78de`)
and `reports/conversation-distribution-2026-10-13.json`
(SHA256 `de103d83b0d74ab26b77d65fe66a77c6158dd42907ea02053aba2680e9ca05dd`).
The tested Lab wheel SHA256 was
`c844ffe5c5e2ef2ad24639721442fe7c1cf1f358cc26228df9ebeb04e2c94cb8`;
the tested source archive SHA256 was
`10569c809050a5c25823461f7aee84703fd597b6fbc7e3f22d08b0c30d09b511`.
Distribution smoke did not start an extracted-sdist stack in this local run;
the two real-stack acceptance runs above used the current checkout's consumer.

## What the examples demonstrate

The native demo follows discovery → admission → execution → review → resume →
completion. Admission and resume dispatch no model calls. Proposal/start replay,
invalid input, stale revision and owner isolation checks passed; two specialist
calls reconcile as complete and remain billing-ineligible synthetic evidence.

The conversation demo follows preference → correction → lookup → selection →
confirmation → approved operation. It retains complete public history, selects
`player-b` from the displayed order, confirms before executing one handler effect,
and uses two workers. Usage remains separated: seven complete conversation calls
and two complete workflow calls, with no unresolved calls. The required
conversation lane additionally exercises duplicate replay, owner/role isolation,
uncertain-effect recovery, concurrent workers and retained-session limits.

Applications should use `Conversation` for ordinary assistant turns, public
`WorkflowFactory` admission for generated graphs, and trusted host attachment
when a conversation needs workflow selection/review/approval. Endpoints, tools,
identity and accounting attribution come from trusted host configuration. Return
filtered public replies and require the exact current revision/interaction before
consequential work. The runnable recipes are in the
[README](../../README.md#try-a-conversation-and-an-approved-workflow),
[conversation guide](../conversations.md) and
[workflow construction guide](../consume-native-workflows.md).

## Reproduction and limits

After the fresh locked installation and manifest preparation in the README:

```sh
.venv-public/bin/python -m pytest -q
.venv-public/bin/python scripts/verify_public_adoption.py \
  --manifest dependencies/releases.json --export reports/public-adoption.json
.venv-public/bin/python scripts/build_consumer.py \
  --manifest dependencies/releases.json --dependency-mode released \
  --tag prosaic-integration-lab:dev
.venv-public/bin/python -m lab_runner demo --mode native --postgres-version 16
.venv-public/bin/python -m lab_runner demo --mode conversation --postgres-version 16
.venv-public/bin/python -m lab_runner test --mode native --postgres-version 18
.venv-public/bin/python -m lab_runner test --mode conversation --postgres-version 18
.venv-public/bin/python -m build
.venv-public/bin/python scripts/conversation_distribution_smoke.py \
  --wheel dist/prosaic_integration_lab-0.5.0-py3-none-any.whl \
  --sdist dist/prosaic_integration_lab-0.5.0.tar.gz \
  --manifest dependencies/releases.json --export reports/conversation-distribution.json
```

These are local released-SDK adoption results, not a new four-cell CI receipt or
the full nine-lane release gate. The current manifest activates conversation
acceptance in normal released CI. Lab 0.5.0 release, fresh AMD64/ARM64 ×
PostgreSQL 16/18 release qualification and hosted-provider certification remain
separate work. All inference in this adoption run was synthetic; the earlier
actual Qwen evidence remains in its own ledger.
