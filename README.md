# Prosaic integration lab

Reference application and repeatable acceptance tests for multiuser Prosaic
Harness workflows, shared PostgreSQL persistence and customer usage accounting.

## Current status

**Documentation-only handoff.** The maintainer approved the design on 2026-10-09.
The service, container stack, test runner and CI are not implemented yet.
There are no runnable acceptance commands and no deployment/test results here.

Start with the [approved design](docs/superpowers/specs/2026-10-09-prosaic-integration-lab-design.md),
[Codex handoff](docs/handoff.md) and [tracking issue #1](https://github.com/B3Cognition/prosaic-integration-lab/issues/1).

## Planned scope

- Two identical Python service replicas and one shared PostgreSQL primary.
- Application-owned fixture authentication, run authorization and idempotency.
- Released Harness/Runtime packages and their optional PostgreSQL adapters.
- Synthetic inference and exact accounting assertions by default; no paid calls.
- Repeatable cross-worker, isolation, recovery and bounded-load acceptance tests.
- Explicitly opt-in TokenProxy tests after deterministic acceptance works.

This repository is a consumer of Prosaic, not another workflow engine. Fix
library defects in their owning repositories and retain regressions there.
Accounting means usage evidence and cost estimates, not customer invoicing.
The eventual fixture service is not a production authentication gateway.

## Continue on another machine

```sh
git clone https://github.com/B3Cognition/prosaic-integration-lab.git
cd prosaic-integration-lab
```

Open the checkout in Codex and use this prompt:

> Read AGENTS.md, docs/handoff.md, the approved design and the tracking issue.
> Prepare a staged implementation plan for the integration lab and ask me to
> review it and select an execution method before implementation. Preserve the
> public SDK, authorization, accounting and exact-owned fixture boundaries.

Python 3.12 and Docker or Podman will be needed for implementation. No package
installation or running PostgreSQL is required just to read this handoff.

## License

Apache-2.0. See [LICENSE](LICENSE).
