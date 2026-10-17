"""Opt-in host scope and immutable planning provenance for native memory runs."""
from importlib.resources import files
from lab_runner.quality.contracts import decode,encode,digest,identifier,sha
from lab_runner.memory.context import current_index,current_sources
from lab_runner.memory.corpus import timestamp
from .scoped import ScopedCorpus,topics
from .assembly import assemble_context


def implementation():
    return {p.name:digest(p.read_text(encoding='utf-8')) for p in files(__package__).iterdir() if p.name.endswith('.py')}


class ScopedContext:
    def __init__(self,corpus,*,counter_descriptor,quote_inputs,quote_identity,limits,output_tokens,
                 continuation_budget=False):
        from prosaic_runtime import TokenCounterDescriptor
        from lab_runner.memory.execution import LIMITS
        if type(corpus) is not ScopedCorpus or not callable(quote_inputs):raise ValueError('trusted scoped policy required')
        if limits!=LIMITS or type(output_tokens) is not int or output_tokens!=512:raise ValueError('unchanged memory caps required')
        if type(continuation_budget) is not bool:raise ValueError('invalid continuation policy')
        self._continuation_budget=continuation_budget
        self.corpus=corpus;self.quote_inputs=quote_inputs;self._quote_identity=sha(quote_identity)
        self._descriptor=TokenCounterDescriptor.from_dict(counter_descriptor).to_dict()
        self._limits=decode(encode(limits));self._output=output_tokens

    @property
    def counter_descriptor(self):return decode(encode(self._descriptor))

    def identity(self,case):
        for key in ('tenantId','entity','caseId'):identifier(case[key])
        timestamp(case['asOf']);trusted_topics=topics(case['topics'])
        scope={k:case[k] for k in ('tenantId','entity','caseId','asOf','task')}
        scope.update(topics=trusted_topics,recordIndex=current_index(case['recordIndex']),
            currentSources=current_sources(case['records']))
        identity=dict(version=1,scope=scope,corpus=self.corpus.tenant_digest(case['tenantId']),
            counterDescriptor=self._descriptor,quoteIdentity=self._quote_identity,limits=self._limits,
            outputTokens=self._output,implementation=implementation())
        if self._continuation_budget:identity['dispatchPolicy']='shared-execution-budget-v1'
        return digest(identity)

    def prepare(self,case,arm):
        if arm not in {'enabled','disabled'}:raise ValueError('invalid memory arm')
        identity=self.identity(case)
        if arm=='enabled':r=self.corpus.retrieve(case['tenantId'],case['entity'],case['topics'],case['asOf'])
        else:r=dict(corpusDigest=self.corpus.tenant_digest(case['tenantId']),querySha256=digest(dict(
            entityId=case['entity'],topics=topics(case['topics']),asOf=case['asOf'])),asOf=case['asOf'],
            episodes=[],resultSha256=digest([]),resultBytes=len(encode([])),eligibleCount=None,candidateCount=None)
        mandatory=dict(caseId=case['caseId'],task=case['task'],recordIndex=current_index(case['recordIndex']),draft=None)
        assembled=assemble_context(mandatory,r,quote_inputs=self.quote_inputs,counter_descriptor=self._descriptor,
            quote_identity=self._quote_identity,max_requests=self._limits['providerRequests'],
            output_tokens=self._output,token_ceiling=self._limits['reportedTokens'],
            continuation_budget=self._continuation_budget)
        request,retrieval=assembled['request'],assembled['retrieval']
        return dict(request=request,retrieval=retrieval,arm=arm,
            binding=digest(dict(tenantId=case['tenantId'],arm=arm,request=request,retrieval=retrieval)),
            contextAssembly=dict(identity=identity,plan=assembled['plan'],decisions=assembled['decisions']))
