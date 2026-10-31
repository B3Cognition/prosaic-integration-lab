"""Scoped equal-display retrieval. No model, key access or implicit ingestion."""
from copy import deepcopy
import json
from pathlib import Path
import re
import subprocess
import time

from .budget_views import EvidenceBudget, source_heading, lf_lines
from .context_expansion import _provenance, fetch_window, validate_catalog
from .dataset import _source
from .document_context import _hit, fetch_document_context
from .primary_context import ValidatedFetchCache, plan_primary_context
from .storage import encoded, require, sha, shape
from .retrieval_policy import (LEGACY_POLICY, BALANCED_POLICY, keywords,
                               keyword_file_candidates, round_robin, validate_policy)

ARMS=('manual','strict','expanded')
CAPTURED='2000-01-01T00:00:00+00:00'


def catalog_for(root, bundle):
    records={};groups={};slices={};sources={}
    imported=bundle.get('castleMap')
    if imported is not None:
        shape(imported,('version','sources'))
        require(type(imported['version']) is int and imported['version']==1
            and type(imported['sources']) is list, 'Castle map version')
        mapped={entry['id']:entry for entry in imported['sources']}
        require(len(mapped)==len(imported['sources']) and set(mapped)==set(bundle['sources']), 'Castle map coverage')
    for sid,source in bundle['sources'].items():
        text=_source(Path(root),source['frozenPath']).decode('utf-8')
        require(sha(text.encode())==source['sha256'], 'source binding')
        if imported is None:
            source_id=sha([bundle['namespace'],sid,source['wing']]);revision='r1-'+source['sha256']
            captured=CAPTURED
            chunks=[dict(recordId=sha([source_id,start]),start=start,end=min(start+800,len(text)))
                    for start in range(0,len(text),800)]
        else:
            row=mapped[sid];shape(row,('id','sourceId','revision','capturedAt','records'))
            source_id,revision,captured,chunks=(row[k] for k in ('sourceId','revision','capturedAt','records'))
        require(source_id not in sources and type(chunks) is list and chunks, 'ambiguous mapped source')
        group=sha([source_id,revision,source['wing'],source['sha256']]);ids=[];end=0
        sources[source_id]=dict(path=f'exports/{sid}.md',sha256=source['sha256'],wing=source['wing'])
        for index,chunk in enumerate(chunks):
            require(type(chunk) is dict and set(chunk) in ({'recordId','start','end'},
                {'recordId','start','end','capturedAt'}), 'closed import record shape')
            require(type(chunk['start']) is int and type(chunk['end']) is int and chunk['start']==end
                and end<chunk['end']<=min(end+800,len(text)), 'exact contiguous import chunk required')
            rid=chunk['recordId'];body=text[end:chunk['end']]
            require(type(rid) is str and rid not in records, 'duplicate record')
            record=dict(recordId=rid,textSha256=sha(body.encode()),revision=revision,
                representation='project',wing=source['wing'],sourceId=source_id,chunkIndex=index,
                orderGroup=group,sourceFileSha256=source['sha256'],capturedAt=chunk.get('capturedAt',captured))
            records[rid]=record;ids.append(rid)
            slices[rid]=dict(schema_version=1,record_id=rid,text_sha256=record['textSha256'],
                slice_sha256=record['textSha256'],text=body,start_char=0,next_start_char=None,
                complete=True,provenance=_hit(record))
            # Host metadata only, derived from exact source code-point positions.
            record_location=dict(startChar=end,endChar=chunk['end'],startLine=text.count('\n',0,end)+1,
                endLine=text.count('\n',0,chunk['end'])+1)
            slices[rid]['_location']=record_location;end=chunk['end']
        require(end==len(text),'import coverage loss');groups[group]=ids
    catalog=dict(schemaVersion=1,namespace=bundle['namespace'],corpusSha256=sha(bundle['sources']),
        sourceCount=len(sources),recordCount=len(records),records=records,groups=groups)
    validate_catalog(catalog,namespace=bundle['namespace'],wings=bundle['allowedWings'])
    return catalog,slices,sources


