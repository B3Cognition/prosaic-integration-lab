# Rule-admission blueprint: catalogue desk

A small, copyable agent that uses the whole rule-admission mechanism: prose
declares which rules a host may check, the host registers the guards that check
them, and a floor in operator config says which checks prose may never drop.
The domain is an invented lending library; every record, title and fee is
synthetic.

> **Candidate status.** This blueprint uses published Prosaic Core 0.5.0
> and the rule admission in Runtime from
> [prosaic-runtime#16](https://github.com/B3Cognition/prosaic-runtime/pull/16),
> at `498ffc7`, which is still in review. `harness.py` additionally needs the
> Harness companion `5b3f0f2`. These two exact-commit candidate wheels are distinct
> from the published Runtime 0.9.13/Harness 0.9.8 packages.

## What is in the folder

| File | What it shows |
| --- | --- |
| `.prosaic/subagents/catalogue-desk.md` | The agent. Tags at `before_tool`, `before_answer` and `final`, plus one `prose-only` rule. |
| `companions/loan-desk.md` | A companion rule file: plain Markdown, no frontmatter, outside `.prosaic/`. It binds the same custom guard at `after_tool`. |
| `guards.py` | One custom domain guard, `loan_period_within_policy`, and `registry()`: the four generic Runtime guards plus that one. |
| `host.py` | Host wiring: synthetic tools, two-file composition, config loading and `build_runtime()`. |
| `harness.py` | Graph-free Harness bindings with the same composition, floor, tools and host guards. |
| `runtime.yml` | Operator config: the endpoint and the `required_guards` floor in both forms, covering the custom guard too. |
| `coverage.py` | Answers "which of this agent's rules are enforced, and by what?" |

Importing the package checks the installed SDKs first. A Core without
`parse_rules` or a Runtime without rule admission is refused with a clear
message.

The agent's rules, and what enforces each one:

| Rule (prose) | Guard | Stage | Action |
| --- | --- | --- | --- |
| Only place loans on records the borrower named or the search returned | `args_reference_seen_ids` (generic) | `before_tool` | `fail`, pinned by the floor |
| Never request a loan longer than 21 days | `loan_period_within_policy` (custom) | `before_tool` | `fix`: rewrite `days` to the limit; `max_days` pinned by the floor |
| Plain Markdown links, never wrapped | `no_wrapped_links` (generic) | `before_answer` | `fix`: unwrap |
| State only fees the lookup returned | `value_in_tool_output` (generic) | `final` | `retry`; the floor's minimum |
| Be patient with first-time borrowers | none (`prose-only`) | n/a | left to the model, by design |
| Stop on a loan period the desk reports above policy (companion) | `loan_period_within_policy` (custom) | `after_tool` | `fail`; `max_days` pinned by the floor |

`args_reference_seen_ids` accepts an id the borrower typed in their message as
well as ids from this turn's tool results. The rule text says so, because the
model is told what is enforced. A search *query* that contains an id is not
evidence; only the search *results* are.

## Look before you run

Everything in this section is offline: no model, no key, no turn.

```sh
cd catalogue-desk            # the copied folder
prosaic inspect subagents/catalogue-desk.md --json   # rules and ruleIssues, as Core reads them
python -m lab_runner.rule_admission.blueprint.coverage            # or your own package path
python -m lab_runner.rule_admission.blueprint.coverage --json
```

`coverage` prints one row per declared rule: status, guard, guard version,
stage, effective action and floor. The status is one of:

- `enforced`;
- `unregistered`;
- `prose-only`;
- `superseded`: a same-stage binding of the same guard, with the same settings,
  in another file has a stronger action and replaces this one. Different
  settings at the same stage are refused by admission.

It then reports whether admission accepts the agent, any cross-file binding
warnings and the rules fingerprint. The verdict comes from the same steps a
turn takes, so it can't disagree with a real turn:

1. The runtime is constructed. A required guard the host did not register is
   refused here as `startup`.
2. The host's composition checks run (`hostPolicy`).
3. `prepare_turn` runs, which makes no provider request.

The command exits non-zero whenever admission refuses, including for a
malformed tag.

## Copy it into your project

The folder is a Python package. Copy it into your application's package so that
`host.py`, `guards.py` and `coverage.py` import each other:

```sh
BLUEPRINT=$(python -c "from lab_runner.rule_admission import BLUEPRINT; print(BLUEPRINT)")
cp -R "$BLUEPRINT" src/yourapp/catalogue_desk
python -m yourapp.catalogue_desk.coverage
```

### 1. Rename the agent

Rename `.prosaic/subagents/catalogue-desk.md` and change `name`, `description`
and `tools` in its frontmatter. Update `AGENT`, `COMPANIONS` and `TOOLS` in
`host.py`, and move or rename the companion files under `companions/`. Replace
`library_tools()` with your own `CustomTool` registrations;
the catalogue in `host.py` is synthetic fixture data. Rule ids are
`file:line:guard`, so renaming changes ids. The fingerprint uses the file name
too, so it changes once; later edits above a rule do not change it.

### 2. Write prose rules

Write each rule as one list item or one plain line. A rule must be worth stating
to the model even when nothing checks it: the model always receives the prose,
with every tag removed by Core's `strip_tags`. Keep anything that is a matter
of judgement as prose, and say so with a `prose-only` tag:

```markdown
- Be patient and welcoming with first-time borrowers. <!-- prose-only: tone is judged by people, not checks -->
```

### 3. Tag them

Put the tag on the rule's own line, or on a tag-only line directly below it:

```markdown
- Never request a loan longer than the 21-day loan policy. <!-- enforce: loan_period_within_policy(max_days=21, stage=before_tool, on_violation=fix) -->
```

- `stage`: `before_tool`, `after_tool`, `before_answer` or `final`. The default
  is `final`. If the floor pins a stage, state that stage explicitly.
- `on_violation`: `fix` (repair, then recheck every rule), `retry` (ask the
  model again once per turn, with feedback quoting the rule) or `fail` (stop with
  a safe result and failure code `ruleViolation`). The default is `retry`.
- Core allows **one binding per guard per file**. To bind the same guard at a
  second stage, put that rule in a companion file, as `companions/loan-desk.md`
  does, and compose both files in the host (`host.compose`).
  - **Keep companions outside `.prosaic/` and without frontmatter.** A file
    under `.prosaic/subagents/` with frontmatter is an agent: `prosaic apply`
    would distribute it on its own, with its tools and none of its guards.
  - `compose` reads a companion with Core's `parse_rules`. It refuses a
    companion with frontmatter (even after a BOM or blank lines), and a file
    listed twice.
  - Each binding keeps its own file, so the companion's rule is reported and
    fingerprinted separately.
- Settings are data checked against the guard's schema at admission, never
  code. A tag never grants a tool, a file or budget.

Run `coverage` after each change. Any tag problem stops admission: a malformed
tag may have been meant as a `fail` rule.

### 4. Register guards

Guards are host code. Markdown can name a guard; it can never define one. Add
your own next to `LOAN_PERIOD` in `guards.py`:

```python
Guard('loan_period_within_policy', 'loan-period-v1', ('before_tool', 'after_tool'), check,
      fixes=True, settings_schema={...closed object schema...})
```

- `version` goes into the fingerprint. Change it whenever the check's
  behaviour changes.
- `stages` lists every stage the guard supports. Binding any other stage is
  refused at admission.
- `fixes=True` only if `check` returns a repair in `Verdict(fixed=...)`. `fix`
  on any other guard is refused at admission, not at run time.
  - Runtime's `fixes` covers the whole guard, though. This guard repairs only at
    `before_tool`; at `after_tool` the loan already exists.
  - List such limits in `REPAIR_STAGES` in `guards.py`. `host.compose` then
    refuses `fix` at any other stage before any request, and `coverage` reports
    it as `hostPolicy`.
  - Without this, Runtime would admit the binding and fault it at run time.
- Say where the guard must run, too. The floor only requires a guard to be
  bound *somewhere*. Without a stage check, prose could drop the `before_tool`
  tag and keep only `after_tool`, so a 300-day loan would be placed before the
  turn failed.
  - List the stages in `REQUIRED_STAGES` in `guards.py`. Once the guard is
    bound, `host.compose` refuses it unless it is bound at every listed stage.
    `coverage` reports that as `hostPolicy`.
  - Whether the guard is bound at all stays the floor's job, so the untagged
    agent still composes.
- Enforce the policy in the tool as well. `place_loan` in `host.py` refuses a
  period above `LOAN_TERMS` itself. The guard repairs the request first, so the
  desk's refusal is only reached when no guard runs.
- `echo_values=True` only if refused values cannot carry instructions. The
  generic `value_in_tool_output` opts in because its values are figures such as
  `EUR 1.20`. This guard's values are integers, but tool-stage feedback always
  carries values anyway.
- Keep `check(stage, context)` quick, bounded and free of side effects. It
  returns `Verdict(ok, reason, refused_values, fixed)`. A raise or an unusable
  verdict fails the turn and is listed in `rules_faulted`.
- Compare numbers by value, never by Python type. JSON Schema's `integer`
  accepts whole-number floats, so a model can send `"days": 28.0`; a check that
  only looks at `int` would let that through. Bools are not numbers.
- Don't call `math.isfinite` on an int: it converts to float and overflows for
  an int such as `10**400`. Keep refused values small enough to deliver as
  feedback; Runtime faults a guard whose values it cannot deliver.
- Fail closed on effects you cannot confirm. At `after_tool`, this guard treats
  a placed loan with a missing or unreadable `loanDays` as a violation. A tool
  error, or a result with no loan placed, passes.

Pass `registry()` to `ProsaicRuntime(config, guards=...)`, as `build_runtime`
does. An agent that names an unregistered guard is refused before any request.

### 5. Set the floor

`required_guards` in `runtime.yml` is host policy that prose can tighten but
never weaken:

```yaml
required_guards:
  value_in_tool_output: retry                 # minimum action
  args_reference_seen_ids:                    # pinned: stage and settings are authoritative
    action: fail
    stage: before_tool
    settings: {keys: [recordId]}
  loan_period_within_policy:                  # the domain guard is protected too
    action: fix
    settings: {max_days: 21}
```

The agent is refused with `invalidPolicy`, before any request, if it:

- omits a required guard;
- binds one with a weaker action;
- changes a pinned stage;
- adds or changes pinned settings.

Put your own domain guard under the floor, or prose can raise its limit or drop
it. Leave its `stage` unpinned when it is bound at more than one stage: a pinned
stage applies to every binding, and would refuse the companion's `after_tool`
rule. The floor only requires a guard to be bound **at least once**, so the
host's `REQUIRED_STAGES` check (step 4) refuses prose that drops or moves one of
the guard's stages.

The 21-day limit appears in the prose text, both tags, the floor and the
synthetic `LOAN_TERMS`. Admission refuses tag settings that differ from the
floor. A Lab test checks that the prose text and `LOAN_TERMS` agree with it.

The refusal detail names the guard and the pin, never the prose values. The
floor applies to every agent this runtime admits; give an agent with a
different floor its own `ProsaicRuntime`. It applies only to Python hosts that
register guards. Keep it out of configs the `prosaic-runtime` CLI reads.

## Run a turn

```python
from yourapp.catalogue_desk import host

runtime = host.build_runtime(host.load_config())
turn = runtime.turn(host.compose(), message='Borrow the Atlas of Invented Rivers for 14 days.',
                    policy=host.policy())
turn.result.stdout        # the accepted answer, after any repairs
turn.rules_evaluated      # rule ids checked this turn
turn.rules_violated, turn.rules_fixed, turn.rules_faulted
turn.rules_fingerprint    # SHA-256 over each binding's guard, version, file, stage, action and settings
```

Store `rules_fingerprint` with each turn. It changes when a binding's action,
settings, stage or guard version changes, even if the prompt bytes do not. It
does not change when you edit text above a rule.

A real turn calls the endpoint in `runtime.yml`. Put models and endpoints in
that file; read credentials from the environment, never from Markdown.

## Run through Harness

```python
from yourapp.catalogue_desk.harness import build_bindings
from prosaic_harness import Conversation, ConversationScope, FileSessionStore

scope = ConversationScope('library', 'production', 'catalogue', 'tenant', 'actor')
store = FileSessionStore('/host-owned/sessions', namespace=scope.namespace)
store.initialize()  # Provision once; workers can use check_ready().
conversation = Conversation(build_bindings(), store=store, scope=scope)
session = conversation.create()
reply = conversation.send(session.session_id, message_id='borrow-1',
    message='Borrow CAT-0001 for 14 days.', expected_revision=session.revision)
```

Derive scope and storage paths from trusted host context. A fresh worker supplies
the same binding version, guards and logical project identity. Guarded failures
persist as `ruleViolation`; saved receipts retain rule IDs and the fingerprint,
and recovery/replay does not repeat model or tool calls. Guard version, stage,
settings-contract or policy drift changes binding identity and refuses resume.
The host passes an explicit rule project so path-setting guards never use worker
CWD. Replace synthetic tools before using this in an application.

## Limits

- Rule hooks run in conversation turns only (`ProsaicRuntime.turn`). `run()`,
  `NativeRuntime` and `UnifiedRuntime` refuse enforce-tagged prose instead of
  running it unenforced.
- Harness support is qualified only with the exact companion candidate; published
  Harness 0.9.8 and earlier still lack that support. Legacy graph `run()` remains
  outside the rule-hook contract. Upgrade all shared-session readers together.
- `value_in_tool_output` reads a currency code or symbol before the number, in
  any case (`EUR 1.20`, `eur 1.20`, `€1.20`, `€1,20`), and a symbol after it
  (`1.20 €`). It does not yet read a code or word after the number (`1.20 EUR`,
  `1.20 euros`) or minor units (`120 cents`). An invented fee written that way
  passes. The Lab tracks these as expected failures against prosaic-runtime#16.
- The Runtime capability check cannot distinguish every #16 candidate. Pin the
  exact build, as the Lab does, and run its install audit; a version string alone
  cannot distinguish the released package from these candidates.
- An agent with every tag stripped runs byte-identically to the tagged one when
  no guard fires, with or without guards registered. It is still refused by a
  runtime whose floor requires guards.
