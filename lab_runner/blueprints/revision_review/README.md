# Versioned cross-step review — V1

Copy with `python -m lab_runner.blueprints copy revision-review /private/project`.
Lab 0.9.8 uses Core 0.5.0, Runtime 0.9.16 and Harness 0.9.11. This directory
contains a complete application-owned workflow, schemas, prose, host checks and
runner. Both Lab distribution formats include every resource.

The trusted request supplies unique stable insight IDs and text. First review
returns findings; revision returns the complete current insight list. The final
review declares both accepted outputs as required inputs. Its versioned public
Validator admits a finding only on a current insight that was previously flagged
or whose text is new/changed. Removed, unknown, malformed or duplicate IDs refuse;
model-claimed change metadata supplies no authority. Exact text comparison is a
small application policy, not semantic understanding; adapt it to your own
trusted structured diff.

The workflow permits at most four calls, with two attempts for final review.
One refused finding may be repaired; exhaustion blocks without accepting it.
It pauses for explicit human acceptance. Reconstruct with the same workflow and
`checks.validators()` registry, then use public `Harness.resume(choice='accept')`
or `choice='reject'`. A saved completion is adopted without a new call; an
interrupted unknown invocation retains the SDK's explicit recovery requirement.

`validators()` combines a semantic V1 label and the actual `checks.py` digest.
Keep that code stable throughout a run. Editing it refuses old-run resume;
replacing an earlier accepted dependency makes its dependent revision stale.
These existing public Validator/CheckContext APIs remain supported; Runtime
enforcement tags inside workflow steps are the separate future V2.

The default runtime endpoint is inert loopback port 9. Set the real model,
endpoint and secret-managed credential reference privately, then explicitly run:

```sh
python run.py --live --run-dir /a/private/new-run-directory --request request.json
```

Without `--live`, it refuses before execution. The run directory and printed
operator JSON can contain private inputs, outputs and state: never commit or
expose them as an application API. Synthetic installed acceptance uses no model
accounts and does not certify a live provider.

Invoke the Python environment containing the released SDKs. The runner selects
that environment's Core CLI explicitly, so it also works without activating the
environment or putting `prosaic` on ambient `PATH`.

Provenance: the workflow and checks come from the Apache-2.0
[Harness 0.9.11 source example](https://github.com/B3Cognition/prosaic-harness/tree/v0.9.11/examples/revision-review),
source `294e935f70e2cfcce2c4ca80dbed5d8aa3977b83`. The Lab adapts only the runner
for isolated copy-out execution and supplies this guide. Keep LICENSE and NOTICE
when copying. See the [Lab feature map](https://github.com/B3Cognition/prosaic-integration-lab/blob/v0.9.8/docs/feature-blueprints.md).
