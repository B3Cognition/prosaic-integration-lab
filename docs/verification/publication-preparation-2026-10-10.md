# Public release preparation — 2026-10-10

Public Lab adoption requires all five original qualified patch wheels to be
published and verified: `b3-prosaic` 0.4.1, Runtime 0.8.1/recorder 0.2.1 and
Harness 0.7.1/store 0.2.1. The [hardening ledger](hardening-2026-10-10.md)
retains their exact sources, native qualification and original hashes. This
follow-up does not change those SDK artifacts, the Lab version or SDK pins.

The Lab's default container command, `python -m prosaic_integration_lab --version`,
looked up only legacy distribution names. It failed with `PackageNotFoundError:
prosaic` in the existing fresh environment containing the five B3 patch wheels.
The correction selects the installed distribution family through Core's
metadata and reports all five versions from that family. Legacy-only operation
remains supported; a missing member still fails rather than mixing families.

The regression launches the real CLI in a fresh isolated Python process against
wheel metadata, with no host site packages or editable source fallback. Before
the fix, the B3-only case failed and the legacy-only case passed. Both cases now
pass. The full Lab source suite passes 539 tests, zero failures or skips, with
one existing Starlette/httpx deprecation warning. These source checks used the
original five qualified SDK wheels in Python 3.12.14 on macOS ARM64.

```sh
python -m pytest tests/functional/test_dependency_install.py -q -k version_cli
python -m pytest -q
```

Before Lab 0.3.0 publication, adopt exact versions and actual verified public
download URLs in the active `dependencies/releases.json`, build a fresh released
consumer, and qualify the final source with all four native Linux architecture /
PostgreSQL cells. Require 864 cases, zero failures/errors/skips, all 32 lane
cleanups and four separate native demo cleanups. Preserve the immutable Lab
0.2.0 baseline, the earlier release manifests, legacy assets and historical
receipts. The successful candidate run `38080612477` applies to its original
`94f313e49707a09e7d0f3abbf818a9861bd6b14a` source; it does not qualify this CLI
follow-up or replace final released-package acceptance.
