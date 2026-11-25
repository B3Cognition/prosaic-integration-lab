# Lab 0.9.5 — Prosaic 0.5 SDK adoption

Both active SDK manifests now select the same published family: Prosaic 0.5.0,
Runtime 0.9.13, Harness 0.9.8, Runtime recorder 0.3.0 and Harness store 0.4.1.
Exact public wheel URLs, checksums and original source receipts are retained.
The [quickstart](quickstart.md) and Explorer badges reflect these versions.

All nine required real-stack lanes, 103 conversation/context cases and installed
native/unified/fallback commands remain required for this exact train. Unknown
or mixed trains still fail admission. Runtime 0.9.13 gives explicit artifact
effort precedence over a profile default; fixtures cover both explicit and
omitted effort. The benchmark agents still omit effort and retain their profile
default. Existing Qwen and Gemma prompt bytes are unchanged.

Previous ordinary/reasoning manifests, public benchmark provenance and memory
freeze records are preserved verbatim as named snapshots. Current freezes bind
the new SDK provenance; corpus, prompts, scoring and historical measurements are
unchanged. Earlier live studies keep their original SDK identity and limits.

## Qualification and publication

The [adoption ledger](verification/core050-sdk-adoption-2026-11-05.md) records the
completed local ARM64 source, distribution and PostgreSQL 16/18 qualification,
including the preserved initial legacy-launcher setup failure and successful
rerun. Local synthetic results do not certify providers or deployment readiness.

Release requires the final versioned source to pass all four native Linux
AMD64/ARM64 × PostgreSQL 16/18 cells and both installed-reasoning jobs. Each stack
cell requires 334 cases, zero skips and verified owned cleanup. Publish only the
original successful CI wheel/source archive, safe qualification receipts,
checksums and exact source/merge provenance. Verify equal qualified/merged trees,
anonymous public downloads and fresh wheel/rebuilt-source consumers after
publication. Add postpublication proof under separate asset names.

Use the wheel for the installed CLI and packaged examples, and the complete source
archive for development and frontend sources. The
[GitHub release](https://github.com/B3Cognition/prosaic-integration-lab/releases/tag/v0.9.5)
and its verification assets record actual publication status. Existing tags,
release bytes, failed receipts and unrelated checkout edits remain preserved.
