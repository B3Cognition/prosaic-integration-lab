from dataclasses import replace
import socket
from pathlib import Path
import tempfile

import pytest
from prosaic_runtime import CliSandboxConfig,EndpointConfig,RuntimeConfig,RunPolicy


def setup(tmp_path):
    root=tmp_path/'workspace';root.mkdir(mode=0o700)
    (root/'evidence').mkdir();(root/'evidence/input').write_text('synthetic')
    config=RuntimeConfig({'fixture':EndpointConfig('http://127.0.0.1:1/v1','synthetic',max_tokens=512)},
        {},'fixture',allowed_tools=frozenset({'probe'}),cli_sandbox=CliSandboxConfig('required'))
    policy=RunPolicy(allowed_tools=frozenset({'probe'}),read_roots=('evidence',),timeout_s=600,
        max_provider_requests=4,max_tool_calls=2,max_reported_tokens=8192)
    return root,config,policy,dict(name='probe',timeout_s=2,max_output_bytes=4096,pass_env=[])


def admit(root,config,policy,manifest,controls=None):
    from lab_runner.sandboxed_tools import admit_sandbox
    return admit_sandbox(config,policy,workspace=root,manifest=manifest,
        required_controls=['filesystem','network','credentials','timeout','output','same_group_cleanup'] if controls is None else controls)


def test_narrow_required_plan_is_admitted_without_execution(tmp_path):
    assert admit(*setup(tmp_path))==dict(version=1,admitted=True,reason='ready',unsupportedControls=[])


@pytest.mark.parametrize('control',['cpu','memory','process_count','detached_cleanup'])
def test_unsupported_control_is_explicitly_refused(tmp_path,control):
    assert admit(*setup(tmp_path),controls=[control])==dict(version=1,admitted=False,
        reason='unsupported_controls',unsupportedControls=[control])


@pytest.mark.parametrize('controls',[[],['unknown'],['network','network'],[True],'network'])
def test_unknown_or_ambiguous_requirements_cannot_downgrade(tmp_path,controls):
    with pytest.raises(ValueError):admit(*setup(tmp_path),controls=controls)


def test_off_mode_and_runtime_root_expansion_are_refused(tmp_path):
    root,config,policy,manifest=setup(tmp_path)
    assert not admit(root,replace(config,cli_sandbox=CliSandboxConfig('off')),policy,manifest)['admitted']
    assert not admit(root,replace(config,cli_sandbox=CliSandboxConfig('required',('/tmp',))),policy,manifest)['admitted']


@pytest.mark.parametrize('roots',[('/',),('../',),('.',),('missing',)])
def test_broad_escaping_or_missing_evidence_grants_are_refused(tmp_path,roots):
    root,config,policy,manifest=setup(tmp_path)
    assert not admit(root,config,replace(policy,read_roots=roots),manifest)['admitted']


def test_socket_and_socket_alias_in_read_grants_are_refused(tmp_path):
    with tempfile.TemporaryDirectory(prefix='sbx-',dir=Path('/tmp').resolve()) as short:
        base=Path(short);root,config,policy,manifest=setup(base)
        with socket.socket(socket.AF_UNIX) as listener:
            listener.bind(str(root/'evidence/socket'))
            assert not admit(root,config,policy,manifest)['admitted']
        (root/'evidence/socket').unlink()
        with socket.socket(socket.AF_UNIX) as listener:
            listener.bind(str(base/'outside.sock'))
            (root/'evidence/alias').symlink_to(base/'outside.sock')
            assert not admit(root,config,policy,manifest)['admitted']


@pytest.mark.parametrize('change',[dict(pass_env=['SYNTHETIC_SECRET']),dict(timeout_s=601),
    dict(timeout_s=True),dict(max_output_bytes=1_000_000),dict(max_output_bytes=True)])
def test_manifest_secrets_and_unbounded_outputs_are_refused(tmp_path,change):
    root,config,policy,manifest=setup(tmp_path)
    assert not admit(root,config,policy,manifest|change)['admitted']


def test_unbounded_invocation_and_extra_tool_grants_are_refused(tmp_path):
    root,config,policy,manifest=setup(tmp_path)
    assert not admit(root,config,replace(policy,max_provider_requests=None),manifest)['admitted']
    assert not admit(root,replace(config,allowed_tools=frozenset({'probe','other'})),policy,manifest)['admitted']
