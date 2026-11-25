"""Copy installed examples out of the package and execute real public SDK calls."""
from dataclasses import replace
import json
from pathlib import Path
import runpy
import sys

import pytest
from lab_runner.rule_admission.fixtures import scripted_provider


def copied(tmp_path, name):
    import os
    import lab_runner
    if os.environ.get('PROSAIC_BLUEPRINT_INSTALLED') == '1':
        assert Path(lab_runner.__file__).resolve().is_relative_to(Path(sys.prefix).resolve())
        assert 'site-packages' in Path(lab_runner.__file__).resolve().parts
    package = Path(lab_runner.__file__).parent / 'blueprints'
    assert (package / '__init__.py').is_file(), 'copyable feature blueprints must be shipped'
    from lab_runner.blueprints import copy_blueprint
    return copy_blueprint(name, tmp_path / name)


@pytest.fixture(autouse=True)
def loopback_only(monkeypatch):
    monkeypatch.setenv('NO_PROXY', '*')
    monkeypatch.setenv('no_proxy', '*')


@pytest.mark.parametrize('entry', ['run', 'turn', 'prepared'])
def test_uncached_blueprint_changes_headers_without_prompt_or_identity_changes(tmp_path, entry):
    project = copied(tmp_path, 'request-headers')
    host = runpy.run_path(str(project / 'host.py'))
    with scripted_provider() as provider:
        runtime = host['build_runtime'](project=project, base_url=provider.url)
        artifact = host['load_agent'](project)
        digest = artifact.digest
        provider.queue_text('synthetic answer'); provider.queue_text('synthetic answer')
        if entry == 'run':
            result = host['run_benchmark'](runtime, artifact, arguments='same synthetic question')
            runtime.run(artifact, 'same synthetic question')
        elif entry == 'turn':
            result = host['turn_benchmark'](runtime, artifact, message='same synthetic question').result
            runtime.turn(artifact, message='same synthetic question')
        else:
            prepared = runtime.prepare_turn(artifact, message='same synthetic question')
            result = host['turn_benchmark'](runtime, prepared).result
            runtime.turn(prepared)
        assert result.exit_code == 0 and artifact.digest == digest
        assert len(provider.raw_requests) == 2
        assert provider.raw_requests[0] == provider.raw_requests[1]
        assert provider.captured_headers[0]['x-tokenproxy-no-cache'] == '1'
        assert 'x-tokenproxy-no-cache' not in provider.captured_headers[1]
        assert 'tokenproxy' not in json.dumps(provider.requests) + json.dumps(result.metadata)


def test_uncached_headers_follow_the_actual_tool_continuation(tmp_path):
    import yaml
    from prosaic_runtime import CustomTool, RunPolicy
    project = copied(tmp_path, 'request-headers');host = runpy.run_path(str(project / 'host.py'))
    calls = []
    tool = CustomTool('lookup', 'Read one synthetic record', {'type': 'object', 'additionalProperties': False},
                      lambda args: calls.append(args) or {'value': 7}, 'lookup-v1')
    config = yaml.safe_load((project / 'runtime.yml').read_text())
    config['allowed_tools'] = ['lookup']  # Separate operator grant; registration alone grants nothing.
    (project / 'runtime.yml').write_text(yaml.safe_dump(config))
    with scripted_provider() as provider:
        runtime = host['build_runtime'](project=project, base_url=provider.url, custom_tools={'lookup': tool})
        artifact = host['load_agent'](project)
        artifact = replace(artifact, frontmatter={**artifact.frontmatter, 'tools': ['lookup']})
        provider.queue_calls(('lookup-1', 'lookup', {}));provider.queue_text('value 7')
        result = host['turn_benchmark'](runtime, artifact, message='Read the record.',
            policy=RunPolicy(allowed_tools=frozenset({'lookup'}), max_provider_requests=2, max_tool_calls=1))
        assert result.result.exit_code == 0 and calls == [{}]
        assert [h['x-tokenproxy-no-cache'] for h in provider.captured_headers] == ['1', '1']
        assert len(provider.raw_requests) == 2


def test_header_blueprint_refuses_unsupported_provider_before_dispatch(tmp_path):
    project = copied(tmp_path, 'request-headers');host = runpy.run_path(str(project / 'host.py'))
    with scripted_provider('anthropic') as provider:
        runtime = host['build_runtime'](project=project, base_url=provider.url)
        config = runtime.config;name = config.default_profile
        from prosaic_runtime import ProsaicRuntime
        runtime = ProsaicRuntime(replace(config, profiles={name: replace(config.profiles[name], provider='anthropic')}))
        with pytest.raises(ValueError):host['turn_benchmark'](runtime, host['load_agent'](project), message='hello')
        assert provider.raw_requests == []


