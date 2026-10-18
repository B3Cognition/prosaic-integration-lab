# Consumer-owned role qualification and evidence diagnostics

Build an adoptable Lab blueprint, not special handling for named models. Core
owns distribution, Runtime execution, Harness orchestration; consumers own role
fitness, domain evidence policy, acceptance and authorization. No SDK changes.
Use the existing Python consumer and public installed dependencies.

Add generic `lab_runner.role_qualification` APIs: assess a closed JSON output
contract against host-supplied field checks; bind qualification to schema,
profile fingerprint, adapter/evaluator/evidence/suite revisions and budgets;
aggregate complete consumer-defined scenario coverage; reject stale, partial,
failed, abstaining or synthetic-only qualification before optional live use.
A host-pinned report digest provides integrity, not a signature or call consent.
Qualification never executes a model, reserves allowance or authorizes a tool.
Synthetic qualification must never become live eligibility. Trusted host input
is mandatory; client/model reports cannot be trusted attestations.

Field checks use JSON pointers, canonical equality or unordered unique arrays,
and host-granted evidence references. Diagnostics contain codes/field paths and
references, not raw expected/observed values or provider payloads. Treat invalid
JSON/schema, unknown usage, component budget violations and explicit abstention
separately. Inline bounded schemas only; no remote schema resolution.

Add a rollout-task adapter in `lab_runner.handoffs.diagnostics`. It verifies
sample/assignment/invocation and source hashes before deriving expected fields
from scoped fetched records and the public task. Worker diagnostics cover all
five fields. Critic diagnostics expose missed/unsupported issue fields and
distinguish a correct coarse warning from complete verification. Original
receipts stay intact; unknown evidence must not manufacture a verdict. The
generic module contains no rollout grammar, provider, model or transport branch.

Publish a guide showing consumer replacement points, trusted evidence boundary,
record pinning and invalidation, separate synthetic/live qualification, retained
unknown accounting and existing budget admission. No automatic model selection,
prompt changes, repair, retry or live study in this milestone.

Preserve limits:4requests/2tools/8192reported tokens/600seconds/output512 per
case. Current cumulative ceilings1524/625/1976623 and charges1494/605/1805193
remain unchanged, including eight historical unknown reservations. No live calls.

Offline proof: behavioral tests of generic APIs using another domain, stale and
tampered attestations, synthetic/live separation, malformed output, all-field
diagnostics, evidence-scope corruption, both existing synthetic wire adapters,
full Lab suite, built/installed wheel smoke and one fresh final review. Keep old
frozen environments/evidence intact; use a new candidate version/environment.

Execution choices above are implementation judgments under the user's explicit
provider-neutral, native execution instruction; no extra design approval needed.
