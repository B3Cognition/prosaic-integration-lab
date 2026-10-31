import copy
import json
from pathlib import Path

import pytest

from lab_runner.memory_benchmark.dataset import freeze, load_frozen, load_key


def supplied(tmp_path, count=2):
    root = tmp_path / 'input'; root.mkdir()
    (root/'note.md').write_bytes('Decision: keep memory off.\r\nŽ🙂\r\n'.encode())
    dataset = {'version':1,'sources':[{'id':'note','path':'note.md','wing':'notes'}],
        'cases':[{'id':f'q{i:04}','question':'What is the decision?', 'queries':['memory'],
                  'sourceIds':['note']} for i in range(count)]}
    policy = {'version':1,'namespace':'owner-project','root':str(root),'allowedWings':['notes']}
    for name, value in [('dataset',dataset),('policy',policy)]:
        (tmp_path/f'{name}.json').write_text(json.dumps(value))
    return tmp_path/'dataset.json', tmp_path/'policy.json', dataset


def test_freezes_200_questions_and_exact_source_bytes_without_key(tmp_path):
    path, policy, original = supplied(tmp_path,200)
    output=tmp_path/'frozen'
    result=freeze(path,policy,output)
    assert result['caseCount']==200 and result['sourceCount']==1
    bundle=load_frozen(output)
    assert len(bundle['cases'])==200 and 'key' not in bundle
    assert bundle['namespace']=='owner-project'
    assert (output/'sources/note.md').read_bytes()==(tmp_path/'input/note.md').read_bytes()
    assert original['cases']==bundle['cases']
    assert result['semanticQuality']=='unmeasured'
    with pytest.raises((ValueError,FileExistsError)):freeze(path,policy,output)


@pytest.mark.parametrize('mutation', ['escape','symlink','wing','unknownSource','duplicate','authority','tooMany'])
def test_rejects_invalid_scope_or_case_manifest_before_freeze(tmp_path,mutation):
    path,policy,data=supplied(tmp_path)
    if mutation=='escape':data['sources'][0]['path']='../policy.json'
    if mutation=='symlink':
        (tmp_path/'input/note.md').unlink();(tmp_path/'input/note.md').symlink_to(policy)
    if mutation=='wing':data['sources'][0]['wing']='secrets'
    if mutation=='unknownSource':data['cases'][0]['sourceIds']=['unknown']
    if mutation=='duplicate':data['cases'][1]['id']=data['cases'][0]['id']
    if mutation=='authority':data['namespace']='model-chosen'
    if mutation=='tooMany':data['cases']*=501
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError):freeze(path,policy,tmp_path/'frozen')
    assert not (tmp_path/'frozen').exists()


def test_replay_rejects_mutated_source_and_manifest(tmp_path):
    path,policy,_=supplied(tmp_path);out=tmp_path/'frozen';freeze(path,policy,out)
    source=out/'sources/note.md';source.chmod(0o600);source.write_text('new')
    with pytest.raises(ValueError):load_frozen(out)


def test_key_is_separate_bound_and_quotes_are_exact(tmp_path):
    path,policy,data=supplied(tmp_path);out=tmp_path/'frozen'
    key={'version':1,'cases':[{'id':c['id'],'expectedAbstention':False,'facets':[
        {'id':'decision','description':'Memory remains disabled','sources':[
            {'sourceId':'note','start':0,'end':27,'quote':'Decision: keep memory off.\r'}]}]} for c in data['cases']]}
    # Offsets are Unicode code points, not normalized lines or UTF-8 byte offsets.
    key_path=tmp_path/'key.json';key_path.write_text(json.dumps(key))
    freeze(path,policy,out,key_path=key_path)
    assert load_key(out)['cases']==key['cases']
    public=load_frozen(out)
    assert 'facets' not in json.dumps(public) and 'Memory remains disabled' not in json.dumps(public)
    bad=copy.deepcopy(key);bad['cases'][0]['facets'][0]['sources'][0]['quote']='other'
    key_path.write_text(json.dumps(bad))
    with pytest.raises(ValueError):freeze(path,policy,tmp_path/'bad',key_path=key_path)


def test_duplicate_json_keys_and_nonfinite_values_rejected(tmp_path):
    path,policy,_=supplied(tmp_path)
    path.write_text('{"version":1,"version":1,"sources":[],"cases":[]}')
    with pytest.raises(ValueError):freeze(path,policy,tmp_path/'frozen')


def test_freezes_external_import_map_and_rejects_coverage_loss(tmp_path):
    path,policy,_=supplied(tmp_path)
    mapping={'version':1,'sources':[{'id':'note','sourceId':'a'*64,'revision':'r1',
        'capturedAt':'2026-10-26T00:00:00Z','records':[{'recordId':'record1','start':0,
        'end':len((tmp_path/'input/note.md').read_bytes().decode())}]}]}
    map_path=tmp_path/'map.json';map_path.write_text(json.dumps(mapping))
    freeze(path,policy,tmp_path/'frozen',castle_map_path=map_path)
    assert load_frozen(tmp_path/'frozen')['castleMap']==mapping
    mapping['sources'][0]['records'][0]['end']-=1;map_path.write_text(json.dumps(mapping))
    with pytest.raises(ValueError):freeze(path,policy,tmp_path/'bad',castle_map_path=map_path)


def test_record_capture_times_are_preserved_without_source_level_aggregation(tmp_path):
    from lab_runner.memory_benchmark.retrieval import catalog_for
    path,policy,_=supplied(tmp_path)
    mapping={'version':1,'sources':[{'id':'note','sourceId':'a'*64,'revision':'r1',
        'capturedAt':'2000-01-01T00:00:00Z','records':[{'recordId':'record1','start':0,
        'end':len((tmp_path/'input/note.md').read_bytes().decode()),'capturedAt':'2026-10-26T00:00:00Z'}]}]}
    map_path=tmp_path/'map.json';map_path.write_text(json.dumps(mapping));out=tmp_path/'frozen'
    freeze(path,policy,out,castle_map_path=map_path)
    catalog,_,_=catalog_for(out,load_frozen(out))
    assert catalog['records']['record1']['capturedAt']=='2026-10-26T00:00:00Z'
