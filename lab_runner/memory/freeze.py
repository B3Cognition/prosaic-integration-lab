"""Two content-addressed freeze stages; local provenance, not time attestation."""
import hashlib
from importlib.resources import files
from lab_runner.quality.contracts import digest
from .execution import PROSE


def development_manifest(corpus,historical_sources):
    source={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in files(__package__).iterdir() if p.name.endswith('.py')}
    source['data/evidence-summary.schema.json']=hashlib.sha256(files(__package__).joinpath('data/evidence-summary.schema.json').read_bytes()).hexdigest()
    source['../retrieval_memory.py']=hashlib.sha256(files('lab_runner').joinpath('retrieval_memory.py').read_bytes()).hexdigest()
    common={name:hashlib.sha256(files('lab_runner.quality').joinpath(name).read_bytes()).hexdigest()
        for name in ('contracts.py','checks.py','execution.py','scoring.py','allowance.py','runner.py','suite.py',
                     'token_admission.py','sdk_provenance.py','data/sdk-provenance-public.json',
                     'data/sdk-provenance-pre-unified.json',
                     'data/sdk-provenance.json','data/answer.schema.json')}
    common.update({'../memory_policy/'+p.name:hashlib.sha256(p.read_bytes()).hexdigest()
        for p in files('lab_runner.memory_policy').iterdir() if p.name.endswith('.py')})
    return dict(version=1,implementation=source,qualityDependencies=common,proseDigest=digest(PROSE),
                corpusDigest=digest(corpus),historicalSourcesDigest=digest(historical_sources))


def evaluation_manifest(suite,development):
    return dict(version=1,suiteDigest=digest(suite),developmentFreezeDigest=digest(development))


def verify(bundle,development,evaluation):
    if development!=development_manifest(bundle['corpus'],bundle['historicalSources']):
        raise ValueError('development freeze drift')
    suite={k:bundle[k] for k in ('version','suiteId','cases')}
    if evaluation!=evaluation_manifest(suite,development):raise ValueError('evaluation freeze drift')
