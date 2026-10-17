# Generic budget hardening — offline qualification

Implemented the approved operational-hardening milestone. No live provider
requests, model changes, allowance increases, pushes or releases occurred.
The prior incomplete memory comparison and all historical ledgers remain intact.

## Frozen candidates

| Candidate | Executable source commit | Wheel SHA-256 |
| --- | --- | --- |
| Runtime 0.9.7+budget.3 | `2c6ffb91dd43fb48ac230aaca51f900a0829ded2` | `adf5454b3d3b8fac2c108ecd5c4462daf05d939a4ae76e8b2b40de8e68cf8c97` |
| Lab 0.5.1+budget.2 | `88e94136c1749861320defb9fdb32ce025dc8789` | `a4f7f780a58c4af7310d2f615b4e04a191fb3fb1363c744de9f2236f511a6e81` |

The candidate manifest retains released Core 0.4.1, Harness 0.9.0, Runtime
recorder 0.3.0 and Harness store 0.4.0. All five wheel checksums were verified
before isolated installation. The released manifest retains its original
`1c4cca26b7aae4ef9fde9e35493e4264fc5ef4def15a5df05e979f590ff5d50b` digest.
Direct wheel/source comparisons verified 49 Runtime and 108 Lab payload files.
Both wheel and sdist builds succeeded; no editable sibling imports were used.

## Verification

Platform: Python 3.12.14, macOS ARM64. Full source suites used an isolated
environment with the installed pinned SDK family and Core CLI on PATH.

| Check | Result |
| --- | --- |
| Runtime full source suite, `python -m pytest -q` | 1,238 passed; one installed-only gate deferred |
| Installed Runtime wheel gate with `PROSAIC_RUNTIME_WHEEL_ACCEPTANCE=1` | 1 passed, zero skips |
| Runtime installed wheel smoke | ownership, CLI, no Node, public admission and recorder construction passed |
| Lab final full source suite, `python -m pytest -q` | 1,205 passed; one existing Starlette deprecation warning |
| Reviewed capture/budget regressions | 48 passed |
| Final accounting/reporting/SDK regression set | 48 passed |
| Freeze/context/runner regression set | 37 passed |

Watched failing tests preceded implementation for request admission, v2 known
overruns, stale public reservation flags, below-case request breaches, recorder
failures and admission-helper drift. One fresh whole-change review found two
issues, both confirmed and corrected with regressions before qualification.

The installed `scripts/qualify_budget_candidate.py` run completed:

- 48 raw and 48 typed memory fixtures, plus 10 quality fixtures, all successful.
- Two strict public SDK/Harness cases: ordinary complete usage and a request
  reservation breach below the unchanged sample ceiling.
- Byte-identical replay of all benchmark outputs with socket creation denied.
- Exact known settlement of 8,516 against an unchanged 8,192 reservation;
  324 excess retained, reopen successful, further reservation denied.

An initial environment lacked setuptools and failed package-build gates; the
final isolated environment includes the fixed build backend. One earlier full
Runtime run hit a CLI preflight timeout; all 31 CLI tests and the final full suite
passed without timeout changes. Installed qualification initially rejected stale
bundled synthetic freezes; refreshed candidate freezes now bind the admission
helper. These unsuccessful attempts were retained rather than reported as passes.

## Meaning and remaining work

Runtime can now admit final native requests using a trusted exact/conservative
counter, reserve input plus bounded output atomically, and retain honest usage
through unknown outcomes and recorder failures. Lab v2 settlements persist
overruns and stop further samples, including request-level breaches that do not
exceed a whole sample's ceiling. V1 readers and historical evidence remain intact.

This is offline SDK/consumer evidence. It does not qualify a production tokenizer,
live provider, PostgreSQL stack, other platform, or the efficacy of memory.
No provider/model-specific tokenizer approximation was added. New live benchmark
execution fails closed until the host supplies qualified counters for each
approved profile. A new held-out comparison still needs new frozen artifacts
and cases; the prior 54-sample partial study cannot establish a typed-memory gain.
