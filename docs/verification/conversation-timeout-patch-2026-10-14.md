# Conversation timeout patch — 2026-10-14

## Root cause and regression

The OpenAI-compatible provider's socket/deadline timeout returns legacy exit
status `-1`. Runtime's conversation turn originally forwarded that status to
Harness, whose existing sealed receipt contract requires a nonnegative status.
This produced HTTP 503 `store_corrupt` while the saved session remained valid.

Runtime 0.9.3 converts negative timed-out statuses to `124` at the turn result
boundary. It preserves the run/CLI result and on-disk receipt format, records
failure `timeout`, and does not retry the provider. The implementation commit is
`01f1a96a77a1bb5b85f600d64d71ca3a00847662`; the exact release candidate includes
workflow artifact filename corrections at
`342d4fa40068e2b3a48165ea29cfcb2248a39833`.

Tests first failed for streaming/nonstreaming Runtime turns, memory/file Harness
send, and the lab's HTTP message route. The fixed source passed those boundaries.
Harness commit `637357a` adds exact replay and recovery checks asserting one
provider dispatch. Lab's regression exercises installed public SDK APIs and
replaces only transport I/O with a synthetic timeout; it uses no model credential.

## Local SDK verification

- Runtime `.venv/bin/python -m pytest -q`: 1,078 passed, 2 gated skips,
  336.36 seconds. The source run started before the version bump; final exact
  release archive/conformance/turn checks passed 76 tests in 19.91 seconds.
- Harness full suite with fixed Runtime installed and source `PYTHONPATH`:
  780 passed, 2 gated skips, 115.30 seconds. One existing fork warning.
  The initial run exposed 10 failures caused by the stale installed Runtime in
  isolated subprocesses; refreshing that dependency resolved all failures.
- Runtime `.venv/bin/python -m build --no-isolation`: wheel and sdist built.
- Lab HTTP regression with the old installed SDK: failed with HTTP 503
  `store_corrupt`. With the patched source as a test-only witness: passed;
  replay/recovery retained the failed timeout without redispatch.
- Independent review found no actionable correctness issues in the narrow fix
  and Runtime/Harness regression tests.
- A clean Python 3.12 installed-wheel environment passed `wheel_smoke.py`,
  `production_wheel_smoke.py` and `conversation_wheel_smoke.py`. The first attempt
  in the old Runtime development environment lacked the recorder package;
  the clean environment installed the coherent Core/Runtime/recorder family.

## Release and installed lab adoption

Runtime 0.9.3 is published on PyPI. Exact-source candidate run `38505142052` and
promotion run `38506619153` passed all required platform and public-byte gates.
Promotion first encountered a macOS CLI version-probe timeout/process-cleanup
failure (all other lanes passed); rerunning the failed lane passed without
changing or weakening any gate. Its immediate post-upload check then hit PyPI
propagation (`published distribution is missing`); a failed-job rerun passed once
the exact public bytes became visible.

The active manifest SHA-256 is
`87862e1d37fd2f2cc1b8c6cd9965289887b0c056b26e81781dad4929a70a36c6`.
Runtime wheel SHA-256 is
`37badaead3935e5a9127da5a3a13a55b6b2b3bf80eb6b09acb4446301d1283c5`.
Harness 0.8.2 remains the published wheel at source
`fc1f0cf69204f24329e8d8cfc3b0e226642fa9e8`; adapter 0.3.0 wheels retain their
original source commits and hashes, not the newer compatibility-witness bytes.

`scripts/prepare_dependencies.py`, `install_dependencies.py` and
`audit_install.py` verified all five public wheels in fresh `.venv-latest`.
The full lab suite passed 955 tests, zero skips, one existing Starlette warning
in 67.04 seconds. The first run had two older Harness lifecycle expectations;
updating them for 0.8.2's saved-decision reconciliation and interrupted simulated
tool reply retained every zero-redispatch/domain-effect assertion.

The rebuilt released consumer image is
`sha256:e4e486276828645586def0b5412056e8efcfc2d65d749f00ca2442271df2b0a1`.
Real-stack acceptance passed. The conversation gate now has 97 cases,
including ordinary and interpretation timeouts persisted and replayed/recovered
on another replica without another provider call.

Native PostgreSQL 18 acceptance passed 54 cases, zero skips, with exact-owned
cleanup verified (owner `26127787ca554a3588784269e06394bb`, 246.08 seconds).
The first PostgreSQL 16 conversation run passed 95 of 97 cases, including both
new real timeout regressions. Its two failures were older saved-command recovery
expectations collected before the updated assertions; cleanup was verified
(owner `74403c7086b04ff88381e55dba23aadf`, 408.43 seconds). The tests now require
completed recovery only after an exact saved decision returned, retain uncertain
recovery for merely prepared commands, and continue to assert unchanged provider
calls, domain/journal rows and workflow revisions. Complete PostgreSQL 16/18
conversation reruns passed all 97 cases each, zero skips, with verified payload
audits and exact-owned cleanup:

| Lane | Owner | Cases | Seconds |
| --- | --- | ---: | ---: |
| Conversation PostgreSQL 16 | `3e777d0823704dc883b5d3f6296dac81` | 97 | 421.53 |
| Conversation PostgreSQL 18 | `c854ee7b2b8247d984376ff4b73565c0` | 97 | 420.85 |

The final commands used `.venv-latest/bin/python -m lab_runner test --mode
conversation --postgres-version 16` (and `18`) with the immutable released
consumer image above. Host architecture was ARM64, Python 3.12.14. All provider
responses and workflow effects in these gates were synthetic; no live credential
was used. Both actual 35-second slow-provider scenarios persisted a failed
`timeout` receipt, then replayed/recovered it on replica B without another call.

A fresh owned chat launch uses the audited released image/manifest and
`.venv-latest`, while the original interrupted demo and its environment remain
preserved. The new browser session was visibly connected and ready, with zero
provider calls consumed from its bounded 32-request local Qwen allowance. This
is startup verification; it is not an additional live provider certification.

Harness upstream CI run `38509598022` passed all source, wheel and PostgreSQL
lanes after the immutable Runtime dependency, artifact verifier and packaging
fixtures were aligned to 0.9.3. Final full local Harness verification again passed
780 tests, two gated skips and the existing fork warning in 115.44 seconds.

The final focused review found no actionable issues in the updated lifecycle
expectations and confirmed their unchanged provider/effect/revision checks.
`git diff --check` passed. Lab changes remain local, alongside the pre-existing
adoption/UI changes; Runtime patch/release and Harness regression/CI commits were
pushed. The original interrupted chat stack remains preserved; the fresh chat
stack intentionally stays running as the user-facing demo.

The initial qualification run `38504978431` failed before tests because several
jobs selected the previous version's artifact filename. Exact-source candidate
run `38505142052` uses the corrected filenames and all normal qualification gates.
