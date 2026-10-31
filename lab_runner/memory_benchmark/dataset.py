"""Explicit source import and immutable dataset snapshots; gold remains separate."""
import os
from pathlib import Path, PurePosixPath

from .storage import code_binding, encoded, exclusive, identifier, read, require, sha, shape
from .retrieval_policy import LEGACY_POLICY, BALANCED_POLICY, keywords, validate_policy
from . import execution

MAX_SOURCE_BYTES = 4_194_304
MAX_CORPUS_BYTES = 67_108_864


def _source(root, relative):
    require(type(relative) is str and '\\' not in relative and ':' not in relative,
            'portable relative source path required')
    parts = PurePosixPath(relative).parts
    require(parts and not PurePosixPath(relative).is_absolute() and '..' not in parts,
            'source path escape')
    path = root.joinpath(*parts)
    require(not any(p.is_symlink() for p in (path, *path.parents)), 'source symlink denied')
    require(path.is_file() and path.resolve().is_relative_to(root), 'source outside root')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, 'rb') as stream:
        raw = stream.read(MAX_SOURCE_BYTES+1)
    require(0 < len(raw) <= MAX_SOURCE_BYTES, 'source byte limit')
    try: raw.decode('utf-8')
    except UnicodeError as error: raise ValueError('source must be UTF-8') from error
    return raw


def _cases(cases, sources):
    require(type(cases) is list and 1 <= len(cases) <= 1000, 'case count must be 1..1000')
    ids = set()
    for case in cases:
        shape(case, ('id','question','queries','sourceIds'))
        identifier(case['id']); require(case['id'] not in ids, 'duplicate case'); ids.add(case['id'])
        require(type(case['question']) is str and 0 < len(case['question'].encode()) <= 4096, 'question limit')
        require(type(case['queries']) is list and 1 <= len(case['queries']) <= 3
            and all(type(q) is str and q.strip() and '\n' not in q and '\r' not in q
                    and len(q.encode()) <= 256 for q in case['queries']), 'query bounds')
        grants=case['sourceIds']
        require(type(grants) is list and grants and len(grants)==len(set(grants))
            and set(grants) <= set(sources), 'case source grant')


def validate_key(key, bundle, texts):
    shape(key, ('version','cases')); require(type(key['version']) is int and key['version']==1, 'key version')
    require(type(key['cases']) is list and len(key['cases'])==len(bundle['cases']), 'key case denominator')
    cases={c['id']:c for c in bundle['cases']}; seen=set()
    for item in key['cases']:
        shape(item, ('id','expectedAbstention','facets'))
        require(item['id'] in cases and item['id'] not in seen, 'key identity'); seen.add(item['id'])
        require(type(item['expectedAbstention']) is bool and type(item['facets']) is list
                and 1 <= len(item['facets']) <= 32, 'key facet bounds')
        facets=set()
        for facet in item['facets']:
            shape(facet, ('id','description','sources')); identifier(facet['id'])
            require(facet['id'] not in facets, 'duplicate facet'); facets.add(facet['id'])
            require(type(facet['description']) is str and 0<len(facet['description'].encode())<=4096,
                    'facet description')
            require(type(facet['sources']) is list and len(facet['sources'])<=16
                and (facet['sources'] or item['expectedAbstention']), 'facet supporting sources required')
            for quote in facet['sources']:
                shape(quote, ('sourceId','start','end','quote')); sid=quote['sourceId']
                require(sid in cases[item['id']]['sourceIds'], 'key source outside case grant')
                text=texts[sid]
                require(type(quote['start']) is int and type(quote['end']) is int
                    and 0<=quote['start']<quote['end']<=len(text)
                    and text[quote['start']:quote['end']]==quote['quote'], 'key quote mismatch')
    return key


