# Balanced memory benchmark follow-up — 2026-10-26

The maintainer authorized fixing query fairness and per-query selection, then
qualifying Qwen before another large model comparison. The new explicit
`terms-round-robin-v2` policy is implemented; `literal-first-v1` remains the
default. Memory and SUE remain disabled, SUE/SOAR stay separate, and no package
publication or remote push is authorized by this work.

## Changes and regression evidence

The file baseline now searches the same normalized keyword intent instead of a
contiguous phrase. It prioritizes at most five matching line anchors/query by
distinct keyword coverage, path and line. Every keyword is matched independently
by rg to preserve its Unicode word boundaries and overlapping-term coverage.
Exact JSON UTF-8 byte anchors are converted to character offsets. Both retrieval
arms allocate five visible opens across queries round-robin; duplicate path/line
or record candidates do not consume another slot. Castle's returned per-query
rank order is preserved, and expanded retrieval reuses it exactly.

Review found Unicode-boundary mismatches, inherited non-LF separator handling,
and overlapping-keyword undercounting. Each was reproduced before its fix.
Source lines now follow rg's LF delimiter while preserving CRLF and other
Unicode separators exactly. No schema, generation prompt, strict validator,
scorer, canonical critic, shared allowance or source/scope check was relaxed.

| Verification on macOS ARM64 / Python 3.12.15 | Result |
| --- | --- |
| Final full SDK-only unit/functional suite | 2,142 passed, 73 passing subtests, one existing Starlette deprecation warning; 493.90 seconds |
| Installed constrained-generation candidate and new policy regressions | 45 passed, 36 passing subtests; 27.65 seconds |
| Focused policy/UTF-8/budget/dataset/recovery tests | 59 passed |
| Old-policy source-only reconstruction | All 300 previous captures match exactly except elapsed time; zero model/worker calls |
| New real-provider retrieval diagnostic | 300 captures, then all 300 saved captures independently source/provenance/digest validated with zero calls |
| Source/wheel/sdist/installed Python identity | 209 Python payloads match |

Earlier failing regression logs, initial builds and review reports remain
preserved. The earlier first-stage full suite also passed 2,132 tests; it is
identified separately from the final post-review run. No PostgreSQL/native Linux
matrix was rerun for this consumer-only policy change.

## Same 100 questions, new declared policy

The 100 questions, queries, key, 18 source files, 414 imported records and scope
grants remain unchanged. Only the explicitly frozen policy/code identity changes.
The key stays separate from retrieval and model inputs. There are 90 supported
questions and ten scope/abstention controls. The 239 reference attachments
represent 166 distinct source intervals; repeated paragraphs can support more
than one required facet.

| New retrieval policy | Reference attachments visible / 239 | Supported cases with all references visible / 90 |
| --- | ---: | ---: |
| Keyword file search | 231 | 87 |
| Raw Castle FTS | 181 | 60 |
| Same Castle hits with bounded expansion | 239 | 90 |

These are source visibility measurements, not correct-answer or abstention
scores. The new fixed file baseline has no empty-context case. It exceeds raw
FTS reference visibility on 32 cases; bounded expansion exposes the eight
attachments still missing from file search across three supported cases.

Compared with the original policy, file search gains 205 attachments and loses
none; expansion gains the three previously missing attachments and loses none.
Raw FTS gains 26 attachments but loses three across two cases: balanced selection
has a real five-slot tradeoff. Nine of the 200 raw result sets also differ after
query normalization, so not every raw change can be attributed solely to open
selection. The old policy remains available and its reconstructed captures are
unchanged. The new expanded arm covers all old/new reference attachments in this
sample; this does not establish production recall or generalization.

This is a declared bounded keyword baseline, not adaptive human/agent file
search. Tokenization, stemming, ranking and line/chunk units still differ.
Expansion reuses searches and a warm provider; timing medians are not an
independent speed comparison. Both arms retain the same 32 KiB display limit,
five-open cap, per-open cap, cache and strict scope/provenance checks.

## Qwen did not qualify

A separate preflight froze three known cases (default behavior, enabled-memory
qualification and excluded-source scope), nine samples with optional review,
27 maximum requests and 884,736 reserved tokens. The same local
Qwen2.5-Coder-7B model, strict schema, prompts, 60-second call limit and no-tools
policy were retained. Generation, scoring and allowance modules are byte-for-byte
unchanged from the preceding study.

The first file-search answer request timed out after 60.35 seconds. The outer
sample took 61.47 seconds; no output or token usage was reported. One request was
initiated, eight samples are blocked, and zero answers or critic revisions were
accepted. The full 100-question model batch was not started. The new unknown
entry retains its full three-request / 98,304-token reservation. All three
earlier unknown reservations remain separate and unchanged. No retry or
settlement was performed.

The failed request carried 75,789 canonical argument bytes, including 27,633
display bytes and a further 25,664 bytes of duplicated source quotation text in
80 address-index entries. This makes payload size a plausible contributor,
not a demonstrated root cause of the timeout. Actual model token cost remains
unknown. Critic benefit and answer completeness remain unmeasured.

Next, qualify a smaller model-facing evidence/address representation in a new
profile while retaining raw artifacts, exact host scope/provenance validation
and the unchanged semantic scorer. Do not silently raise deadlines, accept
invalid spans, manufacture usage, or treat this preflight as a passing review.
No such generation change is included here.

The unchanged released dependency manifest still lacks Runtime's public
`json_schema_v1` capability. Execution requires the separately checksummed
`0.9.8+jsonschema.2` candidate; normal published-version guards remain intact.
Private sources, exact reports, receipts, failed evidence and artifact hashes
remain outside Git in the balanced study archive.
