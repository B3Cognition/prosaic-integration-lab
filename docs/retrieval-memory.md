# Controlled retrieval memory

This Integration Lab consumer experiments with read-only recall of synthetic prior
episodes. It is separate from evidence-review-v1 and does not change Core, Runtime
or Harness. The model must verify current sources through native lookup; recalled
notes never authorize actions or establish current facts. This first retriever is
deterministic lexical overlap, not vector search or semantic memory.

The corpus and historical source snapshots undergo strict host admission. References
must match the canonical historical record hashes. Tenant/asOf selection comes from
the trusted case, before ranking; future notes and foreign tenants are excluded.
Retrieve at most3whole episodes/4096UTF-8 bytes. No model-generated memory is saved.
Malformed global artifacts stop host admission; this experiment does not implement
a hostile-operator or constant-time multi-tenant service boundary.

Native execution receives one frozen request. Enabled and disabled conditions
differ only in recalledEpisodes; both have the same current index, tools, schemas,
prose and budgets. Host retrieval is measured separately from native tool calls.
Validation checks only current-attempt records and gives closed error categories
plus fixed public field/authority/absence guidance; it never supplies an answer
target. Dynamic identifier domains derive only from public task/index fields;
missing required labels remain legal and every current source decoy stays available.
Final scoring uses private expected assertions.

The development freeze binds retrieval/prose/code/corpus before evaluation authoring.
The evaluation freeze separately binds12cases, two per relevant/stale/no-match/
foreign-tenant/hostile-note/missing-current-fact family. Held-out means not used for
retrieval/prose tuning; it does not mean the implementation author is blind to the
answers. Any later tuning requires a fresh evaluation set or a development-set label.

With a qualified installed environment:

```sh
python -m lab_runner.retrieval_memory
python -m lab_runner.retrieval_memory --fixture --output /absolute/private/memory-fixture
```

Default preflight is unexecuted and reads only packaged resources and installed
metadata. It does not create directories, read secrets or contact providers. Fixture
mode executes48actual scripted native samples:12cases x2memory arms x2synthetic
profiles. It is not evidence of live memory efficacy. Arm order alternates by case.

Live mode requires explicit bounded authorization and a private JSON config with
version1, runtimeConfig, profiles, allowanceFile, limits and caseLimits. Use the two
approved existing profiles and secret-file/environment references in Runtime YAML;
no keys in JSON/prose. Runtime-wide tools/catalogues must be empty. Fixed case caps
are4provider requests/2native tools/8192reported tokens/600s. A full48sample schedule
reserves at most192requests/96tools/393216tokens and28800s overall; these are bounds,
not predicted usage. Never reset previous allowances or retry uncertain requests.

```sh
python -m lab_runner.retrieval_memory --live --config /absolute/private/memory.json \
  --output /absolute/private/memory-live
```

Exact repeated schedules/output adopt saved evidence without inference. Use the
same command with --recover-only to adopt saved receipts without starting any new
samples. Missing receipts block. Ordinary publication failures first attempt receipt
adoption; any unknown reservation remains fully charged even if later receipt
adoption establishes the outcome and observed usage. retainedUnknownSamples reports
these full budget holds separately. Such holds stop later samples. Recovered original
execution latency is unknown. Recovery reuses frozen context without retrieval
or provider dispatch. Local corpus/current-source drift blocks resume; valid changes
to foreign history preserve local identity and context. Global roots stay private.

Public summaries show paired outcomes, first-pass success, semantic/schema corrections,
native calls, separate retrieval counts/bytes/timing, recall/precision@3 and corpus
coverage with explicit denominators. Empty gold or result denominators yield null,
not fabricated perfection. Raw notes, queries, tenant IDs, paths and source IDs remain
in private0700directories/0600files. Host evidence is not provider attestation.

Run full Lab pytest, build wheel/sdist, audit installed payloads and run
scripts/retrieval_memory_smoke.py with -I and --source-root. Verify all48fixtures,
recovery and provider/socket-denied byte-identical replay before live authorization.
A full measured baseline can contain failed tasks. Do not infer production readiness
or population gains from one tiny synthetic comparison. The existing512token response
truncation remains a separately observed provider-budget failure, not silently fixed.