def freeze(dataset_path, policy_path, output, *, key_path=None, castle_map_path=None, retrieval_policy=LEGACY_POLICY,
           generation_profile='canonical-v1', execution_profile=execution.LEGACY):
    from .generation import validate_profile, LEGACY
    validate_profile(generation_profile)
    execution.limits(execution_profile)
    validate_policy(retrieval_policy)
    data=read(dataset_path); policy=read(policy_path)
    shape(data, ('version','sources','cases')); shape(policy, ('version','namespace','root','allowedWings'))
    require(type(data['version']) is int and data['version']==1
        and type(policy['version']) is int and policy['version']==1, 'dataset/policy version')
    identifier(policy['namespace']); wings=policy['allowedWings']
    require(type(wings) is list and wings and len(set(wings))==len(wings), 'trusted wing grants')
    for wing in wings: identifier(wing)
    root=Path(policy['root']); require(root.is_absolute() and root.is_dir()
        and not any(p.is_symlink() for p in (root,*root.parents)), 'trusted absolute source root')
    require(type(data['sources']) is list and 1<=len(data['sources'])<=5000, 'source count')
    sources={}; payloads={}; total=0
    for source in data['sources']:
        shape(source, ('id','path','wing')); sid=identifier(source['id'])
        require(sid not in sources and source['wing'] in wings, 'duplicate source or wing outside host grant')
        raw=_source(root,source['path']); total+=len(raw)
        require(total<=MAX_CORPUS_BYTES, 'corpus byte ceiling')
        sources[sid]=dict(source, sha256=sha(raw), bytes=len(raw), frozenPath=f'sources/{sid}.md')
        payloads[sid]=raw
    _cases(data['cases'],sources)
    if retrieval_policy == BALANCED_POLICY:
        for case in data['cases']:
            for query in case['queries']:
                keywords(query)
    public=dict(version=1,namespace=policy['namespace'],allowedWings=wings,
                sources=sources,cases=data['cases'],code=code_binding(),
                castleMap=None if castle_map_path is None else read(castle_map_path))
    if retrieval_policy != LEGACY_POLICY:
        public['retrievalPolicy'] = retrieval_policy
    if generation_profile != LEGACY:
        public['generationProfile'] = generation_profile
    if execution_profile != execution.LEGACY:
        public['executionProfile'] = execution_profile
    # Validate an operator map against the selected source bytes before creating output.
    if castle_map_path is not None:
        from .retrieval import catalog_for
        projected=dict(public,sources={sid:dict(s,frozenPath=s['path']) for sid,s in sources.items()})
        catalog_for(root,projected)
    require(len(encoded(public))<=16_777_216, 'frozen manifest byte limit')
    key=None if key_path is None else validate_key(read(key_path),public,{k:v.decode('utf-8') for k,v in payloads.items()})
    binding=dict(publicSha256=sha(public),keySha256=None if key is None else sha(key))
    output=Path(output)
    require(output.is_absolute() and not output.exists()
        and not any(p.is_symlink() for p in output.parents), 'fresh absolute freeze directory required')
    output.mkdir(mode=0o700,parents=True)
    for sid,raw in payloads.items():
        path=output/sources[sid]['frozenPath'];path.parent.mkdir(mode=0o700,exist_ok=True)
        fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o400)
        with os.fdopen(fd,'wb') as stream:stream.write(raw)
    exclusive(output/'dataset.json',public)
    if key is not None:exclusive(output/'grading/key.json',key)
    exclusive(output/'freeze.json',binding)
    return dict(caseCount=len(data['cases']),sourceCount=len(sources),binding=sha(binding),
                semanticQuality='unmeasured',keyPresent=key is not None)


def load_frozen(directory):
    from .generation import validate_profile, LEGACY
    directory=Path(directory); binding=read(directory/'freeze.json'); data=read(directory/'dataset.json')
    shape(binding, ('publicSha256','keySha256'))
    require(sha(data)==binding['publicSha256'], 'frozen dataset digest mismatch')
    require(data['code']==code_binding(), 'benchmark code differs from frozen version')
    validate_policy(data.get('retrievalPolicy', LEGACY_POLICY))
    validate_profile(data.get('generationProfile', LEGACY))
    execution.limits(data.get('executionProfile',execution.LEGACY))
    for sid,source in data['sources'].items():
        require(source['frozenPath']==f'sources/{identifier(sid)}.md', 'frozen path identity')
        raw=_source(directory,source['frozenPath'])
        require(len(raw)==source['bytes'] and sha(raw)==source['sha256'], 'frozen source mismatch')
    return data


def load_key(directory):
    directory=Path(directory); data=load_frozen(directory); binding=read(directory/'freeze.json')
    if binding['keySha256'] is None:return None
    key=read(directory/'grading/key.json')
    require(sha(key)==binding['keySha256'], 'frozen key mismatch')
    texts={sid:_source(directory,s['frozenPath']).decode('utf-8') for sid,s in data['sources'].items()}
    return validate_key(key,data,texts)
