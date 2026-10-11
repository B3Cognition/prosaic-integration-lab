# Production readiness milestones 1 and 2 — 2026-10-11

Branch: `codex/production-readiness-m1-m2`, starting at `e283752`.
The maintainer authorized native faults/restoration, ordinary public-index
adoption and local Qwen tier routing. SDK release pins remain unchanged.
This ledger records new work; Lab 0.3.0 historical evidence is preserved.

Milestones 1 and 2 are qualified at source
`8f60c587ce36a9bb5d9b65c3ca1876f1de93b9bc`. The final four-cell matrix passed
920 required cases, zero failures/errors/test skips, 32 lane cleanups and four
separate demo cleanups. Each cell passed 744 source tests with one existing
deprecation warning and a fresh ordinary-index adoption check. Local Qwen
routing passed independently. This later documentation checkpoint records the
qualified source; it does not change the SDK pins or published Lab 0.3.0 assets.

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
not run after the gate failure. The milestones remained unqualified at that point.

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

The first [complete native matrix](https://github.com/B3Cognition/prosaic-integration-lab/actions/runs/38127150702)
passed at `6596686933634573de883054c1727f89c94bbb5d`: 230 cases in each of four
cells, 920 total, zero failures/errors/test skips, all 32 lane cleanups verified,
and successful separate native demos. Independent audit checked the original
receipt counts, exact public manifest/payloads, per-cell immutable consumer,
pinned PostgreSQL/Lago, and original five-state Lab 0.2.0 migration. All four
adoption receipts matched the five public versions and wheel hashes. Actual
downloaded artifact ZIP digests matched GitHub's original records, and extracted
receipt bytes matched each archive. This run precedes the installer isolation
correction and therefore cannot alone close the final milestones.

The final [corrected-source matrix](https://github.com/B3Cognition/prosaic-integration-lab/actions/runs/38128089071)
passed at `8f60c587ce36a9bb5d9b65c3ca1876f1de93b9bc` with the normal required
checks and all eight lanes: 230 cases per cell / 920 total, zero failures/errors/
test skips, all 32 lane cleanups verified. All four separate native demo receipts
passed with verified cleanup and exactly two synthetic model calls each. Each
cell passed 744 source tests with one existing deprecation warning and the
corrected ordinary-index verifier. Original run/job/artifact records bind all
four archives to this exact commit. Downloaded ZIP digests match the API records,
and every extracted required/adoption receipt matches its original ZIP bytes.
Independent review checks the counts, owners, immutable images, pinned database
and Lago, exact manifest/payloads, original five-state migration and adoption
flags. The SDK manifest remains
`37a7b0dcf7bffa1c64481aafc7173e947c1e083616adcf50112e53022d589aca`.

| Cell | Artifact ID | Original archive SHA256 | Required receipt SHA256 |
| --- | --- | --- | --- |
| ARM64 / PostgreSQL 16 | 11698831290 | `6703b61c717d0fe5f7d973609153ceb4ca994986bf4bdb60c50fcf7f59a8c231` | `9e4e9550a82fd49c3ad9b193d3c674a6af7622307f09b5ae038d4179c9c61aa6` |
| ARM64 / PostgreSQL 18 | 11699080735 | `7ba6fe6d0edff7757902d26828846ae5cf47bad665ed0fe9d8731e042d967762` | `62ce1375278dddb7997cfefbdce84ac47082aac8b79708977c7ae1ae0200164f` |
| AMD64 / PostgreSQL 16 | 11698046189 | `64bdecd074dc47cbc200f435fa3ed26433072f50db43e4a25924cf011b24ecfa` | `b51b5f00db41ae51403c20177487cade8024bc8560dc22cbf44ec055efec34e4` |
| AMD64 / PostgreSQL 18 | 11698127397 | `b96d1b86244135594f9f27a1692bc8576655adee56f339a05af9a0461661dd95` | `37bc80ae2936025fdc4f099b1a3b0d5ebc941a45f84de9888acd0afc8b54f074` |

The adoption receipt SHA256 is
`77ff80cc835c9fcc886c9e69c5516f2a7cd4edce86f705b35d63fed664f76f5a`
for both ARM64 cells and
`f31c6b2f332691f721c90dae21dd9afda59a4318a2ddd34fdb2d4e8880708d1b`
for both AMD64 cells. All five public versions and wheel hashes, payload/import
ownership, CLI, `pip check`, factory construction and cleanup flags passed.

| Cell | Immutable consumer image |
| --- | --- |
| ARM64 / PostgreSQL 16 | `sha256:77faff80a29cf2822031882f6b821df6d361c821f2139aa15c84dcd13a8e10fa` |
| ARM64 / PostgreSQL 18 | `sha256:aa2442b8783b92f0fd33b4d75dd7ab1fd0b6db55962f19bdeee3f48ccba4ef36` |
| AMD64 / PostgreSQL 16 | `sha256:67a351a4fe9169ae703449bcd2b89d06387e56cbb78683ab7a481f49b7c9ccb1` |
| AMD64 / PostgreSQL 18 | `sha256:2d637c53f6c3c7f24cec829375ce0e51f744ba8bb628eac039410a1b97ca653e` |

The exact committed source archive also built a wheel and source distribution.
All 82 public build inputs and three host extras match the source archive; the
runner/application modules match the wheel. These are unreleased test builds,
kept separately from published Lab 0.3.0 bytes. Their SHA256 values are
`51659a4ed5b89dbb2f898add4300a37d9ab787acd6676852fe234b8efc2a091c`
(wheel) and `f7c86690c27e6f0b9682619da8b74fdb1b2f42a4f92ab50d20a2723254a21210`
(source distribution).

## Reproduce the added checks

Use Python 3.12, a running Docker daemon and a separate checkout of the qualified
source. Create a fresh environment containing the five public SDK pins:

```sh
git clone https://github.com/B3Cognition/prosaic-integration-lab.git prosaic-lab-readiness
cd prosaic-lab-readiness
git checkout --detach 8f60c587ce36a9bb5d9b65c3ca1876f1de93b9bc
python3.12 -m venv .venv
.venv/bin/python -m pip install --require-hashes -r dependencies/requirements.lock
.venv/bin/python scripts/prepare_dependencies.py --manifest dependencies/releases.json
.venv/bin/python scripts/install_dependencies.py --manifest dependencies/releases.json
.venv/bin/python scripts/audit_install.py --manifest dependencies/releases.json
.venv/bin/python -m pip check
export PATH="$PWD/.venv/bin:$PATH"
.venv/bin/python scripts/build_consumer.py \
  --manifest dependencies/releases.json --dependency-mode released \
  --tag prosaic-integration-lab:dev
```

Use that checkout for the [required gates](../release-gates.md),
[native restore command](../qualification.md) and
[local tier routing/public adoption commands](../../configs/README.md).
The published Lab 0.3.0 tag retains its original 216-case contract per cell.
The qualified branch has 230 cases per cell. Local routing requires the explicit
three-call opt-in and host-owned endpoint/credential configuration.

Logical restoration uses a second database on the same owned primary and a fresh
replica. It does not certify primary destruction, HA/PITR, long native soak,
external-effect rollback, deployment identity/TLS or customer invoices.
