# Nemotron lookup correction

Use released Runtime 0.9.26 and Harness 0.9.19. Copy this host with
`python -m lab_runner.blueprints copy nemotron-correction ./nemotron-correction`.

Call `build_workflow` from the copied `host.py` with your trusted oMLX endpoint,
read callback and authorization callback. Supply `api_key_env` as the name of
your secret-managed environment variable when the server requires a key.
Construct a `Harness` with an owned run directory to run or resume the workflow.
The host requires the first lookup by default.

One workflow invocation allows three provider requests and one tool call.
Runtime constrains the correction on a schema-invalid empty-argument lookup,
and the final guard checks the answer against the delivered result. The
private receipt records `argumentsSchema` in `guarded_recovery_v1`. Consult the
tool outcome to verify that the authorized lookup ran.
