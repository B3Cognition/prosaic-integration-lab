# Production readiness milestones 1 and 2 — 2026-10-11

Branch: `codex/production-readiness-m1-m2`, starting at `e283752`.
The maintainer authorized native faults/restoration, ordinary public-index
adoption and local Qwen tier routing. SDK release pins remain unchanged.
This ledger records new work; Lab 0.3.0 historical evidence is preserved.

The [Lab 0.4.0 release closure](#lab-040-release-closure) below records a separate
final source, matrix and package build. The milestone evidence that follows
retains its original `8f60c58` source and local Qwen proof.

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

## Lab 0.4.0 release closure

Release: [Lab 0.4.0](https://github.com/B3Cognition/prosaic-integration-lab/releases/tag/v0.4.0),
source `f47328d2d5a8e7253ad6cb199583f9f0d311fd60`.
[Required integration acceptance run 38147824985](https://github.com/B3Cognition/prosaic-integration-lab/actions/runs/38147824985),
attempt 1, passed all four normal Linux AMD64/ARM64 × PostgreSQL 16/18 cells.
Original run/job/artifact records and downloaded summary bytes bind this result
to the exact source: 230 required cases per cell / 920 total, zero failures/
errors/test skips, all 32 lane cleanups and four separate demo cleanups verified.
Each job passed 744 source tests with one known Starlette TestClient deprecation
warning and ordinary public-index adoption. Every separate demo completed two
independently counted synthetic calls, zero unresolved calls and no billing
eligibility. Conditional candidate steps were skipped; no required test was skipped.

| Cell | Artifact ID | Original archive SHA256 | Required receipt SHA256 |
| --- | --- | --- | --- |
| ARM64 / PostgreSQL 16 | 11706385936 | `c9d65635eb27267db3be3242ce5860769c529ac097d78579ff23a959eb04a560` | `b3a7856366a8f9cefcab296cffbd3e72185148f37bf31d0e8047b0737226d948` |
| ARM64 / PostgreSQL 18 | 11706036357 | `9050035f6884fa6cf28d610e68751fdd59280a9f6b07a076a112c50a7e937fc4` | `3bf33c14601b4214d9e0cc994b6e0c8285b146a68285e48f7146cdf6a3463bcc` |
| AMD64 / PostgreSQL 16 | 11706146485 | `fd4c69d3fc5c09a383a090bb236944edff4df44b994af63063b8be67a3885c75` | `4fcc6f58a8028f8a7f8171d78d12c673691236161350bedb243f1feec756f057` |
| AMD64 / PostgreSQL 18 | 11705571408 | `2b61d9e8867c471bf212f45102463bde3b485a9c9d5a82d7ed4c69313d819d75` | `8a2f5acabd0a2934c7854b24c93ff3daeba230bd80fc2b4c840ee2705d15962a` |

The capacity fixture now uses six seconds of offered work across two
three-second fairness windows and 18 workflows. Its two-second P95 target,
correctness, row-growth, read and accounting assertions remain required; the
recovery profiles are unchanged. Passing summaries establish that the assertions
passed at this source. The safe CI upload omits private measured capacity and
restore scalars, so it does not establish an exact measured P95. Prior failed
receipts remain historical evidence; their omitted failure details were not
recovered from the safe summaries.

The SDK manifest remains
`37a7b0dcf7bffa1c64481aafc7173e947c1e083616adcf50112e53022d589aca`:
Core 0.4.1, Runtime 0.8.1/recorder 0.2.1 and Harness 0.7.1/store 0.2.1.
The earlier three-call local Qwen proof remains separate; the release matrix
makes no additional real-model or deployment certification claim.

Clean exact-source builds and release metadata have the following hashes:

| Artifact | SHA256 |
| --- | --- |
| `prosaic_integration_lab-0.4.0-py3-none-any.whl` | `9ad6584e1c8ffa8ed59fff5b60cd20d6d282c3419fac2bc1767beba68e7a8c79` |
| `prosaic_integration_lab-0.4.0.tar.gz` | `4a6ac1ea1496e34727cea61ff9fc9f30440e46a6c70ff81c5c15301f5dbb8731` |
| `SHA256SUMS-0.4.0.txt` | `1203db0cf94a7b717dc3ed5a1c8831054b75e8578350e14bf153ccfca4a596cf` |
| `VERIFICATION-0.4.0.json` | `b4ed5aed15cd69ea5a73fb30452cf45b8fa58bb2dd59eea5c99666b8ecadf0a9` |
| Exact-source Git archive, `source.tar` | `08a2cdff5a7449437ecd5af9241236df5d0a8f272bf4cd5c42fcb06490cfdc4f` |

The annotated `v0.4.0` tag points to the qualified source. All four published
release assets were downloaded into a fresh directory and matched the original
bytes, GitHub API sizes/digests and checksum entries. Lab 0.3.0's tag and original
package/verification digests remain unchanged. This documentation checkpoint
does not rebuild the released packages or move either tag.

The Git archive matches all 256 tracked files. The sdist retains 251 tracked
files byte-for-byte plus seven standard generated metadata files; its unchanged
manifest omits five historical JSON receipts that remain in Git and the source
archive. All 82 public build inputs, the three host extras, 40 Markdown documents
and 15 assets are retained. The 59-file wheel contains all 27 application and
27 runner Python modules byte-for-byte plus five standard metadata files, with
verified `RECORD` hashes and sizes. No private logs, credentials, local run state,
virtual environments or caches enter the artifacts.

A fresh wheel install passed version/import ownership and CLI startup checks
from a neutral directory. The extracted sdist passed all 744 tests with zero
failures/errors/skips when supplied an explicit `LAB_HISTORY_TEST_REPOSITORY`:
the historical upgrade regression needs a separate Git checkout containing
the original Lab 0.2.0 commit, which packaging does not embed.

To reproduce the release, clone the stable tag and follow the
[fresh public environment and image recipe](../../README.md#try-the-native-workflow).
`git rev-parse HEAD` must report the full `f47328d` source above. After that setup:

```sh
.venv-public/bin/python -m pytest -q
.venv-public/bin/python scripts/verify_public_adoption.py \
  --manifest dependencies/releases.json --export reports/public-adoption.json
.venv-public/bin/python -m build
.venv-public/bin/python scripts/prepare_dependencies.py --manifest dependencies/releases-lab-0.2.0.json
.venv-public/bin/python -c 'from lab_runner.legacy_upgrade import build_baseline; build_baseline()'
.venv-public/bin/python scripts/required_acceptance.py \
  --postgres-version 16 --export reports/required-pg16.json
.venv-public/bin/python scripts/required_acceptance.py \
  --postgres-version 18 --export reports/required-pg18.json
.venv-public/bin/python -m lab_runner demo --mode native --postgres-version 18
```

CI verifies both native Linux architectures. Local acceptance qualifies only
the actual host architecture. For extracted-sdist tests, set
`LAB_HISTORY_TEST_REPOSITORY` to the absolute path of this full-history checkout
before running the pytest command. Logical restoration still uses a second database
on the same owned primary and a fresh replica; HA/PITR, primary destruction,
long soak capacity, live deployment identity/TLS and customer invoicing require
separate acceptance. Lab 0.3.0 assets and all earlier evidence remain unchanged.
