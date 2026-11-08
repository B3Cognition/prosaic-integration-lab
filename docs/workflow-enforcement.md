# Workflow enforcement with earlier accepted outputs

Lab0.9.9 adds the `workflow-enforcement` copy-out blueprint using released
Harness0.9.12, Runtime0.9.16 and Core0.5.0. The original recorder0.3.0/store0.4.1
remain checksum-pinned. It uses public installed SDK APIs, not a copied engine.

Lab0.9.10 retains those exact blueprint resource bytes and qualifies them with
Runtime0.9.17. Its separate [accounting host](accounting-request-metadata.md)
demonstrates frozen request labels; no enforcement or retry budget is broadened.

```sh
python -m lab_runner.blueprints list
python -m lab_runner.blueprints copy workflow-enforcement ./my-workflow-review
# Configure the copied runtime.yml privately before authorizing any calls.
python ./my-workflow-review/run.py --live --mode yaml --run-dir ./private-run
python ./my-workflow-review/run.py --live --mode native --run-dir ./other-private-run
```

Loading/listing/copying makes no model call. Destinations must not exist. The
runner selects its Python's installed Core CLI and works without ambient PATH,
including isolated Python. `--live` explicitly authorizes the configured endpoint;
qualification only uses credential-free loopback fixtures.

A trusted content-versioned final Guard binds
`<!-- enforce: review_scope(stage=final, on_violation=retry) -->` in the final
reviewer. Its step declares accepted `first_review` and `revision` inputs. At
`context.input_data['workflow']`, the Guard receives fixed version/step, nested
original request, declared accepted artifacts/bindings, sources and feedback.
It cannot acquire authority from a client/model `changed_ids` or forged workflow
field. Only currently revised IDs that were flagged previously, edited or newly
added may receive findings. Unknown, removed and untouched/unflagged targets refuse.
The text/ID predicate is example application policy, not semantic certification.

Runtime owns all guard phases and one bounded retry. Harness retains workflow
state, schema/Validator acceptance, dependency freshness and receipts. Successful
outputs retain every selected present guard dependency, including optional ones;
replacing an input invalidates outputs evaluated against its earlier binding.
Saved receipts recover from file/PG storage without another call. A changed Guard
implementation hash/version, prose, schema or logical binding refuses readmission.
Missing or malformed rule proof cannot advance an output. An uncertain lost
receipt still needs explicit retry consent; unknown usage can still block under
a token cap. Accounting is evidence, not retry consent or authorization.

`max_calls: 3` counts workflow invocations. Both invocation caps are explicit:
at most two provider requests and zero tools per invocation, at most six HTTP
requests overall. The final step has one Harness attempt, so a successful
correction uses four HTTP requests in three invocations. Cap1 never becomes2.
Rule failure/fault/exhaustion blocks with `rule_violation`, without another
Harness retry. Accepted review pauses for explicit human accept/reject; this
blueprint has no publication or external mutation action.

Native hosts register Guards through `WorkflowBindings(guards=...)` and grant
names with `WorkflowPolicy.allowed_guards`. YAML hosts use
`Workflow.load(..., guards=...)`. Optional native rule roots require an absolute
host path and a logical identity. Admission seals used full declarations and
compiled material without running Guards or discovering a Runtime. Unsupported
guarded acquisition, terminal tools, args interpolation and required file-read
receipts refuse before effects. Existing untagged contracts stay supported.
See the [Harness contract](https://github.com/B3Cognition/prosaic-harness/blob/v0.9.12/docs/workflow-rules.md).

Both YAML/native constructions and both synthetic wires are required acceptance.
Installed wheel/rebuilt-source consumers copy the actual packaged resources.
PG16/18 tests inject a lost receipt acknowledgment, reopen public stores and
recover both accepted/refused results without HTTP. Real infrastructure must
pass in the four native matrix cells; source unit tests are not stack evidence.
Existing `revision-review` V1 remains available unchanged. Other Cerebro requests
remain in the [SDK backlog](https://github.com/B3Cognition/prosaic-harness/blob/v0.9.12/docs/cerebro-requests.md).
