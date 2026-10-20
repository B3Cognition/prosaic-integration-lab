# Consumer blueprint: sandboxed CLI tools

This experimental example uses the existing public Runtime0.9.7 CLI sandbox.
The consumer owns admission and approvals; Runtime owns dispatch, isolation,
budgets and accounting. Core does no execution. Python callbacks and validators
remain trusted in-process code. The blueprint has no model-specific tuning.

## Admit a narrow invocation

```python
from lab_runner.sandboxed_tools import admit_sandbox

admission = admit_sandbox(runtime_config, run_policy,
    workspace=private_workspace, manifest=trusted_manifest,
    required_controls=["filesystem", "network", "credentials", "timeout",
                       "output", "same_group_cleanup"])
if not admission["admitted"]:
    raise RuntimeError(admission["reason"])
```

This static check requires required-mode confinement, one explicitly allowed
tool, narrow existing workspace-relative reads, no granted host sockets, no
extra runtime roots, no passed environment keys and explicit invocation bounds.
The manifest is trusted host configuration, never model-supplied. The SDK still
validates it. Trusted interpreter/library roots remain readable dependencies.
Freeze the manifest, executable and evidence before approval; prevent concurrent
writes or untrusted owners. Hash checks alone do not eliminate filesystem races.

CPU, memory, process-count and detached-process cleanup requirements return
`unsupported_controls` and refuse dispatch. Runtime exposes no such hard caps
through this configuration. Timeout/output bounds and same-group termination
are narrower guarantees. This is not general hostile-code or resource-DoS
certification. A consumer needing those controls needs an additional qualified
OS/container boundary before admission.

## Bind permission, then enforce

The complete example is `lab_runner/sandbox_fixture.py`. It calls public
`prepare_turn()` without probes or inference, then binds its context identity,
manifest/executable/evidence hashes and case limits to a trusted host decision
in `ApprovalGate`. The host spends `start_sandboxed_turn` once before public
`preflight()` and `turn()`, using the same complete `InvocationScope`.

This permission covers one frozen bounded turn: up to4requests,2tools,
8192reported tokens,600seconds and512output tokens per response. It is a host
start action, not a CLI authorizer callback or per-effect consent. Models cannot
approve themselves. Authenticate operators in your application. A spent start
permission does not prove effect completion or permit automatic retries.

Required mode uses native Seatbelt on macOS and Bubblewrap>=0.12.0 on Linux.
Failed operational preflight blocks execution, even after permission is spent;
never fall back to off mode. Backend presence alone is insufficient. CI builds
a pinned Bubblewrap commit and grants user-namespace creation only to its
broker on disposable Ubuntu runners; host-wide restrictions remain enabled.

Successful CLI results come from public `TurnEvidence`, never the final model
text. With bounded recovery enabled, timeout/output failures stop as
`toolEffectUncertain`, with no completed tool outcome. This SDK version does
not expose the exact CLI failure subtype in that turn receipt. Preserve the
uncertainty; independent owned process witnesses verify cleanup without
turning an unknown effect into success.

## Qualify before adopting

From a source checkout with the public dependencies installed:

```sh
python scripts/sandboxed_tools_smoke.py --source-root . --output /absolute/fresh/private/proof
python scripts/sandboxed_tools_smoke.py --source-root . --output /absolute/fresh/private/proof --replay
```

For isolated installed qualification, omit `--source-root` and run with `-I`.
The recipe runs six scenarios on both scripted provider formats: confinement,
timeout, output overflow, denied permission, unsupported requirements and off
mode rejection. Its unrestricted positive controls touch only owned synthetic
files, listeners and a fake credential. They are diagnostic controls, never a
production fallback. Host TCP/UDP/Unix witnesses verify no sandbox delivery;
two calls verify distinct removed scratch directories. Bounded same-group
children are observed before failure and checked absent afterward.

Saved receipt inspection denies sockets, reads private bounded regular files,
verifies corruption checksums and uses public receipt validation. It performs
no Runtime execution, provider request, renewed consent or usage refund. The
checksums are not protection from a malicious trusted host rewriting the entire
receipt set. Drain writers and restrict access before inspection. Keep raw
receipts private; only sanitized summaries belong in shared reports.

See [qualification](verification/sandboxed-tools-2026-10-20.md) for the exact
tested artifacts/platform and remaining gates. No live inference is required;
memory and correction remain experimental and existing allowances unchanged.
