# Harness 0.9.10 adoption and Lab 0.9.7 qualification

## Scope and provenance

The maintainer authorized the Lab dependency update, full tests, commit, merge
and publication. Work uses the clean `codex/harness0910-lab-release` worktree
from main `81fccf5233e32f1843d4bb027f3cef01bc27f38c`; unrelated experiment
checkout edits are excluded. Session policy migration is outside this change.

Both active manifests retain Core 0.5.0, Runtime 0.9.14, recorder 0.3.0 and store
0.4.1 byte-for-byte. Harness 0.9.10 is the public wheel from source
`1f0886831e2156966e744a947a9406c1c4ac0533`, SHA256
`762d40f78d5aca0d7b2c893a3afa6a594a81264537bf94baa87efc58e2ff28b4`.
Its anonymous PyPI metadata agrees with the upstream original CI release receipt.

The former active manifests/profile/freezes are archived under `pre-harness0910`
names. Existing historical records and benchmark corpus, prompts and scoring
retain their bytes. Current memory freezes bind the new profile and archive.

## Verification checkpoint

- Before implementation, the focused admission/provenance tests reported six
  expected failures and 18 passes against the old active pins.
- After implementation, admission, exact pins, historical profile selection and
  memory-lineage tests passed all 43 cases.
- The first clean virtual environment lacked pip (uv does not seed it by default).
  SDK installation failed before tests; seed pip and repeat unchanged commands.
  This is an environment setup failure, not a passing SDK audit.
- The sandboxed source run failed at loopback socket admission (430 failures,
  91 setup errors, 1,585 passes); the first focused failure is `PermissionError`
  at `ThreadingHTTPServer.bind`. Repeat unchanged outside the sandbox.
- Native/reasoning fixture acceptance passed all 46 cases on Darwin arm64,
  Python 3.12.15. Explorer's locked build and all 16 unit tests passed; generated
  JavaScript changes only the two Harness version labels.
- Both Lab wheel and source archive built successfully. Independent review
  approved the diff and passed 72 focused cases, including historical-byte checks.
- A reused installed environment failed the strict SDK audit on a stale optimized
  Runtime bytecode cache. Repeat in a fresh installed-consumer environment;
  do not weaken the audit or modify SDK code.
- The local consumer build fails its bounded Docker preflight: `docker info`
  times out after 15 seconds. Docker Desktop processes exist, but its shared
  engine is unresponsive. Do not restart or prune shared resources. Ruling:
  require the full hosted native matrix for real-stack evidence; local units
  and a build cannot substitute for it.
- Fresh installed-wheel guarded acceptance passed 138 cases with the same three
  strict fee-grammar xfails. Its installed rule coverage matches the preceding
  release; there are no new skipped requirements.
- `scripts/conversation_distribution_smoke.py` passed for both locally built
  formats: ordinary public-index adoption, isolated imports, payload audit, public
  construction, CLI, agent-quality/memory, sandboxed tools, native/unified pools,
  fallback controls, source assets and temporary cleanup. Stack execution is
  explicitly false in this local receipt.
- Explorer browser tests passed all 10 cases with `EXPLORER_PYTHON` selecting
  the clean Python environment. The first invocation used an incorrect variable,
  selected system Python and failed launcher readiness; no source fix was needed.
- Full source suite passed all 2,106 cases (one existing Starlette deprecation
  warning) using `/tmp/prosaic-lab097-source-venv/bin/python -m pytest -q`: no
  failures or skips. Final hosted results remain pending at this checkpoint.
  Publication must use original successful CI archives and safe receipts,
  followed by independent public-download checks.

No live model calls are authorized. Required missing infrastructure must fail;
three declared strict rule grammar expected failures do not count as passes.
