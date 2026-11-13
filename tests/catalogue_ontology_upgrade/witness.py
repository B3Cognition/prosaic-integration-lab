"""Persist on the published SDK and recover through public candidate APIs."""
import argparse
import hashlib
from importlib.metadata import version
import json
from pathlib import Path

import prosaic_harness as harness
import prosaic_runtime as runtime
from prosaic_harness_postgres import PostgresRunStore
from prosaic_runtime.accounting import MemoryRecorder


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False).encode()).hexdigest()


def run(phase, directory, config, backend):
    candidate = phase == 'resume'
    assert version('b3-prosaic') == ('0.5.1' if candidate else '0.5.0')
    assert version('b3-prosaic-harness') == ('0.9.18' if candidate else '0.9.17')
    assert version('b3-prosaic-runtime') == '0.9.23'
    assert version('b3-prosaic-harness-postgres') == '0.4.5'
    calls = []

    def read(arguments):
        calls.append(arguments)
        assert not candidate
        return {'candidate': 'synthetic'}

    options = {}
    if candidate:
        from prosaic.ontology import validate_ontology
        options['ontology'] = validate_ontology({
            'schemaVersion': 1, 'ontologyId': 'upgrade-fixture', 'concepts': {'candidate': 'Release candidate.'},
            'relations': [], 'agents': {}, 'tools': {'read_receipt': ['candidate']},
        })
    schema = {'type': 'object', 'additionalProperties': False,
              'properties': {'candidate': {'type': 'string'}}, 'required': ['candidate']}
    tool = runtime.CustomTool('read_receipt', 'Read fixture receipt',
        {'type': 'object', 'additionalProperties': False}, read, 'v1')
    settings = runtime.RuntimeConfig(
        {'fixture': runtime.EndpointConfig('http://127.0.0.1:1/v1', 'synthetic')}, {}, 'fixture',
        allowed_tools=frozenset({'read_receipt'}))
    factory = harness.WorkflowFactory(catalog=harness.WorkflowCatalog(schemas={'result': schema}, **options),
        bindings=harness.WorkflowBindings(config=settings, custom_tools={'read_receipt': tool}),
        policy=harness.WorkflowPolicy(allowed_schemas={'result'}, allowed_tools={'read_receipt'},
            allowed_direct_tools={'read_receipt'}, max_provider_requests_per_invocation=0,
            max_tool_calls_per_invocation=1))
    bundle = harness.WorkflowBundle('ontology-upgrade', factory)
    proposal = json.dumps({'definition': {'version': 1, 'start': 'read', 'steps': {
        'read': {'kind': 'tool', 'tool': 'read_receipt', 'schema': 'result', 'arguments': {},
                 'next': 'review'},
        'review': {'kind': 'pause', 'question': 'Accept the synthetic receipt?',
                   'choices': {'accept': 'done'}, 'requires': ['read']},
        'done': {'kind': 'finish', 'requires': ['read']},
    }}})
    evidence = directory / f'{backend}-upgrade.json'
    if candidate:
        saved = json.loads(evidence.read_text())
        workflow = bundle.reconstruct(saved['proposal'], harness.WorkflowReference.from_dict(saved['reference']))
        assert factory.describe(include_ontology=True)['ontology']['tools'] == {'read_receipt': ['candidate']}
    else:
        prepared = bundle.prepare_json(proposal)
        workflow = prepared.workflow
    if backend == 'postgres':
        store = PostgresRunStore(config['harness_dsn'], namespace=config['namespace'])
        store.check_ready()
    else:
        store = harness.FileRunStore(directory / 'runs', namespace='ontology-upgrade')
        if not candidate:
            store.initialize()
    context = runtime.ExecutionContext(application_id='fixture', tenant_id='tenant', actor_id='actor',
                                       billing_account_id='payer')
    recorder = MemoryRecorder(provider_id='openai-compatible')
    try:
        run_id = 'b' * 32 if backend == 'postgres' else 'a' * 32
        controller = harness.Harness(workflow, store=store, run_id=run_id, context=context, accounting=recorder)
        if not candidate:
            checkpoint = controller.run({})
            assert checkpoint['current'] == 'review' and calls == [{}]
            before = controller.recovery_evidence()
            evidence.write_text(json.dumps({
                'proposal': prepared.proposal_json, 'reference': prepared.reference.to_dict(),
                'identity': bundle.identity, 'evidence_sha256': digest(before),
            }))
        else:
            assert bundle.identity == saved['identity']
            before = controller.recovery_evidence()
            assert digest(before) == saved['evidence_sha256']
            assert controller.resume() == before['checkpoint']
            completed = controller.resume(choice='accept', expected_revision=before['revision'],
                                          decision_id='c' * 32)
            assert completed['status'] == 'completed' and completed['outputs']['read'] == {'candidate': 'synthetic'}
            assert controller.recovery_evidence()['receipts'] == before['receipts']
            assert calls == []
    finally:
        store.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=('save', 'resume'))
    parser.add_argument('directory', type=Path)
    parser.add_argument('--config', type=Path)
    args = parser.parse_args()
    config = json.loads(args.config.read_text()) if args.config is not None else None
    run(args.phase, args.directory, config, 'file')
    if config is not None:
        run(args.phase, args.directory, config, 'postgres')