def test_header_example_requires_opt_in_and_prints_the_actual_result(tmp_path):
    import subprocess
    import yaml
    project = copied(tmp_path, 'request-headers')
    with scripted_provider() as provider:
        config = yaml.safe_load((project / 'runtime.yml').read_text())
        config['profiles']['local']['base_url'] = provider.url
        (project / 'runtime.yml').write_text(yaml.safe_dump(config))
        args = [sys.executable, '-I', str(project / 'host.py')]
        refused = subprocess.run(args, cwd=tmp_path, capture_output=True, text=True, timeout=30)
        assert refused.returncode == 2 and provider.requests == []
        provider.queue_text('synthetic answer')
        completed = subprocess.run([*args, '--live'], cwd=tmp_path, capture_output=True, text=True, timeout=30)
        assert completed.returncode == 0, completed.stderr
        assert completed.stdout.strip() == 'synthetic answer' and len(provider.requests) == 1


ORIGINAL = {'insights': [{'id': 'A', 'text': 'first'}, {'id': 'B', 'text': 'second'}, {'id': 'C', 'text': 'untouched'}]}
REVISED = {'insights': [{'id': 'A', 'text': 'first'}, {'id': 'B', 'text': 'edited'}, {'id': 'C', 'text': 'untouched'}, {'id': 'D', 'text': 'new'}]}


def workflow(project, provider):
    import yaml
    from prosaic_harness import Workflow
    config = yaml.safe_load((project / 'runtime.yml').read_text())
    config['profiles']['local']['base_url'] = provider.url
    (project / 'runtime.yml').write_text(yaml.safe_dump(config))
    return Workflow.load(project / 'workflow.yml', executable=str(Path(sys.executable).with_name('prosaic')))


def first_two(provider, revision=REVISED):
    provider.queue_text(json.dumps({'findings': [{'insight_id': 'A', 'text': 'flagged'}]}))
    provider.queue_text(json.dumps(revision))


@pytest.mark.parametrize('target', ['A', 'B', 'D'])
def test_revision_validator_uses_both_accepted_outputs_and_replays_without_http(tmp_path, target):
    from prosaic_harness import Harness
    project = copied(tmp_path, 'revision-review');checks = runpy.run_path(str(project / 'checks.py'))
    with scripted_provider() as provider:
        graph = workflow(project, provider);registry = checks['validators']();first_two(provider)
        provider.queue_text(json.dumps({'findings': [{'insight_id': target, 'text': 'admitted'}]}))
        controller = Harness(graph, tmp_path / 'run', validators=registry)
        state = controller.run(ORIGINAL)
        assert state['status'] == 'waiting' and len(provider.requests) == 3
        assert state['outputs']['revised_review']['findings'][0]['insight_id'] == target
        wire = json.dumps(provider.requests[-1])
        assert 'first_review' in wire and 'revision' in wire
        assert controller.resume(choice='accept')['status'] == 'completed'
        assert Harness(graph, tmp_path / 'run', validators=registry).resume()['status'] == 'completed'
        assert len(provider.requests) == 3


def test_revision_validator_repairs_one_unrelated_finding_within_four_calls(tmp_path):
    from prosaic_harness import Harness
    project = copied(tmp_path, 'revision-review');checks = runpy.run_path(str(project / 'checks.py'))
    with scripted_provider() as provider:
        graph = workflow(project, provider);first_two(provider)
        provider.queue_text(json.dumps({'findings': [{'insight_id': 'C', 'text': 'unrelated'}]}))
        provider.queue_text(json.dumps({'findings': [{'insight_id': 'B', 'text': 'changed'}]}))
        state = Harness(graph, tmp_path / 'run', validators=checks['validators']()).run(ORIGINAL)
        assert state['status'] == 'waiting' and len(provider.requests) == 4
        assert state['outputs']['revised_review']['findings'][0]['insight_id'] == 'B'
        assert 'previously flagged' in json.dumps(provider.requests[-1])


@pytest.mark.parametrize('target', ['C', 'invented'])
def test_unrelated_finding_exhausts_bounded_attempts_without_acceptance(tmp_path, target):
    from prosaic_harness import Harness
    project = copied(tmp_path, 'revision-review');checks = runpy.run_path(str(project / 'checks.py'))
    with scripted_provider() as provider:
        graph = workflow(project, provider);first_two(provider)
        for _ in range(2):provider.queue_text(json.dumps({'findings': [{'insight_id': target, 'text': 'unrelated'}]}))
        controller = Harness(graph, tmp_path / 'run', validators=checks['validators']())
        state = controller.run(ORIGINAL)
        assert state['status'] == 'blocked' and state['reason'] == 'attempt_limit'
        assert 'revised_review' not in state['outputs']
        controller.resume();assert len(provider.requests) == 4


