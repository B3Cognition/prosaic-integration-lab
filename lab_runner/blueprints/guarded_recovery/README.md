# Guarded workflow recovery

Use Runtime 0.9.25 and Harness 0.9.19. Copy the example with
`python -m lab_runner.blueprints copy guarded-recovery ./guarded-recovery`.
Call `build_workflow` from the copied host with the provider configuration,
the trusted lookup callback and its authorization callback. Construct a
`Harness` with an owned run directory to run or resume the admitted workflow.

The fixture allows one lookup and five provider requests in one invocation.
The correction, tool continuation and two guard retries share that request
limit. A final guard rejects a wrong draft and declines a direct repair.
A successful synthetic run executes exactly one authorized lookup.

Read `result.metadata.guarded_recovery_v1` in the private invocation receipt
for the retry count, declined and retried rule IDs and correction codes.
Check the tool outcome separately to establish delivery. Resume with the
same settings. Changing either setting requires a new workflow identity.