def _snapshot(provider, ids, catalog, slices):
    ids=sorted(set(ids));require(len(ids)<=128,'snapshot record limit')
    if not ids:return None
    expected={rid:dict(text_sha256=catalog['records'][rid]['textSha256'],
                      revision=catalog['records'][rid]['revision']) for rid in ids}
    result=provider.snapshot(ids,expected=expected,maximum_bytes=262144)
    shape(result,('schema_version','sources','texts','digest'))
    require(type(result['schema_version']) is int and result['schema_version']==1
        and result['sources']==[slices[r]['provenance'] for r in ids]
        and result['texts']==[slices[r]['text'] for r in ids], 'snapshot exact source mismatch')
    # Castle's public wire digest uses MemorySource declaration order. Saved
    # evidence sorts JSON keys, so reconstruct that order from the independently
    # verified frozen provenance instead of trusting incoming mapping order.
    payload=dict(schema_version=1,sources=[slices[r]['provenance'] for r in ids],texts=[slices[r]['text'] for r in ids])
    wire=json.dumps(payload,ensure_ascii=False,allow_nan=False,separators=(',',':')).encode()
    require(result['digest'] in {sha(wire),sha(payload)} and len(encoded(result))<=262144,'snapshot digest/size')
    return result


class FixtureProvider:
    """Literal synthetic ranking only; never advertised as Castle FTS quality."""
    def __init__(self,catalog,slices,policy=LEGACY_POLICY):
        self.catalog=catalog;self.slices=slices;self.fetches=[];self.snapshots=0;self.policy=policy
    def health(self):return dict(status='ready',profile='memory-fts-v1',recency_boost=False)
    def search(self,query,limit=5):
        hits=[]
        for rid,value in self.slices.items():
            matched=(any(re.search(r'\b'+re.escape(t)+r'\b',value['text'],re.I) for t in keywords(query))
                     if self.policy==BALANCED_POLICY else query.casefold() in value['text'].casefold())
            if matched:
                hits.append(dict(value['provenance'],excerpt=value['text'][:800],rank=len(hits)+1,score=1.0))
                if len(hits)==limit:break
        return dict(schema_version=1,hits=hits)
    def fetch(self,rid,**kwargs):
        self.fetches.append(rid);value=deepcopy(self.slices[rid]);value.pop('_location');return value
    def snapshot(self,ids,**kwargs):
        self.snapshots+=1
        payload=dict(schema_version=1,sources=[self.slices[r]['provenance'] for r in ids],
                     texts=[self.slices[r]['text'] for r in ids])
        return dict(payload,digest=sha(payload))


def fixture_provider(root,bundle):
    catalog,slices,_=catalog_for(root,bundle)
    return FixtureProvider(catalog,slices,validate_policy(bundle.get('retrievalPolicy',LEGACY_POLICY)))