def test_changed_copied_validator_refuses_saved_run_without_new_call(tmp_path):
    from prosaic_harness import Harness
    project = copied(tmp_path, 'revision-review');checks = runpy.run_path(str(project / 'checks.py'))
    with scripted_provider() as provider:
        graph = workflow(project, provider);first_two(provider);provider.queue_text('{"findings": []}')
        registry = checks['validators']();controller = Harness(graph, tmp_path / 'run', validators=registry)
        assert controller.run(ORIGINAL)['status'] == 'waiting'
        path = project / 'checks.py';path.write_text(path.read_text() + '\n# changed application policy\n')
        changed = runpy.run_path(str(path))['validators']()
        with pytest.raises(ValueError):Harness(graph, tmp_path / 'run', validators=changed).resume(choice='accept')
        assert len(provider.requests) == 3


@pytest.mark.parametrize('revision', [
    {'insights': [{'id': 'A', 'text': 'one'}, {'id': 'A', 'text': 'duplicate'}]},
    {'insights': [{'id': '', 'text': 'invalid'}]},
    {'insights': [{'id': 'B', 'text': 'edited'}], 'changed_ids': ['C']},
])
def test_malformed_revision_cannot_reach_the_revised_review(tmp_path, revision):
    from prosaic_harness import Harness
    project = copied(tmp_path, 'revision-review');checks = runpy.run_path(str(project / 'checks.py'))
    with scripted_provider() as provider:
        graph = workflow(project, provider);first_two(provider, revision)
        state = Harness(graph, tmp_path / 'run', validators=checks['validators']()).run(ORIGINAL)
        assert state['status'] == 'blocked' and 'revised_review' not in state['outputs']
        assert len(provider.requests) == 2


def test_removed_flagged_insight_is_not_authorized_by_the_old_review(tmp_path):
    from prosaic_harness import Harness
    project = copied(tmp_path, 'revision-review');checks = runpy.run_path(str(project / 'checks.py'))
    with scripted_provider() as provider:
        graph = workflow(project, provider);first_two(provider, {'insights': [{'id': 'B', 'text': 'edited'}]})
        for _ in range(2):provider.queue_text('{"findings": [{"insight_id":"A", "text":"removed"}]}')
        state = Harness(graph, tmp_path / 'run', validators=checks['validators']()).run(ORIGINAL)
        assert state['status'] == 'blocked' and 'revised_review' not in state['outputs']
        assert len(provider.requests) == 4


def test_replaced_first_review_makes_the_earlier_revision_stale(tmp_path):
    import yaml
    from prosaic_harness import Harness
    project = copied(tmp_path, 'revision-review');checks = runpy.run_path(str(project / 'checks.py'))
    with scripted_provider() as provider:
        workflow(project, provider)
        path = project / 'workflow.yml';document = yaml.safe_load(path.read_text())
        document['limits'].update(max_calls=5, max_visits=2)
        document['steps']['first_review'].update(next='route', max_visits=2)
        document['steps']['revision']['next'] = 'first_review'
        document['steps']['route'] = {'kind':'gate', 'from':'first_review', 'field':['repeat'], 'equals':True,
            'pass':'revised_review', 'fail':'revision', 'max_visits':2}
        schema_path = project / 'schemas/review.json';schema = json.loads(schema_path.read_text())
        schema['properties']['repeat'] = {'type':'boolean'};schema_path.write_text(json.dumps(schema))
        path.write_text(yaml.safe_dump(document));graph = workflow(project, provider)
        provider.queue_text('{"findings": [{"insight_id":"A", "text":"flagged"}], "repeat":false}')
        provider.queue_text(json.dumps(REVISED))
        provider.queue_text('{"findings": [], "repeat":true}')
        state = Harness(graph, tmp_path / 'run', validators=checks['validators']()).run(ORIGINAL)
        assert state['status'] == 'blocked' and state['reason'] == 'stale_artifact'
        assert 'revised_review' not in state['outputs'] and len(provider.requests) == 3


def test_revision_runner_works_from_an_isolated_copied_directory(tmp_path, monkeypatch):
    import subprocess
    project = copied(tmp_path, 'revision-review')
    with scripted_provider() as provider:
        workflow(project, provider);first_two(provider);provider.queue_text('{"findings": []}')
        request = tmp_path / 'request.json';request.write_text(json.dumps(ORIGINAL))
        # An explicit Python invocation must use its installed Core CLI, not ambient PATH.
        monkeypatch.setenv('PATH', str(tmp_path / 'no-ambient-executables'))
        args = [sys.executable, '-I', str(project / 'run.py'), '--run-dir', str(tmp_path / 'run'), '--request', str(request)]
        refused = subprocess.run(args, cwd=tmp_path, capture_output=True, text=True, timeout=30)
        assert refused.returncode == 2 and provider.requests == [], refused.stderr
        result = subprocess.run([*args, '--live'], cwd=tmp_path, capture_output=True, text=True, timeout=30)
        assert result.returncode == 0, result.stderr
        assert json.loads(result.stdout)['status'] == 'waiting' and len(provider.requests) == 3


