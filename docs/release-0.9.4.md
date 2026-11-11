# Lab 0.9.4 — separate Qwen and Gemma reasoning prompts

Keep the compact constructive CRT prompt in all seven shared effort agents.
Add `subagents/gemma-medium.md`, which retains the complete tested JSON contract
and tool prohibition while omitting CRT method advice. The default Gemma example
workflow selects that file explicitly. For Qwen workflows, select the Qwen API
profile and shared xhigh agent. Profiles and the Lab multi-effort live command
do not automatically switch prompts based on model names.

The [reasoning guide](reasoning-effort.md) explains configuration and execution.
The Qwen/shared body has 95 words; the separate Gemma body has 69. Effort
metadata and native controls are unchanged. Gemma medium remains binary
thinking-on, not a distinct reasoning budget. No removed reasoning prohibition,
expected answer, worked solution, extra tool or API JSON mode is introduced.

## Retained live evidence

The [compact Qwen study](verification/reasoning-prompt-compaction-2026-11-04.md)
improved usable correct JSON from 9/18 to 15/18, retaining the original CRT fix
and correcting knapsack in all three trials. Both prompts still capped on all
three digit-counting attempts. The same shared prompt regressed on Gemma and
is not its recommended prompt.

The [final Gemma study](verification/reasoning-gemma-minimal-2026-11-04.md)
recovered all three correct-but-fenced baseline answers: usable correct JSON
improved from 9/18 to 12/18, with strict JSON in all twelve completed candidate
responses. Correct integer returns were 12/18 for both; both had six caps.
Historical shared C3 had thirteen caps, but it was not a simultaneous arm.
An earlier positive-only attempt failed formatting and stopped after sixteen
known requests; its evidence and unused allowance remain preserved.

These are adaptive prompt experiments on six reused regression questions with
three nested temperature-zero repetitions, not held-out or general accuracy
qualification. Native controls, arithmetic, formatting and completion are
separate measurements. The experiments used the same installed public Lab
0.9.3 / Runtime 0.9.12 for both arms, private candidate prose and unchanged
Python payloads. The exact selected prompt bytes are retained in 0.9.4; this
release does not relabel those observations as new 0.9.4 live runs.

## Package and publication qualification

Both checksum-pinned SDK manifests are unchanged: ordinary Runtime 0.9.8;
separate reasoning Runtime 0.9.12; Core 0.4.1, recorder 0.3.0, Harness 0.9.4
and store 0.4.0. No SDK publication, provider change or new live inference is
needed for this release.

Require all four Linux AMD64/ARM64 × PostgreSQL 16/18 acceptance cells and both
installed-reasoning architectures on the final versioned source. Qualify the
new Gemma file, unchanged Qwen bodies and explicit workflow in the wheel and
source archive. Publish original successful CI archives, safe qualification
receipts, checksums and exact source/merge provenance. Verify anonymous public
downloads and fresh ordinary/reasoning wheel and rebuilt-source consumers after
publication; attach that proof under new names without replacing release bytes.

Use the wheel for the installed CLI and packaged blueprints; use the complete
source archive for frontend/Observatory assets. The
[GitHub release](https://github.com/B3Cognition/prosaic-integration-lab/releases/tag/v0.9.4)
and its verification assets record publication status and original archive
hashes. Earlier tags, assets, failed evidence and unknown reservations are
preserved.
