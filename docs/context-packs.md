# Context-pack candidate acceptance

Hosted qualification uses the existing `Required integration acceptance` workflow
on the feature branch with `candidate=true` and `context_packs=true`. Supply the
successful exact-source Core, Runtime and Harness `Publish SDK` run IDs and
commits. The four Linux ARM/AMD64 and PostgreSQL16/18 cells verify those receipts,
retain the original recorder wheel, audit installed payloads and require all new
contracts and owned-stack cases without skips. SDK publication stays disabled.

Released-baseline CI keeps its existing SDK pins. Context-pack-only unit cases
are optional there because those packages have no such capability; setting
`CONTEXT_PACKS_REQUIRE_CANDIDATE=1` makes missing capability a failure. The hosted
candidate job always sets this flag. Legacy candidate modes keep their original
gates and cannot be silently upgraded to a different SDK train.

This candidate-only lane consumes five checksummed installed SDK wheels. It
does not change the released baseline or the historical live-evaluation approvals.
Build an isolated candidate image with `scripts/build_consumer.py`, using the
same complete manifest and wheel directory selected for the host environment.
The host also audits its installed SDK payload against that manifest's verified
cache at `.cache/wheels/<manifest-sha256>` before creating any resources. Populate
the cache with `scripts/prepare_dependencies.py` or the candidate preparation
workflow; a separately built image never substitutes for matching host bytes.
Then run:

```sh
python -m lab_runner test --mode context-packs --candidate \
  --candidate-manifest /absolute/path/to/manifest.json \
  --consumer-image sha256:THE_IMMUTABLE_IMAGE_ID
```

The lane fails without the requested capabilities, candidate lineage, Docker or
PostgreSQL. The owner-only provisioning job enables new workflow/session storage
contracts; workers use restricted roles and never perform DDL. Each invocation
creates an owned stack and verifies cleanup, including when tests fail. Context
bindings and tenant/actor identities are trusted fixture data, not public HTTP
parameters. This is SDK consumer acceptance; it adds no new HTTP API.

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
