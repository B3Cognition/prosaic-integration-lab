"""Copyable guarded Harness host, using public installed SDK APIs only.

ALWAYS supply trusted scope, tools and policy from the host. NEVER derive them
from borrower messages or treat a saved rule fingerprint as authorization.
"""
from pathlib import Path
from inspect import signature

from prosaic_harness import ConversationBindings, ConversationPolicy

from . import host
from .guards import registry

if not {'guards', 'rule_project', 'rule_project_identity'} <= signature(ConversationBindings).parameters.keys():
    raise ImportError('guarded catalogue conversations need the Harness rule-admission companion candidate')


def build_bindings(*, project=host.BLUEPRINT, config=None, guards=None, tools=None,
                   version='catalogue-desk-rules-v1', project_identity='catalogue-desk-v1'):
    """Admit the composed blueprint once; re-admit these same declarations in each worker.

    Pair with Conversation(..., store=FileSessionStore(...), scope=trusted_scope).
    Policy errors are refused before session creation or provider spend.
    """
    project = Path(project).resolve()
    config = host.load_config(project / 'runtime.yml') if config is None else config
    return ConversationBindings(host.compose(project), version=version, config=config,
        policy=ConversationPolicy(), run_policy=host.policy(),
        custom_tools=host.library_tools() if tools is None else tools,
        guards=registry() if guards is None else guards,
        rule_project=project, rule_project_identity=project_identity)
