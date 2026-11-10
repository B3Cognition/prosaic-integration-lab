from copy import deepcopy
import pytest
from prosaic_integration_lab.parallel_tools import TRAIN,CASES



def test_parallel_candidate_keeps_all_existing_lanes():
    from lab_runner.gates import ALL_COUNTS,supports_parallel_tools,required_modes,TOOL_EVIDENCE_TRAIN
    assert len(CASES)==16 and ALL_COUNTS['parallel-tools']==32
    old={'artifacts':[dict(distribution=k,version=v) for k,v in TOOL_EVIDENCE_TRAIN.items()]}
    assert not supports_parallel_tools(old) and len(required_modes(candidate=False,manifest=old))==11
    assert sum(ALL_COUNTS[m] for m in required_modes(candidate=False,manifest=old))==364
    # Conversation context assembly adds six cases: 370 old / 402 new.
    with pytest.raises(ValueError):supports_parallel_tools({'artifacts':[dict(distribution=k,version=v) for k,v in TRAIN.items()]})


def paired_manifest():
    pins={'b3-prosaic':'e858a853595746c6930fbe062e84bd8ece1a366aa3b126f2fe11bfb7cb2ceb81','b3-prosaic-runtime-postgres':'5f29ce5b0a1cb3ce4ee41f44c50e322b5b1af73cbe186ecadc428f81ccc7b5ca'}
    artifacts=[dict(distribution=k,version=v,filename=k.replace('-','_')+'-'+v+'-py3-none-any.whl',source_commit='a'*40,sha256=pins.get(k,'b'*64)) for k,v in TRAIN.items()]
    paired=[]
    for sdk,names in [('runtime',{'b3-prosaic-runtime'}),('harness',{'b3-prosaic-harness','b3-prosaic-harness-postgres'})]:
        chosen=[a for a in artifacts if a['distribution'] in names]
        receipt=dict(source_commit='a'*40,distributions=[dict(name=a['distribution'],version=a['version']) for a in chosen],artifacts=[dict(filename=a['filename'],sha256=a['sha256']) for a in chosen])
        qualification=dict(source_commit='a'*40,artifacts=receipt['artifacts'],label='parallel-tool-consumer',exit_code=0,command=['python','-I','-m','pytest','tests/test_parallel_tool_installed.py'],result_counts=dict(tests=8,failures=0,errors=0,skipped=0))
        paired.append(dict(sdk=sdk,receipt=receipt,qualification=qualification))
    paired[1].update(runtime_receipt=deepcopy(paired[0]['receipt']),runtime_qualification=deepcopy(paired[0]['qualification']))
    return dict(artifacts=artifacts,candidate_lineage=dict(version=1,kind='local-parallel-tool-handoff',candidates=paired,retained_artifacts=[a for a in artifacts if a['distribution'] in pins]))


def test_exact_parallel_family_adds_32_without_losing_any_case():
    from lab_runner.gates import required_modes,ALL_COUNTS,supports_parallel_tools,expected_test_count
    manifest=paired_manifest();assert supports_parallel_tools(manifest)
    modes=required_modes(candidate=True,manifest=manifest)
    assert len(modes)==12 and sum(expected_test_count(m,True) for m in modes)==402


@pytest.mark.parametrize('damage',['source','hash','upstream','recorder','skip','missing','mixed'])
def test_corrupt_or_incomplete_parallel_family_fails_closed(damage):
    from lab_runner.gates import supports_parallel_tools
    d=paired_manifest();line=d['candidate_lineage']['candidates']
    if damage=='source':line[0]['receipt']['source_commit']='c'*40
    elif damage=='hash':d['artifacts'][0]['sha256']='c'*64
    elif damage=='upstream':line[1]['runtime_receipt']['source_commit']='c'*40
    elif damage=='recorder':next(a for a in d['artifacts'] if a['distribution']=='b3-prosaic-runtime-postgres')['sha256']='c'*64
    elif damage=='skip':
        line[0]['qualification']['result_counts']['skipped']=1
        line[1]['runtime_qualification']['result_counts']['skipped']=1
    elif damage=='missing':d['candidate_lineage'].pop('candidates')
    else:d['artifacts'][1]['version']='0.9.20'
    with pytest.raises(ValueError):supports_parallel_tools(d)
