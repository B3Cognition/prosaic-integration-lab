"""Host wiring for the catalogue-desk blueprint: tools, composition, config and the runtime.

Everything here is host code. The prose under ``.prosaic/`` declares rules; this
module decides which guards exist (``guards.registry()``), the floor prose cannot
weaken (``runtime.yml``) and which tools the agent may call. The catalogue is a
small in-memory synthetic fixture: replace ``library_tools`` with your own.
"""

from dataclasses import replace
from pathlib import Path

from prosaic import inspect_artifact, parse_rules, strip_tags
from prosaic_runtime import CustomTool, ProsaicArtifact, ProsaicRuntime, RunPolicy, RuntimeConfig

from .guards import REPAIR_STAGES, registry

BLUEPRINT = Path(__file__).parent
CONFIG = BLUEPRINT / 'runtime.yml'
AGENT = 'subagents/catalogue-desk.md'
# Companions are plain rule files beside .prosaic/, never agents: Core does not distribute them.
COMPANIONS = ('companions/loan-desk.md',)
TOOLS = ('catalogue_search', 'loan_terms', 'place_loan')

CATALOGUE = {
    'CAT-0001': {'title': 'Atlas of Invented Rivers', 'shelfMark': 'RIV-12'},
    'CAT-0002': {'title': 'Handbook of Imaginary Knots', 'shelfMark': 'KNO-07'},
}
LOAN_TERMS = {'loanDays': 21, 'currency': 'EUR', 'dailyLateFee': 0.4}

SEARCH_SCHEMA = {
    'type': 'object',
    'properties': {'query': {'type': 'string', 'maxLength': 200}},
    'required': ['query'],
    'additionalProperties': False,
}
RECORD_SCHEMA = {
    'type': 'object',
    'properties': {'recordId': {'type': 'string', 'maxLength': 32}},
    'required': ['recordId'],
    'additionalProperties': False,
}
PLACE_LOAN_SCHEMA = {
    'type': 'object',
    'properties': {'recordId': {'type': 'string', 'maxLength': 32}, 'days': {'type': 'integer', 'minimum': 1}},
    'required': ['recordId', 'days'],
    'additionalProperties': False,
}


def library_tools(on_call=None):
    """Synthetic catalogue tools; ``on_call(name, arguments)`` observes each executed call."""

    def observed(name, handler):
        def run(arguments):
            if on_call is not None:
                on_call(name, dict(arguments))
            return handler(arguments)

        return run

    def search(arguments):
        query = arguments['query'].casefold()
        return {
            'records': [
                {'recordId': record_id, **record, 'link': f'/catalogue/{record_id}'}
                for record_id, record in CATALOGUE.items()
                if query in record['title'].casefold()
            ]
        }

    def terms(arguments):
        if arguments['recordId'] not in CATALOGUE:
            return {'error': 'unknown record'}
        return {'recordId': arguments['recordId'], **LOAN_TERMS}

    def place(arguments):
        if arguments['recordId'] not in CATALOGUE:
            return {'error': 'unknown record'}
        return {'recordId': arguments['recordId'], 'loanDays': arguments['days']}

    return {
        'catalogue_search': CustomTool(
            'catalogue_search',
            'Search the synthetic catalogue by title',
            SEARCH_SCHEMA,
            observed('catalogue_search', search),
            'catalogue-v1',
        ),
        'loan_terms': CustomTool(
            'loan_terms',
            'Loan period and late fee for one record',
            RECORD_SCHEMA,
            observed('loan_terms', terms),
            'terms-v1',
        ),
        'place_loan': CustomTool(
            'place_loan', 'Place a synthetic loan', PLACE_LOAN_SCHEMA, observed('place_loan', place), 'loan-v1'
        ),
    }


def _inspect(project, artifact_id):
    inspected = inspect_artifact(project, artifact_id)
    if not inspected.get('ok'):
        raise ValueError(f'cannot inspect {artifact_id}')
    return inspected['data']


def repair_problems(rules):
    """Rule ids bound with ``fix`` at a stage where their guard returns no repair (see ``REPAIR_STAGES``)."""
    return [
        f'{entry["id"]}: {entry["guard"]} cannot repair at {entry["stage"]}'
        for entry in rules
        if entry.get('kind') == 'enforce'
        and entry.get('action') == 'fix'
        and entry.get('guard') in REPAIR_STAGES
        and entry.get('stage') not in REPAIR_STAGES[entry['guard']]
    ]


def _companion(project, name):
    """A companion: plain Markdown rules, no frontmatter, read and parsed with Core's own functions."""
    path = Path(project) / name
    if path.is_symlink() or not path.is_file():
        raise ValueError(f'companion {name} is not a regular file')
    text = path.read_text(encoding='utf-8')
    if text.startswith('---'):
        raise ValueError(f'companion {name} has frontmatter; companions are rules, never agents')
    return text, parse_rules(text, name)


def compose(project=BLUEPRINT, *, agent=AGENT, companions=COMPANIONS, check=True):
    """One turn's artifact from an agent and its companion rule files.

    The agent's body stays the primary body. Each companion reaches the model as
    a Markdown resource with Core's ``strip_tags`` applied, and its rules come
    from Core's ``parse_rules``, so every binding keeps its own source file. Core
    allows one binding per guard per file; a companion is how the same guard is
    bound at another stage. Companions live outside ``.prosaic/`` without
    frontmatter, so ``prosaic apply`` never distributes one as an agent.

    Files must be distinct. With ``check`` (the default), a ``fix`` binding at a
    stage where its guard returns no repair is refused here, before any request.
    """
    names = [agent, *companions]
    if len(set(names)) != len(names):
        raise ValueError('compose needs distinct agent and companion files')
    primary = _inspect(project, agent)
    document = {key: primary[key] for key in ('id', 'type', 'frontmatter', 'body')}
    document['resources'] = list(primary.get('resources', []))
    rules, issues = list(primary.get('rules', [])), list(primary.get('ruleIssues', []))
    for name in companions:
        text, parsed = _companion(project, name)
        document['resources'].append({'relPath': name, 'content': strip_tags(text)})
        rules += parsed['rules']
        issues += parsed['issues']
    if check and (problems := repair_problems(rules)):
        raise ValueError('; '.join(problems))
    if rules or issues:  # No tag, no keys: an untagged composition is unchanged.
        document.update(rules=rules, ruleIssues=issues)
    return ProsaicArtifact.from_inspection(document)


def load_config(path=CONFIG, *, base_url=None):
    """Operator config; ``base_url`` replaces the default profile's endpoint (used by the Lab's fixture)."""
    config = RuntimeConfig.load(path)
    if base_url is None:
        return config
    profile = config.default_profile
    profiles = {**config.profiles, profile: replace(config.profiles[profile], base_url=base_url)}
    return replace(config, profiles=profiles)


def build_runtime(config, *, project=BLUEPRINT, guards=None, tools=None):
    """Register guards and tools in Python; ``guards=()`` registers none."""
    return ProsaicRuntime(
        config,
        source=Path(project) / '.prosaic',
        custom_tools=library_tools() if tools is None else tools,
        guards=registry() if guards is None else list(guards),
    )


def policy():
    """Per-turn bounds. A retry never adds a request beyond max_provider_requests."""
    return RunPolicy(allowed_tools=frozenset(TOOLS), max_provider_requests=6, max_tool_calls=6, timeout_s=30)
