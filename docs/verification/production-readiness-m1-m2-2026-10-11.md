# Production readiness milestones 1 and 2 — 2026-10-11

Branch: `codex/production-readiness-m1-m2`, starting at `e283752`.
The maintainer authorized native faults/restoration, ordinary public-index
adoption and local Qwen tier routing. SDK release pins remain unchanged.
This ledger records new work; Lab 0.3.0 historical evidence is preserved.

## Source and public consumer verification

An isolated `.venv-readiness` installed hash-locked third-party dependencies and
the five audited public SDK wheels. The old `.venv` still had obsolete packages;
its import failures were setup failures, not SDK regressions. The refreshed
baseline passed 540 tests. Sandbox-restricted sockets/build networking failed
before escalation; the unrestricted baseline passed.

Task source/fixture verification reached 730 passing tests with one existing
Starlette TestClient deprecation warning. New cases include real loopback Runtime
transport faults, live relay partition/reconnection, public factory tier routing,
strict native restoration evidence and ordinary adoption verifier boundaries.
These source tests do not establish owned PostgreSQL/container acceptance.

The ordinary-index verifier passed on Python 3.12.14 / Darwin ARM64. It created
an isolated temporary environment, resolved all five exact public pins through
PyPI with dependencies enabled and no cache, checked pip-report archive hashes
and separately downloaded wheel bytes, audited installed payloads, verified
import ownership/CLI startup/`pip check`, and constructed a public workflow.
Owned temporary cleanup was verified. Manifest SHA256:
`37a7b0dcf7bffa1c64481aafc7173e947c1e083616adcf50112e53022d589aca`.

## Local model routing

A bounded authenticated catalogue read confirmed local Qwen Coder 7B and
ThinkingCap Qwen 27B. The initial three-call smoke completed default and balanced
on 7B, strong on 27B, reporting 83, 87 and 143 tokens respectively. No tools,
retries or cloud endpoint were used. Review required stronger isolation from
ambient proxies and observed-model/request evidence; the initial smoke therefore
establishes completion only, pending the hardened receipt verification.
After the proxy/evidence fixes and clean scoped re-review, a fresh bounded smoke
passed all three cases. Public sealed FileRunStore checkpoint/receipt evidence
verified the observed profile/request model and exactly one provider request per
case, zero tools, complete consistent usage and three shared reserved invocations:

| Tier | Observed profile | Observed request model | Reported tokens |
| --- | --- | --- | --- |
| omitted/default | `local` | `mlx-community--Qwen2.5-Coder-7B-Instruct-4bit` | 87 |
| balanced | `local` | `mlx-community--Qwen2.5-Coder-7B-Instruct-4bit` | 87 |
| strong | `local-strong` | `ThinkingCap-Qwen3.8-27B-MLX-4bit-DWQ` | 143 |

The hardened receipt records three provider requests and zero tool calls.
Ambient proxies are disabled in a restored standalone-script scope, redirects
are rejected, and contradictory or missing receipt evidence stops subsequent
cases. This is routing qualification, not a quality/performance benchmark or billing.

## Native stack qualification

The collected contract is native53 (40 prior + 13 faults), qualification3
(fairness + legacy restore + native restore); other six required lanes are
unchanged. The total required contract is 230 per cell / 920 across four cells.
Collection is not execution evidence.

Local Docker Desktop was opened, but both the engine and desktop status timed
out; its UI inspection also timed out. No fixture was allocated, and no shared
container or engine restart was performed. Exact-source Linux AMD64/ARM64 ×
PostgreSQL 16/18 CI remains required before the new native cases can be claimed
qualified.

The first [full matrix run](https://github.com/B3Cognition/prosaic-integration-lab/actions/runs/38124891877)
tested exact source `13d52d28bff0ce7cad24174b4c82e0244b987570`. All four cells
passed the 730 source tests, ordinary public-index adoption, immutable consumer
build and exact Lab 0.2.0 baseline build. Seven required lanes passed in every
cell, including all 53 native cases with provider faults and live SQL partition
takeover. The qualification lane ran all three cases but failed native restore
in every cell: 916 passes and four failures across the required 920 cases, zero
test skips, and all 32 outer lane cleanups verified. Native adoption demos did
not run after the gate failure. The milestones remain unqualified.

Diagnosis uses closed phase/category receipts, with no arbitrary exception
messages or captured state exported. A temporary direct native restore dispatch
uses distinct `diagnostic-native-restore-*` check names and cannot satisfy the
normal required acceptance checks. The complete matrix must be rerun after a
confirmed correction; diagnostic success alone is insufficient.

The [direct diagnostic run](https://github.com/B3Cognition/prosaic-integration-lab/actions/runs/38126506463)
tested source `a66bf0beccf45c19ee7ccfdb90dfb7b7c798af28`. All four safe receipts
reported `proposal_admission` / `unexpected_failure` with verified cleanup.
A fresh SDK-only local interpreter reproduced `ModuleNotFoundError` in the
approved-proposal helper: pytest supplies the Lab application `src` path, while
the direct native recovery CLI lacked the native demo's source setup. This is a
Lab runner defect; the public SDK pins do not need a change. Its correction must
be verified outside pytest's path setup and through actual restore acceptance.

The corrected native CLI reuses the native demo's current-application source
setup while retaining installed SDK imports and existing candidate checks. Its
isolated `python -I` subprocess regression starts without the application,
admits the actual approved graph and loads the public journal before allocation.
The source suite reached 741 passes, zero skips and one existing warning; narrow
independent review found no substantive issue.
The [corrected direct restore run](https://github.com/B3Cognition/prosaic-integration-lab/actions/runs/38126892849)
at `eba4ea7a448b6002a97d3b1eba6ac7bbecd20f23` qualified all four cells, with
verified cleanup in all four original safe receipts. The temporary diagnostic
workflow input is now removed; normal required checks and all eight lanes are
restored for the complete matrix rerun. Direct success alone does not close the
milestones.

A final installer isolation review found that pip's `--isolated` still honors
mixed-case proxy variables and netrc authentication. A fake loopback proxy
received one CONNECT, and a temporary fake netrc supplied Authorization during
request preparation; no PyPI request or real credentials were used in the proof.
The fixed-name environment filter therefore did not establish the documented
ambient-neutral, credential-free boundary, although the five verified SDK wheel
identities remain valid. The correction must remove proxy variables regardless
of casing, disable system-proxy fallback, and prevent netrc/keyring lookup or
authentication prompts. Final full qualification will use that corrected source.

The correction removes every case-insensitive `*_proxy`, forces both bypass
variables to `*`, selects `NETRC=os.devnull`, and invokes pip with `--no-input`
and `--keyring-provider disabled`. It preserves `HOME` and the parent process
environment. Four watched failures reproduced mixed proxy traffic and fake
netrc Authorization on a direct origin; the corrected 17-case scope passed.
Only owned loopback services and fake credentials were used. Independent
re-review passed the same 17 cases and accepted the real pip flags for install,
download and check. The full source suite passed 744 tests with one existing
warning; exact-source full qualification remains required.

Logical restoration uses a second database on the same owned primary and a fresh
replica. It does not certify primary destruction, HA/PITR, long native soak,
external-effect rollback, deployment identity/TLS or customer invoices.