def prepare(root,bundle,case,arm,*,provider=None,search_replay=None):
    require(arm in ARMS,'unknown retrieval arm');started=time.monotonic()
    policy=validate_policy(bundle.get('retrievalPolicy',LEGACY_POLICY));balanced=policy==BALANCED_POLICY
    def remaining():
        value=300-(time.monotonic()-started)
        if value<=0:raise TimeoutError('retrieval task deadline')
        return value
    catalog,slices,sources=catalog_for(root,bundle)
    granted={sid:bundle['sources'][sid] for sid in case['sourceIds']}
    paths={f'exports/{sid}.md':s for sid,s in granted.items()}
    allowed_sids={r['sourceId'] for r in catalog['records'].values()
                  if sources[r['sourceId']]['path'] in paths}
    allowed_wings=sorted({s['wing'] for s in granted.values()})
    frames={};budget=EvidenceBudget(32768);selected=[];hits={};backing=[];plan=[]
    audit=[];visible_groups=[]
    def identity(record):
        return dict(namespace=bundle['namespace'],sourceId=record['sourceId'],
            sourceFileSha256=record['sourceFileSha256'],revision=record['revision'],wing=record['wing'],
            path=sources[record['sourceId']]['path'])
    def emit(rendered,kind,metadata,identities=None):
        remaining()
        spans=deepcopy(rendered.get('bodySpans',[]))
        if identities:
            for span in spans:span['sourceIdentity']=identities[span['path']]
        frames[f'visible-{len(frames)+1:03d}.json']=dict(kind=kind,display=rendered['display'],
            bodySpans=spans,metadata=metadata)
    if arm=='manual':
        texts={path:_source(Path(root),s['frozenPath']).decode('utf-8') for path,s in paths.items()}
        ordered=sorted(paths)
        for qi,query in enumerate(case['queries']):
            # stdin avoids ambiguous filename delimiters and shell/argv injection.
            previews=[];counts=[]
            if balanced:
                candidates,counts=keyword_file_candidates(texts,keywords(query),remaining)
                for index,candidate in enumerate(candidates):
                    sid=f'q{qi}-s{index}'
                    previews.append(dict(selectionId=sid,**{k:candidate[k] for k in ('path','line','preview')}))
                    hits[sid]={k:candidate[k] for k in ('path','line','anchorChar')}
            else:
                for path in ordered:
                    run=subprocess.run(['rg','-n','-i','-F','--',query],input=texts[path].encode(),
                        capture_output=True,timeout=min(10,remaining()))
                    remaining()
                    require(run.returncode in (0,1),'rg failed')
                    count=0
                    lines=lf_lines(texts[path])
                    for line in run.stdout.decode('utf-8').split('\n'):
                        if not line:continue
                        n,_,_=line.partition(':');number=int(n);line_text=lines[number-1]
                        match=re.search(re.escape(query),line_text,re.I);require(match is not None,'literal rg anchor')
                        anchor=sum(map(len,lines[:number-1]))+match.start()
                        sid=f'q{qi}-s{len(previews)}';count+=1
                        previews.append(dict(selectionId=sid,path=path,line=number,preview=line_text.rstrip('\r\n')[:160]))
                        hits[sid]=dict(path=path,line=number,anchorChar=anchor)
                    if count:counts.append(dict(path=path,count=count))
            frame=budget.render_search(f'query {qi+1}: {json.dumps(query)}',counts,previews)
            if balanced:
                visible=set(frame['visibleSelectionIds'])
                visible_groups.append([p['selectionId'] for p in previews if p['selectionId'] in visible])
            else:
                for sid in frame['visibleSelectionIds']:
                    if len(selected)<5:selected.append(sid)
            identities={p:identity(next(r for r in catalog['records'].values() if sources[r['sourceId']]['path']==p)) for p in ordered}
            emit(frame,'search',{},identities)
        if balanced:
            selected=round_robin(visible_groups,key=lambda sid:(hits[sid]['path'],hits[sid]['line']))
        for sid in selected:
            hit=hits[sid];path=hit['path'];source=paths[path]
            rendered=budget.render_window('literal file window',texts[path],path,hit['line'],anchorChar=hit['anchorChar'])
            if rendered['startChar'] is None:continue
            record=next(r for r in catalog['records'].values() if sources[r['sourceId']]['path']==path)
            meta=dict(path=path,sourceFileSha256=source['sha256'],sourceIdentity=identity(record),
                **{k:rendered[k] for k in ('startChar','endChar')},
                startLine=texts[path].count('\n',0,rendered['startChar'])+1,
                endLine=texts[path].count('\n',0,rendered['endChar'])+1)
            emit(rendered,'open',meta)
        status='not_used';snapshot=None
    else:
        require(search_replay is None or arm=='expanded' and type(search_replay) is list
            and len(search_replay)==len(case['queries']), 'search replay binding')
        try: health=provider.health();remaining()
        except Exception as error:
            if not isinstance(error,(OSError,TimeoutError)) and getattr(error,'code',None) not in ('unavailable','timeout'):
                raise
            return dict(frames={},memoryStatus='unavailable',sourceExpansion=False,elapsedSeconds=time.monotonic()-started,
                        selectedIds=[],snapshot=None,planning=[],audit=[])
        require(health.get('profile')=='memory-fts-v1' and health.get('recency_boost') is False,
                'raw FTS provider required')
        for qi,query in enumerate(case['queries']):
            effective=' '.join(keywords(query)) if balanced else query
            result=deepcopy(search_replay[qi]) if search_replay is not None else provider.search(effective,limit=5)
            remaining()
            audit.append(dict(op='search',result=result,replayed=search_replay is not None))
            require(type(result) is dict and result.get('schema_version')==1 and type(result.get('hits')) is list
                and len(result['hits'])<=5,'search shape')
            previews=[]
            for hit in result['hits']:
                rid=hit['record_id'];require(rid in catalog['records'],'unknown hit')
                record=catalog['records'][rid];require(record['sourceId'] in allowed_sids,'hit outside case scope')
                _provenance(hit,record);require(type(hit['excerpt']) is str and len(hit['excerpt'])<=800,'preview bounds')
                # Longer private audit excerpts never enter the public packet.
                preview=hit['excerpt'][:160];require(preview in slices[rid]['text'],'preview source mismatch')
                hits[rid]=hit
                previews.append(dict(selectionId=rid,path=sources[record['sourceId']]['path'],line=slices[rid]['_location']['startLine'],
                    recordId=rid,preview=preview,textSha256=record['textSha256'],sourceId=record['sourceId'],
                    sourceFileSha256=record['sourceFileSha256'],wing=record['wing'],revision=record['revision'],
                    namespace=bundle['namespace'],**slices[rid]['_location']))
            rendered=budget.render_memory_search(f'query {qi+1}: {json.dumps(query)}',previews)
            retained=rendered['visibleSelectionIds'];metadata={}
            visible_groups.append(list(retained))
            for rid in retained:
                if not balanced and rid not in selected and len(selected)<5:selected.append(rid)
                backing.append(rid);r=catalog['records'][rid]
                metadata[rid]=dict(sourceIdentity=identity(r),provenance=_hit(r),textSha256=r['textSha256'],revision=r['revision'],
                    preview=True,displayedTextSha256=sha(hits[rid]['excerpt'][:160].encode()),**slices[rid]['_location'])
            emit(rendered,'search',dict(records=metadata))
        if balanced:
            selected=round_robin(visible_groups)
        cache=ValidatedFetchCache(provider,catalog,bundle['namespace'],allowed_wings,catalog_wings=bundle['allowedWings'])
        scoped_sources={sid:s for sid,s in sources.items() if sid in allowed_sids}
        scoped_catalog=deepcopy(catalog)
        scoped_catalog['records']={rid:r for rid,r in catalog['records'].items() if r['sourceId'] in allowed_sids}
        scoped_catalog['groups']={g:ids for g,ids in catalog['groups'].items() if ids[0] in scoped_catalog['records']}
        scoped_catalog.update(sourceCount=len(scoped_sources),recordCount=len(scoped_catalog['records']))
        windows=[]
        for rid in selected:
            values=(fetch_document_context(cache,hits[rid],scoped_catalog,bundle['namespace'],allowed_wings,scoped_sources,
                    catalog_wings=bundle['allowedWings']) if arm=='expanded' else
                    fetch_window(cache,hits[rid],catalog,bundle['namespace'],allowed_wings,radius=0,catalog_wings=bundle['allowedWings']))
            rows=[]
            for value in values:
                record=catalog['records'][value['record_id']]
                rows.append(dict(record,text=value['text'],path=sources[record['sourceId']]['path'],namespace=bundle['namespace'],
                    contextRole=value.get('contextRole','seed'),**slices[value['record_id']]['_location']))
            windows.append(dict(seedId=rid,heading=source_heading(rows[0]),records=rows))
        plan=plan_primary_context(windows,limit=32768,used=budget.used) if arm=='expanded' else []
        for i,window in enumerate(windows):
            rendered=plan[i] if arm=='expanded' else budget.render_records(window['heading'],window['seedId'],window['records'])
            if arm=='expanded':budget.charge(rendered['display'])
            metadata={}
            for rid in rendered['retainedIds']:
                backing.append(rid);r=catalog['records'][rid]
                metadata[rid]=dict(sourceIdentity=identity(r),provenance=_hit(r),textSha256=r['textSha256'],revision=r['revision'],
                    preview=False,**slices[rid]['_location'])
            emit(rendered,'open',dict(records=metadata))
        snapshot=_snapshot(provider,backing,catalog,slices)
        remaining()
        status='available' if backing else 'empty'
    return dict(frames=frames,memoryStatus=status,sourceExpansion=arm=='expanded',elapsedSeconds=time.monotonic()-started,
                selectedIds=selected,snapshot=snapshot,planning=plan,audit=audit)


