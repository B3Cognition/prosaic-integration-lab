# Lab 0.6.2 release and clean-install verification

[Lab 0.6.2](https://github.com/B3Cognition/prosaic-integration-lab/releases/tag/v0.6.2)
publishes the original CI wheel/source artifacts from
[run 40190681901](https://github.com/B3Cognition/prosaic-integration-lab/actions/runs/40190681901).
Tag `v0.6.2` selects qualified source
`b5773c33ba7305b92667c9874e4a8526c4394dd9`.
[PR #33](https://github.com/B3Cognition/prosaic-integration-lab/pull/33) merged as
`46a2d807b3965d6cfd016819675d80acb14f754e` with an identical file tree.

All four Linux AMD64/ARM64 × PostgreSQL 16/18 cells passed 1,922 source tests
each and 334 required stack checks each: 36 lanes / 1,336 checks total, zero skipped
or failed stack checks, verified cleanup. Public-index SDK adoption, actual
sandbox confinement, installed native/unified fixtures, distribution consumers
and documented demos passed. ARM64/PostgreSQL 16 also qualified the source
service stack. 172 wheel and 665 archive source payloads matched the qualified
commit before publication. No local rebuild replaced the release artifacts.

| Public asset | SHA-256 |
| --- | --- |
| `prosaic_integration_lab-0.6.2-py3-none-any.whl` | `d5a84d09577dcc4caba14cb862be4a6df7110ac184837fda6888c04aeccd9061` |
| `prosaic_integration_lab-0.6.2.tar.gz` | `458cf95165e6cce7e11ca81cd169e551a8b0728135077175c7ae4393001a67fb` |
| `SHA256SUMS-0.6.2.txt` | `824c6bd15aeab3d85f488abb59f08c34741bcccac18117284eb3f6f37ea58c1d` |
| `VERIFICATION-0.6.2.json` | `fd74ff33bebf6f110c8ec29cd1252712883cbb520989dcc0732240266e6740f0` |

Uploaded asset hashes/sizes and all four anonymous public downloads matched the
audited files. Earlier 0.6.0/0.6.1 asset identities remained unchanged.

Fresh public-wheel and rebuilt-public-source consumers ran on macOS ARM64,
Python 3.12.15. Each installed the locked dependencies and public SDK train:
Core 0.4.1, Runtime 0.9.8, Runtime recorder 0.3.0, Harness 0.9.4, store 0.4.0.
Manifest SHA-256:
`36eec99280acb8688d2496f704f4445b59c3ff269fc506a83d6e7fe83bc92698`.

| Installed verification | Public wheel | Rebuilt public source |
| --- | --- | --- |
| `test` native fixtures | 9/9 | 9/9 |
| `unified-test` API fixtures | 11/11 | 11/11 |
| `unified-cli-test` CLI fixtures | 13/13 | 13/13 |
| `unified-fallback-test` rejection/no-replay fixtures | 18/18 | 18/18 |
| CLI default 180s, explicit 240s, fractional 299.999999s | 3/3 | 3/3 |
| Total | **54/54** | **54/54** |

All 108 checks passed with cleanup verified and zero live invocations. Isolated
imports, absence of repository `scripts`, all 176 installed Lab wheel files per
consumer, SDK payload auditing and dependency compatibility passed. The deadline
fixtures exercise real installed CLI parsing, configuration, readiness,
scheduling/accounting and saved receipts; inference is replaced by explicit
refusals. They do not establish a new live-model benchmark or a 240s completion
guarantee. The historical 0.6.1 private-driver study retains its separate evidence.

The guided onboarding and first-workflow example were added after this immutable
release; the 0.6.2 archives do not contain them. Private release receipts retain
the download, payload, installation and command proofs. Historical releases,
SDK pins, Markdown tasks, inputs, graders and experimental boundaries are unchanged.
