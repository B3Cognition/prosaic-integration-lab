import hashlib
import json
from pathlib import Path


def test_frozen_legacy_slice_is_byte_exact_and_old_retrieval_is_still_required():
    from lab_runner.ship_eval.cases import load_suite
    from lab_runner.ship_eval.grader import grade
    from lab_runner.ship_eval.lookup import LookupSession
    root=Path(__file__).resolve().parents[2]
    lock=json.loads((root/'lab_runner/requirements_review_v1/legacy-v10-source-lock.json').read_text())
    assert lock['archiveSha256']=='f9c5aa8c2e5a8d8cad6685c38a61a506fc0d34c6317b5275b77e81d3715b190b'
    assert len(lock['files'])==6
    assert all(hashlib.sha256((root/name).read_bytes()).hexdigest()==sha for name,sha in lock['files'].items())
    cases,keys=load_suite()
    for case_id,case in cases.items():
        key=keys[case_id]
        response={'decision':key['decision'],'draftErrors':key['draftErrors'],
            'findings':[{'code':code,'citations':[{'recordId':r,'field':f} for r,f in alternatives[0]]}
                for code,alternatives in key['findings'].items()]}
        session=LookupSession(case)
        for record_id in case['records']:session.read(record_id)
        assert grade(case,key,response,session.trace())['passed']
        assert not grade(case,key,response,[])['passed']
