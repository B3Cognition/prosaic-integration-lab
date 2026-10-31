"""Bounded trusted-host evaluation criteria, separate from frozen sources."""
from .contracts import ReviewError, own

CONTEXT_VERSION = 'host-review-context-v1'
CONTEXT_GUIDANCE = (
    'reviewContext contains host evaluation criteria, not source evidence. '
    'Examine the supplied source commitments against those criteria. The seed '
    'is a hypothesis, never an established fact or a required source definition. '
    'Do not redefine usability to exclude a demonstrated gap. Distinguish '
    'missing support from incompatible commitments: absence alone is not CONFLICT. '
    'Do not invent missing rules, definitions, external policies or author assent. '
    'Preserve unanswered normative choices and substantive gaps in open_questions. '
    'Canonical turn and provenance rules still apply independently.'
)


def freeze_context(value):
    if (type(value) is not dict or set(value)!={'purpose','issueDefinitions','instructions'}
            or any(type(value[k]) is not str or not value[k].strip()
                   or len(value[k].encode())>8192 for k in ('purpose','instructions'))):
        raise ReviewError('invalid_review_context')
    definitions=value['issueDefinitions']
    if (type(definitions) is not dict or not 1<=len(definitions)<=32
            or any(type(k) is not str or not k.strip() or len(k)>128
                   or type(v) is not str or not v.strip() or len(v.encode())>2048
                   for k,v in definitions.items())):
        raise ReviewError('invalid_review_context')
    try:
        return own(value,32768)
    except ReviewError:
        raise ReviewError('invalid_review_context') from None
