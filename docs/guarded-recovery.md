# Guarded workflow recovery

Install Lab 0.9.18, then copy the host.

```sh
python -m lab_runner.blueprints copy guarded-recovery ./guarded-recovery
```

The release source includes `dependencies/releases-guarded-recovery.json`.
Use `scripts/prepare_dependencies.py` and `scripts/install_dependencies.py`
with that manifest to install the exact SDKs used by the acceptance lane.

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
