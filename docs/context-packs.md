# Context-pack acceptance

Lab 0.9.12 consumes Runtime 0.9.19, Harness 0.9.13 and Harness PostgreSQL 0.4.2,
with the original Core 0.5.0 and Runtime recorder 0.3.0 public bytes. The ordinary
required acceptance matrix runs context packs in every Linux AMD64/ARM64 and
PostgreSQL 16/18 cell. Historical released trains retain their original gates.

Prepare the complete checksummed manifest and its cache with
`scripts/prepare_dependencies.py`, then install exactly those wheels in the host
environment. Build an isolated consumer image with `scripts/build_consumer.py`
using the same manifest and wheel directory. Run:

```sh
python -m lab_runner test --mode context-packs \
  --consumer-image sha256:THE_IMMUTABLE_IMAGE_ID
```

The runner verifies the host SDK payload against `dependencies/releases.json`
and `.cache/wheels/<manifest-sha256>` before creating resources. An image alone
does not substitute for matching host bytes. Missing capabilities, mismatched
payloads or unavailable Docker/PostgreSQL fail qualification. The owner provisions
new context storage contracts explicitly; restricted workers never perform DDL.
Every invocation creates an owned stack and verifies cleanup, including on failure.
Bindings and identities are trusted fixture data, not public HTTP parameters.

For prepublication qualification, the existing manual `candidate=true` and
`context_packs=true` lane consumes complete exact-source successful SDK receipts.
Supply `--candidate --candidate-manifest /absolute/path/to/manifest.json` for a
local candidate run. Candidate lineage remains mandatory there; public runs bind
the released manifest instead. Both modes enforce the same 12 no-skip cases.

Twelve no-skip cases cover Markdown agent defaults and node overrides; an explicit
service lookup producer and its accepted structured result; citations and actual
deferred reads; partial, absent and contradictory records; revocation and foreign
scope refusal; receipt adoption by a fresh controller; default capacity; and denied
runtime-role DDL. The synthetic provider listens only on loopback. Assertions
compare expected context membership, undeclared disclosures and provider/tool
counts against real requests and stored records. They do not judge model quality.

Local-build lineage must say `kind: local-immutable-build` and must not contain
invented successful hosted run IDs. Promotion still requires the SDK release
receipts and complete hosted gates. A passing local lane does not certify them.

## Optional real-model evaluation plan

Pin a held-out question set and source revisions before execution. Include
Kafka dependencies, release-email impact, Markdown review, empty lookups,
pagination/partial data and conflicting/stale observations. Record expected
required facts, permitted citations and unsupported-claim checks before seeing
model responses. Keep tuning questions separate from held-out questions.

Compare unchanged full-context baseline, static packs and packs with the reader,
using the same model revision, provider parameters, tool grants and per-question
total budget. Randomize order and run repeated trials. Score answer correctness,
required-fact recall, unsupported claims, conflict/staleness handling, citation
accuracy, duplicate reads, total provider input tokens, latency and full cost,
including context counting and tool traffic. Report uncertainty and failed or
unknown-usage calls; do not report savings from byte estimates as token savings.

Paid execution needs a separate explicit opt-in, reviewed bounded allowance and
secret-managed credentials. No such calls are made by this acceptance lane.