@pytest.mark.parametrize('run_cap,allowed', [(2048, False), (8192, True)])
def test_cap_blueprint_exposes_the_limit_that_enforces_growing_history(tmp_path, run_cap, allowed):
    from prosaic_harness import Conversation, ConversationError, ConversationScope, FileSessionStore
    project = copied(tmp_path, 'conversation-caps');host = runpy.run_path(str(project / 'host.py'))
    with scripted_provider() as provider:
        bindings = host['build_bindings'](project=project, base_url=provider.url, max_input_bytes=8192,
            run_max_input_bytes=run_cap, interpretation_max_input_bytes=4096)
        assert host['limits'](bindings) == {'ordinary': run_cap, 'interpretation': 4096}
        scope = ConversationScope('caps', 'synthetic', 'app', 'tenant', 'actor')
        store = FileSessionStore(tmp_path / 'sessions', namespace=scope.namespace);store.initialize()
        try:
            controller = Conversation(bindings, store=store, scope=scope);session = controller.create()
            provider.queue_text('a' * 900)
            first = controller.send(session.session_id, message_id='first', message='u' * 800, expected_revision=session.revision).document
            assert first['status'] == 'completed'
            revision = store.load_session(session.session_id, scope=scope).revision
            provider.queue_text('second')
            if allowed:
                assert controller.send(session.session_id, message_id='second', message='u' * 800, expected_revision=revision).document['status'] == 'completed'
                assert len(provider.requests) == 2
            else:
                with pytest.raises(ConversationError):controller.send(session.session_id, message_id='second', message='u' * 800, expected_revision=revision)
                assert len(provider.requests) == 1
        finally:store.close()


def test_copy_never_overwrites_a_consumer_directory(tmp_path):
    copied(tmp_path, 'request-headers')
    from lab_runner.blueprints import copy_blueprint
    sentinel = tmp_path / 'request-headers/private.txt';sentinel.write_text('retain')
    with pytest.raises(FileExistsError):copy_blueprint('request-headers', sentinel.parent)
    assert sentinel.read_text() == 'retain'
    with pytest.raises(ValueError):copy_blueprint('../other', tmp_path / 'other')


@pytest.mark.parametrize('wire', ['openai-compatible', 'anthropic'])
@pytest.mark.parametrize('fee', ['1.20 EUR', '1.20 euros', '120 cents'])
def test_fee_blueprint_refuses_invented_suffix_fees_on_both_wires(tmp_path, wire, fee):
    from lab_runner.rule_admission.blueprint import host
    project = copied(tmp_path, 'rule-admission')
    with scripted_provider(wire) as provider:
        config = host.load_config(project / 'runtime.yml', base_url=provider.url);name = config.default_profile
        config = replace(config, profiles={**config.profiles, name: replace(config.profiles[name], provider=wire)})
        runtime = host.build_runtime(config, project=project)
        provider.queue_calls(('fee', 'loan_terms', {'recordId':'CAT-0001'}))
        provider.queue_text('The fee is ' + fee + ' per day.')
        provider.queue_text('The fee is EUR 0.40 per day.')
        turn = runtime.turn(host.compose(project), message='What is the fee for CAT-0001?', policy=host.policy())
        assert turn.result.exit_code == 0 and turn.rules_violated == ('subagents/catalogue-desk.md:12:value_in_tool_output',)
        assert len(provider.requests) == 3 and turn.result.stdout == 'The fee is EUR 0.40 per day.'


def test_cap_example_prints_limits_without_contacting_the_endpoint(tmp_path):
    import subprocess
    import yaml
    project = copied(tmp_path, 'conversation-caps')
    with scripted_provider() as provider:
        config = yaml.safe_load((project / 'runtime.yml').read_text())
        config['profiles']['local']['base_url'] = provider.url
        (project / 'runtime.yml').write_text(yaml.safe_dump(config))
        result = subprocess.run([sys.executable, '-I', str(project / 'host.py')], cwd=tmp_path,
            capture_output=True, text=True, timeout=30)
        assert result.returncode == 0, result.stderr
        assert json.loads(result.stdout) == {'ordinary':8192, 'interpretation':8192}
        assert provider.requests == []
