# Lab 0.6.1 release and clean-install verification — 2026-10-25

## Published artifacts

[Lab 0.6.1](https://github.com/B3Cognition/prosaic-integration-lab/releases/tag/v0.6.1)
publishes the original artifacts retained by the successful ARM64/PostgreSQL 16
job in [run 40133039899](https://github.com/B3Cognition/prosaic-integration-lab/actions/runs/40133039899).
No local rebuild replaced the qualified release archives.

[PR #30](https://github.com/B3Cognition/prosaic-integration-lab/pull/30) merged as
`4b0258f306b8fde91ef22aaf347d7113a1ed630c`. Release tag `v0.6.1` selects the
qualified head `73a071480f4399ddea52839f6836ccaa742e9a03`; their file trees
are identical. All 172 wheel source payloads and 660 archive source payloads
matched that qualified commit before publication.

| Asset | SHA-256 |
| --- | --- |
| `prosaic_integration_lab-0.6.1-py3-none-any.whl` | `4c2fcd63c9b151e5007292670dbcb1a2e6a578be1710f2b37fa6eea3b79e7d13` |
| `prosaic_integration_lab-0.6.1.tar.gz` | `01831834c424a93276b8c44b9de0130486af3af4296955cdb9992a9318374a31` |
| `SHA256SUMS-0.6.1.txt` | `c9236d388fd7002a7f239cdb632e3f93a08c2c7f0f3aae9b93162c2e8bb87e02` |
| `VERIFICATION-0.6.1.json` | `74ecefd5e541b8e3858674fe9c517782ce9be5fe7c415590c97d625491d82b82` |

All four uploaded asset hashes and sizes matched the audited files. After
publication, anonymous downloads with proxy and credential helpers disabled
matched those same bytes. All four existing 0.6.0 asset digests were checked
and remained unchanged. The archives retain their pre-publication “unreleased”
changelog heading; release notes and this documentation record publication.

## Exact-source CI qualification

| Native Linux runner | PostgreSQL | Source regressions | Required stack checks | Lanes |
| --- | --- | --- | --- | --- |
| AMD64 | 16 | 1,899 passed | 334 passed | 9 |
| AMD64 | 18 | 1,899 passed | 334 passed | 9 |
| ARM64 | 16 | 1,899 passed | 334 passed | 9 |
| ARM64 | 18 | 1,899 passed | 334 passed | 9 |

All 1,336 required stack checks across 36 lanes passed without skips, with
verified cleanup and SDK payload audits. Each cell passed public-index adoption,
installed native/unified acceptance, and clean wheel/rebuilt-source qualification.
ARM64/PostgreSQL 16 additionally exercised the clean-source service stack.

## Post-publication clean installs

Two fresh environments on macOS ARM64/Python **3.12.15** installed the downloaded
public wheel and a wheel rebuilt from the downloaded public source archive.
Both installed locked third-party dependencies and the checksummed released SDK
train: Core **0.4.1**, Runtime **0.9.8**, recorder **0.3.0**, Harness **0.9.4**
and store **0.4.0**. The active manifest SHA-256 remained
`36eec99280acb8688d2496f704f4445b59c3ff269fc506a83d6e7fe83bc92698`.

`pip check`, SDK payload auditing, isolated installed import ownership and all
**176 installed Lab wheel files per consumer** passed verification. The 172
source payloads above exclude distribution metadata; this installed count
includes metadata and excludes `RECORD`. No source checkout was on the import
path and no repository `scripts` package was available.

| Standalone command | Public wheel | Rebuilt public source |
| --- | --- | --- |
| `test` | 9/9 | 9/9 |
| `unified-test` | 11/11 | 11/11 |
| `unified-cli-test` | 13/13 | 13/13 |
| `unified-fallback-test` | 18/18 | 18/18 |
| Total | **51/51** | **51/51** |

Each command ran from a neutral working directory through isolated Python:

```sh
python -I -B -m lab_runner.native_eval test --manifest /path/to/releases.json --wheel-dir /path/to/verified-sdk-wheels
python -I -B -m lab_runner.native_eval unified-test --manifest /path/to/releases.json --wheel-dir /path/to/verified-sdk-wheels
python -I -B -m lab_runner.native_eval unified-cli-test --manifest /path/to/releases.json --wheel-dir /path/to/verified-sdk-wheels
python -I -B -m lab_runner.native_eval unified-fallback-test --manifest /path/to/releases.json --wheel-dir /path/to/verified-sdk-wheels
```

The manifest and verified wheel directory came from the source archive's
released dependency install commands. Every receipt verified Runtime 0.9.8 and
the exact manifest digest. Fallback scenarios proved quota rejection before work,
learned/persisted cooldowns and no replay after partial Claude, Codex or API work.
All eight command invocations reported verified cleanup and zero live invocations.

These **102 checks** use synthetic fixtures. They are separate from live-model
benchmarks and from Linux/database qualification in CI. SDK pins, Markdown,
inputs, permissions, budgets, freezes and historical benchmark measurements
remain unchanged. Private receipts and operational logs are excluded from this
documentation; no new model-quality or memory-efficacy claim is made.
