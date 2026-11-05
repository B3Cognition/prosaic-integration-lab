# Rule-admission blueprint: catalogue desk

A small, copyable agent that uses the whole rule-admission mechanism: prose
declares which rules a host may check, the host registers the guards that check
them, and a floor in operator config says which checks prose may never drop.
The domain is an invented lending library; every record, title and fee is
synthetic.

> **Candidate status.** This blueprint needs Prosaic Core `9d5a02f` or later
> (enforcement tags) and the rule admission in Runtime from
> [prosaic-runtime#16](https://github.com/B3Cognition/prosaic-runtime/pull/16),
> which is still in review. Both are installed by the Lab from exact-commit
> candidate wheels until they are released. Interfaces can change before release.

## What is in the folder

| File | What it shows |
| --- | --- |
| `.prosaic/subagents/catalogue-desk.md` | The agent. Tags at `before_tool`, `before_answer` and `final`, plus one `prose-only` rule. |
| `.prosaic/subagents/loan-desk.md` | A companion file. It binds the same custom guard at `after_tool`. |
| `guards.py` | One custom domain guard, `loan_period_within_policy`, and `registry()`: the four generic Runtime guards plus that one. |
| `host.py` | Host wiring: synthetic tools, two-file composition, config loading and `build_runtime()`. |
| `runtime.yml` | Operator config: the endpoint and the `required_guards` floor in both forms. |
| `coverage.py` | Answers "which of this agent's rules are enforced, and by what?" |

The agent's rules, and what enforces each one:

| Rule (prose) | Guard | Stage | Action |
| --- | --- | --- | --- |
| Only place loans on records the search returned | `args_reference_seen_ids` (generic) | `before_tool` | `fail`, pinned by the floor |
| Never request a loan longer than 21 days | `loan_period_within_policy` (custom) | `before_tool` | `fix`: rewrite `days` to the limit |
| Plain Markdown links, never wrapped | `no_wrapped_links` (generic) | `before_answer` | `fix`: unwrap |
| State only fees the lookup returned | `value_in_tool_output` (generic) | `final` | `retry`; the floor's minimum |
| Be patient with first-time borrowers | none (`prose-only`) | n/a | left to the model, by design |
| Stop on a loan period the desk reports above policy (companion) | `loan_period_within_policy` (custom) | `after_tool` | `fail` |

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
- `superseded`: a same-stage binding of the same guard in another file has a
  stronger action and replaces this one.

It then reports whether admission accepts the agent, any cross-file binding
warnings and the rules fingerprint. The verdict comes from Runtime's own
admission, so it can't disagree with a real turn: the runtime is constructed,
then `prepare_turn` runs, which makes no provider request. The command exits
non-zero when admission refuses, including for a malformed tag or a required
guard the host did not register (`startup`).

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
`host.py`. Replace `library_tools()` with your own `CustomTool` registrations;
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
  second stage, put that rule in a companion file, as `loan-desk.md` does, and
  compose both files in the host (`host.compose`). Each binding keeps its own
  file, so the companion's rule is reported and fingerprinted separately.
  `compose` refuses a file listed twice and a companion with bundled resources,
  rather than composing it silently or partially.
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
```

The agent is refused with `invalidPolicy`, before any request, if it:

- omits a required guard;
- binds one with a weaker action;
- changes a pinned stage;
- adds or changes pinned settings.

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

## Limits

- Rule hooks run in conversation turns only (`ProsaicRuntime.turn`). `run()`,
  `NativeRuntime` and `UnifiedRuntime` refuse enforce-tagged prose instead of
  running it unenforced.
- Do not run this agent inside Harness yet. Harness 0.9.7 and earlier reject the
  `ruleViolation` failure code after the provider call has been made. Wait for a
  Harness release that accepts it.
- An agent with every tag stripped runs byte-identically to the tagged one when
  no guard fires, with or without guards registered. It is still refused by a
  runtime whose floor requires guards.
