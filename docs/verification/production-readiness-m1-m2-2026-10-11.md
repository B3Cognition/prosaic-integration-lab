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
qualified. Actual matrix receipts and independent review will be appended here.

Logical restoration uses a second database on the same owned primary and a fresh
replica. It does not certify primary destruction, HA/PITR, long native soak,
external-effect rollback, deployment identity/TLS or customer invoices.
