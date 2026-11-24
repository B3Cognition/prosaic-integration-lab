# Guarded workflow recovery

Install Lab 0.9.18, then copy the host.

```sh
python -m lab_runner.blueprints copy guarded-recovery ./guarded-recovery
```

The release source includes `dependencies/releases-guarded-recovery.json`.
Use `scripts/prepare_dependencies.py` and `scripts/install_dependencies.py`
with that manifest to install the exact SDKs used by the acceptance lane.

For the bounded tool recovery case, use Lab 0.9.20 and its
`dependencies/releases.json` manifest with Runtime 0.9.28 and Harness 0.9.20.
Pass `bounded_tool_recovery=True` to the copied host's `build_workflow`.
The installed test checks that the required lookup starts and completes with
the same tool version and that resuming makes no additional requests or reads.

```sh
.venv/bin/python scripts/qualify_guarded_recovery.py --origin wheel \
  --profile bounded-tool-recovery --export /tmp/lab-bounded-tool-recovery.json
```

The copied host configures one bounded workflow invocation with a required
lookup, one malformed-call correction, and up to two rule retries. The guard
compares the proposed JSON output with the delivered tool result. The host must
provide both the read callback and the authorization decision.

The private workflow receipt carries a versioned `guarded_recovery_v1`
record of retries, declined repairs and correction codes. A correction code
does not establish that a tool ran. Keep the same declared recovery options
when resuming a run. Change them by admitting a new workflow identity.

The installed synthetic cases exercise both provider protocols. They verify
one authorized read, the accepted grounded result, and zero additional
dispatch on exact resume. Live-model grammar remains separate work.
