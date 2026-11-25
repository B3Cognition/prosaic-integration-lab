# Core 0.5.0 SDK adoption — 2026-11-05

This source adopts published Core 0.5.0, Runtime 0.9.13 and Harness 0.9.8,
with Runtime recorder 0.3.0 and Harness store 0.4.1. Both active manifests select
the same five wheels. Exact PyPI downloads were verified against their original
GitHub release SHA256SUMS and source receipts; no SDK source checkout is installed.

The ordinary former manifest is retained at
`dependencies/releases-pre-core050-2026-11-05.json`; the former reasoning manifest
is retained at `dependencies/releases-reasoning-pre-core050-2026-11-05.json`.
The former packaged public benchmark profile is retained separately. Historical
private/candidate manifests, prompts, reports and live-study results are unchanged.

The new exact family retains conversation, context assembly and consumer
blueprint admission, all nine required real-stack lanes and all 103 context-enabled
conversation cases. Unknown or mixed families remain rejected. The third-party
requirements lock and the Lab package version remain unchanged.

Current benchmark freeze hashes bind the new SDK provenance. Original development
and evaluation freeze bytes are retained in `*-freeze-pre-core050.json`; corpus,
historical sources, prose, scoring and suite values are unchanged. These new
bindings do not requalify historical live results. The installed distribution
gate retains all four native/unified/fallback commands for the new train.

Runtime 0.9.13 gives explicit prose effort precedence over a profile default.
The native fixture now checks both explicit and omitted effort. Benchmark agent
bytes are unchanged and still omit effort, retaining their configured low default.

## Verification

- Baseline release/provenance checks: 39 passed before edits.
- Focused provenance/freeze/admission checks: 74 passed; distribution-gate checks:
  37 passed, including strict rejection of failed, live, incomplete or unclean
  native/unified receipts.
- `PATH="$PWD/.venv/bin:$PATH" .venv/bin/python -m pytest -q`: 2,086 passed.
- Separate `tests/native_acceptance`: 15 passed; `tests/reasoning_acceptance`:
  31 passed. Only owned native clients and loopback HTTP fixtures were used.
- `scripts/verify_public_adoption.py`: passed fresh ordinary PyPI resolution,
  exact archive and installed-payload hashes, import ownership, CLI startup,
  public factory construction, `pip check` and temporary cleanup for all five SDKs.
- `.venv/bin/python -m build`: wheel and source archive built successfully.
- `scripts/conversation_distribution_smoke.py --run-stack --postgres-version 16`:
  passed original-wheel and rebuilt-source consumers, installed native/unified,
  sandbox and benchmark checks, plus extracted-source conversation demo and
  context-enabled acceptance. Owned temporary cleanup verified.
- Explorer: 16 frontend unit tests, TypeScript/Vite build and 10 browser tests
  passed after updating only the displayed SDK badges and generated bundle;
  56 related Python checks also passed. Final original-wheel/rebuilt-source
  consumers were rerun successfully after the badge rebuild, without repeating
  the already qualified unchanged service stack.
- Required real-stack PostgreSQL 16 and 18: all nine lanes validated per major,
  334 passing cases each (668 total), zero skips and verified cleanup. Every
  actual raw receipt passed the existing strict gate; every task-owned stack's
  ownership manifest records verified cleanup.

| Required lane | PostgreSQL 16 | PostgreSQL 18 |
| --- | ---: | ---: |
| Audit | 88 | 88 |
| Identity | 20 | 20 |
| Ingress | 5 | 5 |
| Lago/accounting | 25 | 25 |
| Native persistence | 26 | 26 |
| Native workflow | 54 | 54 |
| Legacy upgrade | 10 | 10 |
| Capacity/restore qualification | 3 | 3 |
| Conversation and context | 103 | 103 |
| Total | 334 | 334 |

The first PostgreSQL 16 legacy launcher correctly failed before allocating
resources because the new host environment lacked the built Lab wheel. After
installing that wheel, the unchanged legacy-upgrade lane passed all ten cases;
its raw receipt and every other successful lane were checked with the existing
strict `lab_runner.gates.validate`. The original failed summary is preserved.
No SDK or application behavior was changed for this setup correction.

The real-stack commands used immutable consumer image
`sha256:76ea6bdb56881007c5a9af0b473ac8dbd05e49a5c1ffad5c963d229e1e3786b9`
and original historical baseline
`sha256:218ff9a17cd7b4cb3368abde96d70fecf02675a2a9aaccfa67d6bacd6d41bdfc`.
The service image contains the SDK/provenance/freeze update; subsequent
distribution-gate and displayed-badge changes are covered separately above.

Local Docker reports Linux/aarch64; the host uses Python 3.12.15. Native AMD64
and hosted CI results are separate from this local verification. No real-provider
inference or deployment readiness is certified by synthetic fixture checks.
