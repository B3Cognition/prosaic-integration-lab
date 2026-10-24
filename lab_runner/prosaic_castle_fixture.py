"""Explicit installed fork/adapter/SUE qualification. Disabled allocates nothing."""

import argparse
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import tempfile
from xml.etree import ElementTree

ENGINE_SHA256 = '7dfe0697de596e745b5934570d449238d28db380e5e800a96a606d01eed0bc4d'
WORKER_SHA256 = '3d8b1d9da57b9374ca8cdd6260c793cc105788ae242dc44116d294781eee1915'
ADAPTER_SHA256 = '7131c12e9b1bc36cb302874d7c5dbbd349de42d74581f8b5ec9c2981aabbbc35'


def required_test_names():
    common = ('test_actual_castle_snapshot_survives_changed_source_and_cross_process_resume',
        'test_unavailable_optional_continues_required_blocks_before_run',
        'test_disabled_default_creates_no_castle_and_keeps_explicit_status',
        'test_cli_freezes_exact_utf8_and_resumes_with_owned_usage_after_source_deletion',
        'test_rejection_and_disabled_start_dispatch_nothing',
        'test_unknown_usage_never_enters_accepted_history_or_authorizes_retry',
        'test_absent_engine_fails_before_any_dispatch',
        'test_concurrent_cli_decisions_accept_once_without_extra_calls_or_usage',
        'test_saved_receipt_is_adopted_after_process_loss_without_repeating_call')
    names = {f'{name}[{store}]' for name in common for store in ('file','postgres')}
    names.update(('test_process_loss_before_receipt_remains_unknown_without_redispatch[file]',
                  'test_disabled_qualification_allocates_no_database_or_engine'))
    names.update(f'test_actual_frozen_castle_hackathon_case_survives_source_removal[{store}-{strategy}-requirements-{n:02}]'
        for store in ('file','postgres') for strategy in ('direct','critic_author','sue') for n in range(1,9))
    names.update(f'test_installed_optional_job_owner_freeze_usage_and_replay[{store}-{kind}]'
        for store in ('file','postgres') for kind in ('judge','entity_refinement','corpus_origin'))
    names.update(f'test_installed_invalid_judge_preserves_original_order_without_retry[{store}]'
        for store in ('file','postgres'))
    return names


def complete_test_inventory(xml):
    names = [case.get('name') for case in xml.iter('testcase')]
    return len(names) == len(set(names)) and set(names) == required_test_names()