def validate_capture(root,bundle,case,capture):
    """Independent exact frozen-source verification, with no provider calls."""
    catalog,slices,sources=catalog_for(root,bundle)
    paths={f'exports/{sid}.md':source for sid,source in bundle['sources'].items() if sid in case['sourceIds']}
    require(sum(len(f['display'].encode()) for f in capture['frames'].values())<=32768,'display allowance exceeded')
    for frame in capture['frames'].values():
        for span in frame['bodySpans']:
            rid=span.get('recordId');meta=frame['metadata'];body=frame['display'][span['start']:span['end']]
            if rid is not None:
                require(rid in catalog['records'],'capture foreign record')
                record=catalog['records'][rid];source=sources[record['sourceId']];path=source['path']
                require(path in paths,'capture outside source grant')
                trusted=meta['records'][rid];_provenance(trusted['provenance'],record)
                identity=trusted['sourceIdentity'];expected=record['textSha256']
                require(trusted['textSha256']==expected and trusted['revision']==record['revision'],'capture record identity')
                require(body==slices[rid]['text'] if frame['kind']=='open' else 0<len(body)<=160 and body in slices[rid]['text'],
                    'capture source bytes')
                if frame['kind']=='open':
                    require(all(trusted[k]==v for k,v in slices[rid]['_location'].items()),'capture source offsets')
            else:
                identity=span.get('sourceIdentity',meta.get('sourceIdentity'));path=identity['path']
                require(path in paths,'manual source grant')
                source=paths[path];text=_source(Path(root),source['frozenPath']).decode('utf-8')
                if frame['kind']=='open':
                    require(type(meta.get('startChar')) is int and type(meta.get('endChar')) is int
                        and 0<=meta['startChar']<meta['endChar']<=len(text)
                        and body==text[meta['startChar']:meta['endChar']],'manual exact source window')
                else:require(body in text,'manual source preview')
                record=next(r for r in catalog['records'].values() if sources[r['sourceId']]['path']==path)
            require(identity==dict(namespace=bundle['namespace'],sourceId=record['sourceId'],sourceFileSha256=record['sourceFileSha256'],
                revision=record['revision'],wing=record['wing'],path=path),'capture trusted source identity')
    ids=sorted({span['recordId'] for f in capture['frames'].values() for span in f['bodySpans'] if 'recordId' in span})
    if ids:
        snapshot=capture['snapshot'];require(type(snapshot) is dict,'frozen snapshot required')
        class Saved:
            def snapshot(self,*a,**kw):return snapshot
        _snapshot(Saved(),ids,catalog,slices)
    return capture
