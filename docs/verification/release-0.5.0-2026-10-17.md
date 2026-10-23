# Lab 0.5.0 release preparation

The maintainer authorized releasing ready work on 2026-10-17. This branch starts
from current main and adds the agent-quality benchmark and controlled retrieval
memory examples, preserving the published context-assembly baseline. Earlier
SDK pins, experimental source and private run evidence remain in their original
worktrees; they are not overwritten by release adoption.

Memory is experimental and explicitly selected. The fresh study found smaller
model 8/12 without memory versus 9/12 with it, larger model 12/12 in both arms,
increased token costs, and unresolved smaller-model missing-evidence failures.
See memory-grounding-live-2026-10-17.md for the exact frozen study and limits.
The release adopts newer public SDKs; the historical live results retain their
original candidate identity and do not qualify the new release bytes.

Release sequence: adopt published Runtime 0.9.6 and preserve current Harness
pins; update packaged provenance; run full source tests and installed wheel/sdist
checks; fresh review; required four-cell Linux/PostgreSQL matrix on final source;
publish original qualified artifacts and verify their public hashes.

Runtime 0.9.6 is published on PyPI and GitHub at source
`ed78fc8fb80e68a5687781d7db05b5f7ae117877`, qualified by
[run 39013143703](https://github.com/B3Cognition/prosaic-runtime/actions/runs/39013143703)
and promoted by
[run 39014075997](https://github.com/B3Cognition/prosaic-runtime/actions/runs/39014075997).
The first upload's immediate index check encountered propagation delay; the
public files subsequently matched the original bytes, and only the failed
publication jobs were retried. All published GitHub assets were verified too.
The Lab manifest SHA256 is
`1c4cca26b7aae4ef9fde9e35493e4264fc5ef4def15a5df05e979f590ff5d50b`.

Final local qualification: 1,159 tests passed in 153.48 seconds, with one existing
Starlette warning. Wheel and source builds passed. Both installed examples passed
under isolated Python: ten-case quality admission/native fixture dispatch and
eight memory fixture samples, with pure preflight checks. All five installed SDK
payloads matched their verified wheels and dependency checks passed. Fresh review
found no blocking issue. The earlier artifact-upload assertion failed because it
allowed only summaries; its replacement explicitly allows exactly three safe
reports and the two qualified archives, retaining the no-private-evidence boundary.

Final native qualification remains required before publication. The release's
`VERIFICATION-0.5.0.json` records the exact source, successful four-cell run,
manifest identity and case counts. `SHA256SUMS-0.5.0.txt` binds the original CI
wheel/source archives and that verification record. These are release assets,
not a replacement for the historical study's original evidence.

Next milestone: test a typed public evidence summary separating current
authoritative facts, excluded observer records and absent required facts, without
supplying a private expected decision. Use a new development freeze and fresh
held-out cases. Any further live run requires its own bounded allowance.
