# Integration Lab 0.6.2

Lab 0.6.2 makes `unified-benchmark --local-timeout` configurable within finite
1–300 seconds, retaining the default of 180 seconds. Plans, per-sample receipts
and report limitations preserve the selected deadline, including fractional
values. Invalid deadlines fail before SDK auditing or readiness checks.

Native deadlines remain 60 seconds and the total pool deadline remains 300
seconds. Permissions, exact output grants, attempt/request/tool/token limits,
shared allowance, Markdown tasks, inputs and graders are unchanged. The separate
`realistic` command retains its fixed 180-second local deadline.

The public SDK train remains Core 0.4.1, Runtime **0.9.8**, Runtime recorder
0.3.0, Harness 0.9.4 and Harness store 0.4.0. The installed evaluation auditor
fix from 0.6.1 is retained.

Use the [benchmark recipe](realistic-runtime-benchmark.md) and
[unified pool guide](unified-runtime-pools.md). The historical
[240-second study](verification/unified-cli-lab061-local240-2026-10-25.md)
used a disclosed private driver with Lab 0.6.1; it is not a live benchmark of
this release. Release qualification uses credential-free fixtures and makes no
new model-quality or memory-efficacy claim.

Release preparation requires all four exact-source Linux AMD64/ARM64 ×
PostgreSQL 16/18 acceptance jobs. Publish the original qualified CI wheel and
source archive with `SHA256SUMS-0.6.2.txt` and `VERIFICATION-0.6.2.json`, then
verify public downloads and clean wheel/rebuilt-source installs using Runtime
0.9.8. Check both omitted `--local-timeout` (180s) and explicit
`--local-timeout 240` through the installed standalone CLI.
