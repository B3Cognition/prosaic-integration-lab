# Working on Prosaic integration lab

## Read first

1. `docs/handoff.md` for the exact implemented/planned checkpoint.
2. `docs/superpowers/specs/2026-10-09-prosaic-integration-lab-design.md`.
3. The tracking issue linked from README.md and the approved implementation plan
   when one exists. There is no implementation plan at initial handoff.

The design is approved. The next step is a written implementation plan and
maintainer review/execution-method selection, not immediate service coding.
Use applicable skills available on the current machine; do not assume this
machine's absolute paths or local caches exist elsewhere.

## Ownership boundaries

This is an application/integration-test consumer. Use public installed APIs:
Harness owns workflow state, Runtime owns model execution, the Runtime recorder
owns usage evidence, and this application owns user/run authorization and HTTP
idempotency. No private imports, monkey-patching or copied library engines.

ALWAYS derive tenant, actor, billing account and namespace from trusted host
context. NEVER accept a client/model-supplied identity as authorization.
ALWAYS filter public run/usage views. NEVER return raw Harness operator state.
ALWAYS preserve frozen accounting attribution across resume. NEVER treat usage
evidence as consent to retry, authority to approve output or a customer invoice.

## Development and safety

- Use released packages with checksums and locked dependencies; do not silently
  depend on sibling editable checkouts or mutable upstream main branches.
- Keep synthetic tests credential-free. Live tests require explicit opt-in,
  secret-managed credentials and a bounded shared call allowance.
- Bind test-service ports to loopback. Fixture authentication is lab-only.
- Never commit DSNs, endpoint keys, bearer tokens, prompts from live users,
  private run state or unsanitized incident logs.
- Provision migration and runtime roles separately; runtime replicas never
  receive owner credentials or perform automatic schema creation.
- Label fixtures and verify exact resource IDs before stopping/removing them.
  Never prune global engine resources or mutate a shared existing database.
- Do not fork an active Harness execution. Construct resources inside workers.
- Run tests with watched failures before fixes. Required acceptance lanes must
  fail rather than skip missing infrastructure; verify cleanup as well as tests.
- Record actual verification commands, architectures, versions and limitations.
  A plan, successful build or synthetic test is not live/provider certification.
- If a library defect is found, add its regression/fix upstream. Stop and seek
  authority for changes/releases outside this repository's agreed scope.
- Preserve user changes. Do not push, release or delete unrelated branches or
  data without authorization. Do not spawn agents unless authorized by the user
  or applicable instructions.

No implementation/test commands exist at initial handoff. Replace this status
only after commands are implemented and freshly verified.
