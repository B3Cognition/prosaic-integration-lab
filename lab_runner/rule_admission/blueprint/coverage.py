"""Which of this agent's rules are enforced, and by what? No model, no turn, no network.

    python -m lab_runner.rule_admission.blueprint.coverage [--project DIR] [--config FILE] [--json]

Reads Core's rules for the agent (the same ``rules`` that ``prosaic inspect
--json`` prints) and its companion rule files, and joins each rule to the guard
registry. The admitted/refused verdict comes from the same steps a turn takes:
constructing the runtime (``startup``), the host's own composition checks
(``hostPolicy``), then Runtime's ``prepare_turn``, which makes no provider
request. So this report can never disagree with what a turn would do.

Statuses: ``enforced``, ``unregistered``, ``prose-only``, or ``superseded`` (a
same-stage binding of the same guard and settings in another file with a
stronger action replaces it; different settings are refused by admission).
"""

import argparse
from dataclasses import replace
import json
from pathlib import Path
import sys
import warnings

from prosaic_runtime import RuleBindingWarning, TurnAdmissionError, compile_rules

from .guards import registry
from .host import AGENT, BLUEPRINT, COMPANIONS, build_runtime, compose, host_problems, load_config, policy

COLUMNS = ('id', 'status', 'guard', 'version', 'stage', 'action', 'floor')


def _floor(required, guard):
    spec = required.get(guard)
    return 'pinned' if isinstance(spec, dict) else spec


def _admission(project, config, guards, artifact):
    """Real admission: (refusal code or None, compiled rules or None, binding warnings)."""
    try:
        runtime = build_runtime(config, project=project, guards=guards)
    except ValueError:
        return 'startup', None, []  # e.g. a required guard the host did not register.
    if host_problems(artifact.rules or ()):
        return 'hostPolicy', None, []  # compose() refuses these before any turn.
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always', RuleBindingWarning)
        try:
            runtime.prepare_turn(artifact, message='coverage check', policy=policy())
        except TurnAdmissionError as error:
            return error.code, None, []
    notes = [str(item.message) for item in caught if issubclass(item.category, RuleBindingWarning)]
    # Same inputs admission used, including the project root for path settings.
    compiled = compile_rules(
        list(artifact.rules or ()),
        guards,
        required_guards=config.required_guards,
        project_root=project.resolve(),
        warn=False,
    )
    return None, compiled, notes


def report(project=BLUEPRINT, *, config_path=None, guards=None):
    project = Path(project)
    config = load_config(config_path or project / 'runtime.yml')
    guards = registry() if guards is None else list(guards)
    artifact = compose(project, check=False)  # Admission below reports host refusals as hostPolicy.
    # Coverage itself ignores the floor; admission applies it.
    official = build_runtime(replace(config, required_guards={}), project=project, guards=guards).rule_coverage(
        artifact
    )
    refusal, compiled, notes = _admission(project, config, guards, artifact)
    effective = {} if compiled is None else {binding.rule_id: binding.action for binding in compiled.bindings}
    versions = {guard.name: guard.version for guard in guards}
    status = {rule_id: 'enforced' for rule_id in official['registered']}
    status |= {rule_id: 'unregistered' for rule_id in official['unregistered']}
    status |= {rule_id: 'prose-only' for rule_id in official['proseOnly']}
    if compiled is not None:
        status |= {
            rule_id: 'superseded'
            for rule_id, value in status.items()
            if value == 'enforced' and rule_id not in effective
        }
    rows = [
        {
            'id': entry['id'],
            'guard': entry['guard'],
            'version': versions.get(entry['guard']),
            'stage': entry['stage'],
            'action': effective.get(entry['id'], entry['action']),
            'status': status[entry['id']],
            'floor': _floor(config.required_guards, entry['guard']),
        }
        for entry in artifact.rules or ()
    ]
    return {
        'files': [AGENT, *COMPANIONS],
        'rules': rows,
        'issues': official['issues'],
        'admitted': refusal is None,
        'refusal': refusal,
        'fingerprint': None if compiled is None else compiled.rules_fingerprint(),
        'warnings': notes,
    }


def table(data):
    widths = {
        column: max([len(column)] + [len(str(row[column] or '-')) for row in data['rules']]) for column in COLUMNS
    }
    lines = ['  '.join(column.upper().ljust(widths[column]) for column in COLUMNS)]
    lines += ['  '.join(str(row[column] or '-').ljust(widths[column]) for column in COLUMNS) for row in data['rules']]
    verdict = 'admitted' if data['admitted'] else f'refused ({data["refusal"]})'
    lines.append(
        f'{len(data["rules"])} rules, {data["issues"]} tag issues, {verdict}, fingerprint {data["fingerprint"] or "-"}'
    )
    return '\n'.join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--project', type=Path, default=BLUEPRINT, help='folder holding .prosaic/ and runtime.yml')
    parser.add_argument('--config', type=Path, help='runtime config (default: PROJECT/runtime.yml)')
    parser.add_argument('--json', action='store_true', help='print the report as JSON')
    args = parser.parse_args(argv)
    data = report(args.project, config_path=args.config)
    print(json.dumps(data, indent=2) if args.json else table(data))
    return 0 if data['admitted'] else 1


if __name__ == '__main__':
    sys.exit(main())
