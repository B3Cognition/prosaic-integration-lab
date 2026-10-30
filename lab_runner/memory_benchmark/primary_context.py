"""Private pure primary-evidence reservation and scoped exact-slice caching.

Planning reads verified identities, offsets and UTF-8 sizes only. It never
receives questions, queries, keys, prior answers or source-reading interfaces.
"""
from copy import deepcopy

from .budget_views import EvidenceBudget, document_frame
from .context_expansion import fetch_window, WINGS
from .document_context import _hit


class ValidatedFetchCache:
    """One open invocation; cache only fully validated provider slices."""
    def __init__(self, provider, catalog, namespace, allowed_wings, *, catalog_wings=WINGS):
        self.provider=provider;self.catalog=catalog;self.namespace=namespace
        self.allowed_wings=allowed_wings;self.cache={}
        self.catalog_wings=catalog_wings

    def fetch(self, record_id, start_char=0, max_chars=800):
        if type(start_char) is not int or start_char!=0 or type(max_chars) is not int or max_chars!=800:
            raise ValueError('unsupported cached slice')
        if record_id not in self.cache:
            if len(self.cache)>=40:
                raise ValueError('unique fetch cap exceeded')
            record=self.catalog['records'][record_id]
            values=fetch_window(self.provider,_hit(record),self.catalog,self.namespace,
                self.allowed_wings,radius=0,catalog_wings=self.catalog_wings)
            self.cache[record_id]=deepcopy(values[0])
        return deepcopy(self.cache[record_id])


def plan_primary_context(windows, limit=32768, used=0, per_open=5120, seen_ids=()):
    """Preserve the original radius-only floor before allocating extras.

    Each window contains seedId, exact legacy heading, and <=8 verified rich
    records in the unchanged document-candidate priority. Returned frames are
    uncharged plans; the caller must atomically charge each exact display.
    """
    baseline_budget=EvidenceBudget(limit,used)
    if type(per_open) is not int or not 0<=per_open<=5120 or len(windows)>5:
        raise ValueError('invalid primary context bounds')
    baselines=[]
    for window in windows:
        records=window['records'];ids=[r['recordId'] for r in records]
        if not records or len(records)>8 or len(set(ids))!=len(ids) or ids[0]!=window['seedId']:
            raise ValueError('invalid primary context candidates')
        seed=records[0]
        local=sorted((r for r in records if r['sourceId']==seed['sourceId']
            and abs(r['chunkIndex']-seed['chunkIndex'])<=2),key=lambda r:r['chunkIndex'])
        baselines.append(baseline_budget.render_records(window['heading'],window['seedId'],local,per_open))

    def floor(window, baseline, seen):
        seed=window['seedId'];by_id={r['recordId']:r for r in window['records']}
        ids=[rid for rid in baseline['retainedIds'] if rid==seed or rid not in seen]
        if not ids:
            # A baseline without a seed has no body credit to spend on extras.
            return dict(baseline),ids
        rows=[by_id[rid] for rid in ids]
        result=document_frame(window['heading'],window['records'][0],rows,
            baseline['omitted'] or len(ids)!=len(baseline['retainedIds']))
        if result['bytes']>baseline['bytes']:
            raise ValueError('primary floor exceeds original cost')
        return result,ids

    # Reserve every future mandatory frame before any optional body is added.
    seen=set(seen_ids);floors=[]
    for window,baseline in zip(windows,baselines):
        result,ids=floor(window,baseline,seen);floors.append(result)
        seen.update(ids)
    remaining=limit-used;seen=set(seen_ids);frames=[]
    for index,(window,baseline) in enumerate(zip(windows,baselines)):
        result,mandatory=floor(window,baseline,seen)
        future=sum(f['bytes'] for f in floors[index+1:])
        cap=min(per_open,remaining-future)
        if result['bytes']>cap:
            raise ValueError('reserved primary floor does not fit')
        mandatory_bytes=result['bytes'];selected=set(mandatory);extras=[]
        if mandatory:
            for record in window['records']:
                rid=record['recordId']
                if rid in selected or rid in seen:
                    continue
                trial_selected=selected|{rid}
                trial=document_frame(window['heading'],window['records'][0],
                    [r for r in window['records'] if r['recordId'] in trial_selected],
                    len(trial_selected)!=len(window['records']))
                if trial['bytes']<=cap:
                    result=trial;selected=trial_selected;extras.append(rid)
        result.update(baselineRetainedIds=baseline['retainedIds'],mandatoryIds=mandatory,
            extraIds=extras,baselineBytes=baseline['bytes'],mandatoryBytes=mandatory_bytes,
            futureReservedBytes=future,planningUsedBytes=used,planningLimit=limit)
        frames.append(result);remaining-=result['bytes'];seen.update(result['retainedIds'])
    if not set().union(*(set(b['retainedIds']) for b in baselines))<=seen:
        raise ValueError('primary evidence floor lost')
    return frames
