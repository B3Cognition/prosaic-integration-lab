# Lab 0.9.19 — Nemotron lookup correction blueprint

The [copyable host](nemotron-correction.md) demonstrates the opt-in oMLX
correction for a schema-invalid empty-argument lookup. It allows one
authorized read and accepts only a response grounded in that read.

The dedicated manifest selects published Runtime 0.9.26, Harness 0.9.19,
Core 0.5.1, recorder 0.3.0 and store 0.4.5. The ordinary, reasoning and
guarded-recovery profiles keep their pins.

Synthetic installed acceptance covers both first-tool policies, an endpoint
ignoring the constraint, a wrong final answer and no-call resume. The release
qualifies the Lab wheel and the wheel rebuilt from the source archive.
