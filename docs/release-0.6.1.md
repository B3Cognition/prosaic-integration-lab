# Integration Lab 0.6.1

Integration Lab 0.6.1 fixes the standalone installed evaluation CLI. The SDK
payload auditor now ships inside the Lab package, so
`python -I -m lab_runner.native_eval` works without a repository `scripts`
package. The source audit command remains compatible; payload, ownership,
import-shadowing and executable-cache checks are preserved.

The [GitHub release](https://github.com/B3Cognition/prosaic-integration-lab/releases/tag/v0.6.1)
provides the original qualified CI wheel and source archive, plus
`SHA256SUMS-0.6.1.txt` and `VERIFICATION-0.6.1.json`. Verify those checksums before
installation. The [verification ledger](verification/release-0.6.1-2026-10-25.md)
binds the exact source, CI run, published bytes and clean-install results.

Fresh public-wheel and rebuilt-public-source installs each passed all four
standalone evaluation lanes: native 9/9, unified API 11/11, unified CLI 13/13
and provider fallback/no-replay 18/18. Both verified isolated imports, all 176
installed Lab wheel files, absence of repository `scripts`, dependency
compatibility and cleanup. The 102 checks made zero live provider calls.

All four Linux AMD64/ARM64 × PostgreSQL 16/18 CI cells passed 1,899 source tests
each and 334 real-stack checks each, with verified cleanup. Clean wheel and
rebuilt-source qualification passed throughout; ARM64/PostgreSQL 16 also
qualified the source service stack. Post-publication clean installs ran on
macOS ARM64/Python 3.12.15.

The public SDK train remains Core **0.4.1**, Runtime **0.9.8**, Runtime recorder
**0.3.0**, Harness **0.9.4** and Harness store **0.4.0**. Start with the
[unified pool guide](unified-runtime-pools.md) and retained
[0.6.0 feature and benchmark notes](release-0.6.0.md). Markdown tasks, inputs,
permissions, budgets and historical live measurements are unchanged. Synthetic
fallback checks do not represent induced live quota exhaustion or a new model
benchmark. Live inference remains opt-in; memory and correction remain experimental.

The published archives preserve the qualified source's pre-publication
“unreleased” changelog heading. This follow-up records the release date without
replacing those bytes or changing the 0.6.0 assets.
