# Lab 0.9.3 — clearer reasoning blueprints

Removes the ambiguous “hidden reasoning” prohibition from all seven packaged
effort agents. The agents still require exactly one JSON object with an integer
`answer` and forbid Markdown fences, commentary and additional fields.
Only the two-word phrase is deleted from each agent body; effort metadata,
native control mappings, tools, schemas and workflow execution are unchanged.

The preceding bounded prompt comparison tested the original instruction,
phrase deletion and final-answer-scoped wording at none/medium on the existing
Qwen and Gemma servers. Removing the phrase did not fix the observed arithmetic
errors. Native thinking remained active with positive effort under all variants.
The cleanup resolves ambiguous wording; it does not qualify improved accuracy
or a particular reasoning-token budget. JSON shape and task correctness remain
independent checks.

The [reasoning guide](reasoning-effort.md) uses the same separate manifest:
Core 0.4.1, Runtime 0.9.12, recorder 0.3.0, Harness 0.9.4 and store 0.4.0.
The ordinary manifest retains Runtime 0.9.8. Both manifests and all pinned SDK
bytes are unchanged. No additional live inference or SDK release is part of
this patch; previous live evidence and consumed allowances remain preserved.

Qualification requires all four Linux AMD64/ARM64 × PostgreSQL 16/18 cells and
both installed-reasoning architectures on the exact final versioned source.
The GitHub release publishes original successful CI wheel/source archives,
checksums, safe qualification receipts and source/merge provenance. Anonymous
downloads and fresh wheel/rebuilt-source consumers are checked after publication;
their proof is attached under new asset names without replacing release bytes.

Use the wheel for the installed CLI and packaged blueprints. Use the complete
source archive for frontend/Observatory assets. Earlier tags, release assets,
model-server settings and private credentials remain unchanged.
