# Qualified host token counters

Runtime owns the provider-neutral `TokenCounterRegistration` contract. Each
consumer owns counter qualification for its serving profiles. Lab's optional
local counter supports frozen Hugging Face tokenizer assets for OpenAI-compatible
native **text/tool** requests. Other framing/providers use other registrations;
Runtime and the workflow engine stay unchanged.

Install the `token-counters` extra in an isolated environment. The additional
wheel hashes for this qualification are in
`dependencies/token-counter-qualification-macos-arm64.lock`. This is a Python
3.12/macOS ARM64 witness; other platforms qualify their own wheels. SDK wheels
remain pinned by `dependencies/budget-candidate.json`.

Copy tokenizer data to a private frozen directory and hash every file. No model
weights, remote Python code or serving engines are imported. The exact library
versions are checked at load, and assets are checked before and after each count.

```python
from lab_runner.quality.local_token_counter import register_local_counter

registration = register_local_counter(
    frozen_assets_directory, assets=filename_to_sha256,
    model=approved_profile.model, variants=qualified_framing_variants,
    capacity=approved_context_capacity,
)
```

Explicit framing variants select template keywords and canonical schema
descriptions. Their maximum is counted; numerical padding is never learned from
model results. Public descriptors bind source, library versions, asset hashes
and variants. Hosts freeze serving settings separately and invalidate on drift.

Qualification compares development requests against independent serving-library
framing, then compares a bounded live sample with per-request provider usage.
It is specific to those assets, settings and request domain. Unsupported fields
fail closed: media, historical `reasoning_content`, middle system messages,
consecutive user/assistant roles and unknown schema/request vocabulary need
separate qualification before support is extended.

Use the registration with `ExecutionBudget(token_counter=...)` or the benchmark's
`token_counters={profile_alias: registration}` parameter. Existing models and
limits are independent of this implementation. Qualification probes precede
fresh held-out evaluation; held-out failures never tune counters or limits.
