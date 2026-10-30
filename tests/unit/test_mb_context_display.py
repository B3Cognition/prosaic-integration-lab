"""Real renderer checks for exact source-body quotation boundaries."""
import hashlib
from lab_runner.memory_benchmark.budget_views import EvidenceBudget

def sha(s):return hashlib.sha256(s.encode()).hexdigest()

def test_memory_search_source_spans_exclude_metadata_and_preserve_unicode():
    text='Že\r\nÁ🙂'
    out=EvidenceBudget().render_memory_search('query',[dict(selectionId='r',recordId='r',path='metadata-forgery',preview=text)])
    assert len(out['bodySpans'])==1
    span=out['bodySpans'][0]
    assert out['display'][span['start']:span['end']]==text
    assert span['recordId']=='r'
    assert 'metadata-forgery' not in out['display'][span['start']:span['end']]

def test_manual_context_body_spans_exclude_wrappers():
    source='Ž\r\nÁ🙂\r\n'
    out=EvidenceBudget().render_window('scope metadata',source,'file.md',1)
    span=out['bodySpans'][0]
    assert out['display'][span['start']:span['end']]==source
    assert out['display'][span['start']:span['end']].encode()==source.encode()

def record(rid,text,source='s',role='seed',offset=0):
    return dict(recordId=rid,textSha256=sha(text),text=text,path=source+'.md',
        sourceId=source,sourceFileSha256=sha(source),wing='notes',revision='v1',
        namespace='owner',contextRole=role,startChar=offset,endChar=offset+len(text),startLine=1,endLine=2)

def test_document_context_labels_related_source_and_produces_exact_spans():
    records=[record('r2','main text',offset=20),record('r0','introduction',role='sourceIntroduction'),
             record('t0','related text','other','relatedIntroduction')]
    out=EvidenceBudget().render_document_context('bounded document context','r2',records)
    assert out['retainedIds']==['r0','r2','t0']
    assert 'sourceId="s"' in out['display'] and 'sourceId="other"' in out['display']
    assert 'relatedIntroduction' in out['display']
    texts={r['recordId']:r['text'] for r in records}
    for span in out['bodySpans']:
        assert out['display'][span['start']:span['end']]==texts[span['recordId']]
    assert out['bytes']==len(out['display'].encode())<=5120

def test_document_context_drops_whole_low_priority_records_under_shared_cap():
    records=[record('seed','Ž'*300),record('related','Q'*700,'other','relatedIntroduction')]
    budget=EvidenceBudget(1400)
    out=budget.render_document_context('bounded','seed',records)
    assert out['retainedIds']==['seed']
    assert out['omitted'] and 'Q'*10 not in out['display']
    assert out['bytes']<=1400 and budget.used==out['bytes']

def test_empty_search_produces_no_quotable_source_span():
    out=EvidenceBudget().render_memory_search('no hits',[])
    assert out['bodySpans']==[]

def test_manual_search_quotes_exact_source_bytes_not_json_escapes():
    preview='Quoted "Ž" at C:\\fixture\r\nwith Á🙂'
    out=EvidenceBudget().render_search('query',[dict(path='f.md',count=1)],
        [dict(selectionId='a',path='f.md',line=1,preview=preview)])
    span=out['bodySpans'][0]
    assert out['display'][span['start']:span['end']].encode()==preview.encode()
