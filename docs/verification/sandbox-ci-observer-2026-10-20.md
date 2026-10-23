# PR22 process-inventory portability repair

The first four Linux cells at6af89f4 passed the mandatory actual native sandbox
smoke on AMD64/ARM64, then each failed the same four direct timeout/output
regressions (1820passed/4failed). The missing witness was the owned child;
the guard refused qualification. No sandbox gate was skipped or relaxed.

An owned, network-disabled GNU procps4.0.2 diagnostic reproduced a truncation
defect in the exact source observer: inherited COLUMNS=80 hides the executable
or trailing nonce. Requesting unlimited width with ps -ww preserves the child
marker at80/120/200columns. The same exact-source diagnostic failed before
and passed after the fix. The committed regression exercises real ps with a
long owned child command at all three widths. Failure diagnostics expose only
owned process/group counts, never unrelated command lines. Exact-head CI must
still establish whether this accounts for the original four failures.

Native macOS arm64 qualification:58focused tests pass in71.87seconds, including
all required sandbox scenarios, optimized Python and saved network-denied
inspection. The fresh0.6.0 wheel/sdist build passes. Full source regressions and
fresh public wheel/rebuilt-sdist adoption are running; CI remains required.
Artifacts/logs use the private prosaic-pr22-observer prefix; earlier0.6.0
artifacts and all historic evidence remain immutable.

No SDK/dependency changes, live requests, limit changes, package publication or
merge. Memory and correction remain experimental.
