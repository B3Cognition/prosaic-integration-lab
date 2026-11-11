import json

from lab_runner.memory_benchmark.__main__ import main


def test_disabled_default_imports_no_worker_or_runtime(monkeypatch,capsys):
    assert main([])==0
    assert json.loads(capsys.readouterr().out)=={'enabled':False,'executed':False,'version':'memory-benchmark-v1'}


def test_template_freeze_200_cases_and_validate_are_offline(tmp_path,capsys):
    root=tmp_path/'example'
    assert main(['init','--directory',str(root),'--questions','200'])==0
    assert main(['validate','--dataset',str(root/'dataset.json'),'--policy',str(root/'policy.json')])==0
    frozen=tmp_path/'frozen'
    assert main(['freeze','--dataset',str(root/'dataset.json'),'--policy',str(root/'policy.json'),
                 '--output',str(frozen)])==0
    assert main(['validate','--frozen',str(frozen)])==0
    assert len(json.loads((frozen/'dataset.json').read_bytes())['cases'])==200


def test_live_requires_explicit_mode_and_configuration(tmp_path,capsys):
    assert main(['run','--frozen',str(tmp_path/'absent'),'--output',str(tmp_path/'run')])==2
    assert not (tmp_path/'run').exists()