def sanitize_fixture_log(text, dsn):
    # Pytest may truncate a fixture repr in the middle of its password, so an
    # exact full-DSN replacement alone is insufficient on a failing test.
    text = text.replace(dsn,'[fixture-dsn]')
    return re.sub(r"password=[^\s,'\"<)]+",'password=[redacted]',text)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--enable',action='store_true')
    parser.add_argument('--postgres-version',type=int,choices=(16,18),default=16)
    for name in ('lab-wheel','engine-wheel','adapter-wheel','worker-wheel','worker-python','tests-root','output'):
        parser.add_argument('--'+name,type=Path)
    args = parser.parse_args(argv)
    if not args.enable:
        print(json.dumps(dict(enabled=False,qualified=False,reason='disabled')))
        return 0
    if any(getattr(args,name.replace('-','_')) is None for name in
           ('lab-wheel','engine-wheel','adapter-wheel','worker-wheel','worker-python','tests-root','output')):
        parser.error('enabled qualification requires all artifact, worker, test and output paths')
    if args.output.exists():
        parser.error('output must be a new evidence directory')
    from .sue_review_fixture import verify_installed_wheel
    from .memory_fixture import OwnedPostgres

    result = dict(enabled=True,qualified=False,profile='prosaic-castle-v1',synthetic_only=True,
                  consumer_platform=platform.system(),consumer_architecture=platform.machine())
    fixture = None
    try:
        import hashlib
        if hashlib.sha256(args.worker_wheel.read_bytes()).hexdigest() != WORKER_SHA256:
            raise ValueError('worker candidate checksum mismatch')
        result['artifacts'] = [
            verify_installed_wheel(args.lab_wheel,'prosaic-integration-lab',('prosaic_integration_lab/','lab_runner/')),
            verify_installed_wheel(args.engine_wheel,'cognitive-castle-sue',('castle_sue/',),expected_sha=ENGINE_SHA256),
            verify_installed_wheel(args.adapter_wheel,'b3-prosaic-memory-castle',('prosaic_memory_castle/',),expected_sha=ADAPTER_SHA256),
        ]
        # Worker verification runs with its own isolated interpreter, never an editable checkout.
        probe = subprocess.run([str(args.worker_python),'-I','-c',
            'import importlib.metadata as m,importlib.util,json;'
            'print(json.dumps({"worker":m.version("prosaic-castle"),"forbidden":'
            '{n:importlib.util.find_spec(n) is not None for n in '
            '("torch","sentence_transformers","spacy","sml")}}))'],
            capture_output=True,text=True,check=True,timeout=30)
        result['worker_environment'] = json.loads(probe.stdout)
        if any(result['worker_environment']['forbidden'].values()):
            raise ValueError('qualification needs a genuinely lean worker installation')
        # Reuse the audited byte verification helper in the worker environment.
        verify = '''import hashlib,importlib.metadata,json,sys,zipfile
p=sys.argv[1];d=importlib.metadata.distribution('prosaic-castle')
with zipfile.ZipFile(p) as z:
 names=[n for n in z.namelist() if n.startswith(('cognitive_castle/','prosaic_castle/')) and not n.endswith('/')]
 assert names
 for n in names: assert d.locate_file(n).read_bytes()==z.read(n)
print(json.dumps({'distribution':d.metadata['Name'],'version':d.version,'sha256':hashlib.sha256(open(p,'rb').read()).hexdigest()}))
'''
        check = subprocess.run([str(args.worker_python),'-I','-c',verify,str(args.worker_wheel)],
                               capture_output=True,text=True,check=True,timeout=30)
        result['artifacts'].append(json.loads(check.stdout))
        args.output.mkdir(parents=True,exist_ok=False)
        fixture = OwnedPostgres(args.postgres_version)
        with fixture, tempfile.TemporaryDirectory(prefix='prosaic-castle-acceptance-') as temporary:
            architecture = {'arm64':'arm64','aarch64':'arm64','x86_64':'amd64','AMD64':'amd64'}.get(platform.machine())
            if fixture.manifest['architecture'] != architecture or fixture.manifest['server_version'].split('.')[0] != str(args.postgres_version):
                raise ValueError('PostgreSQL architecture/version mismatch')
            configuration = Path(temporary)/'fixture.json'
            configuration.write_text(json.dumps(dict(dsn=fixture.dsn,worker_python=str(args.worker_python),
                evidence_directory=str(args.output/'cases'))))
            configuration.chmod(0o600)
            junit = args.output/'result.xml'
            tests = args.tests_root.resolve(strict=True)
            environment = {key:value for key,value in os.environ.items() if not key.startswith('PYTEST_')}
            environment.update(PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',LAB_MEMORY_FIXTURE=str(configuration),
                               LAB_SUE_FIXTURE=str(configuration))
            run = subprocess.run([sys.executable,'-I','-m','pytest',
                str(tests/'acceptance/test_memory_workflow.py'),str(tests/'acceptance/test_sue_review_workflow.py'),
                str(tests/'prosaic_castle'),'-c',os.devnull,'--rootdir',temporary,'--confcutdir',temporary,
                '--import-mode=importlib','-o','pythonpath=','-o','addopts=','-q','--junitxml',str(junit)],cwd=temporary,
                env=environment,
                capture_output=True,text=True,timeout=600)
            # These tests use only synthetic data; retain stdout/stderr without fixture DSN.
            (args.output/'pytest.log').write_text(sanitize_fixture_log(run.stdout+run.stderr,fixture.dsn))
            if junit.exists():
                junit.write_text(sanitize_fixture_log(junit.read_text(),fixture.dsn))
                suites = ElementTree.parse(junit).getroot()
                for key in ('tests','skipped','failures','errors'):
                    result[key] = sum(int(s.get(key,'0')) for s in suites.iter('testsuite'))
                result['complete_inventory'] = complete_test_inventory(suites)
            result['qualified'] = (run.returncode == 0 and result.get('tests') == 76 and result.get('skipped') == 0
                                   and result.get('complete_inventory') is True)
    except (OSError,ValueError,RuntimeError,subprocess.SubprocessError) as error:
        result['reason'] = type(error).__name__
    finally:
        if fixture is not None:
            result['postgres'] = fixture.manifest
            result['qualified'] = result['qualified'] and fixture.manifest['cleanup_verified']
        args.output.mkdir(parents=True,exist_ok=True)
        (args.output/'qualification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))
    return 0 if result['qualified'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
