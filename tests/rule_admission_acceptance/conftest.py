"""Shared synthetic scenarios for the rule-admission blueprint lane; no live models."""

from dataclasses import replace
import shutil
from types import SimpleNamespace

import pytest

AGENT = 'subagents/catalogue-desk.md'
COMPANION = 'subagents/loan-desk.md'
IDS = SimpleNamespace(
    seen_ids=f'{AGENT}:9:args_reference_seen_ids',
    loan_before=f'{AGENT}:10:loan_period_within_policy',
    links=f'{AGENT}:11:no_wrapped_links',
    values=f'{AGENT}:12:value_in_tool_output',
    prose_only=f'{AGENT}:13:prose-only',
    loan_after=f'{COMPANION}:8:loan_period_within_policy',
)
HAPPY_MESSAGE = 'Please borrow the Atlas of Invented Rivers for 14 days.'
HAPPY_ANSWER = 'Your loan of [Atlas of Invented Rivers](/catalogue/CAT-0001) is due back in 14 days.'


def failure(turn):
    return turn.evidence.to_dict()['failureCode']


def queue_happy(provider):
    """Search, borrow within policy, answer with a plain link: no rule fires."""
    provider.queue_calls(('call-1', 'catalogue_search', {'query': 'Invented Rivers'}))
    provider.queue_calls(('call-2', 'place_loan', {'recordId': 'CAT-0001', 'days': 14}))
    provider.queue_text(HAPPY_ANSWER)


def copy_project(tmp_path, edits=None, *, strip=False):
    """Copy the blueprint and apply exact text edits; strip=True removes every tag with Core."""
    from prosaic import strip_tags

    from lab_runner.rule_admission import BLUEPRINT

    target = tmp_path / 'project'
    shutil.copytree(BLUEPRINT, target, ignore=shutil.ignore_patterns('__pycache__'))
    for relative, changes in (edits or {}).items():
        path = target / '.prosaic' / relative
        text = path.read_text()
        for old, new in changes:
            assert text.count(old) == 1, f'edit anchor not unique in {relative}: {old!r}'
            text = text.replace(old, new)
        path.write_text(text)
    if strip:
        for relative in (AGENT, COMPANION):
            path = target / '.prosaic' / relative
            path.write_text(strip_tags(path.read_text()))
    return target


def run_turn(provider, message, *, project=None, config=None, guards=None, tools=None, required_guards='file'):
    """One conversation turn of the composed agent against the scripted provider.

    guards=None registers the blueprint registry; guards=() registers nothing. A fixed
    public InvocationScope makes Runtime's opaque tool-call ids repeatable, as in
    Runtime's own untagged golden capture, so turns compare as raw request bytes.
    """
    from prosaic_runtime import InvocationScope

    from lab_runner.rule_admission import BLUEPRINT
    from lab_runner.rule_admission.blueprint import host

    project = BLUEPRINT if project is None else project
    config = host.load_config(base_url=provider.url) if config is None else config
    if required_guards != 'file':
        config = replace(config, required_guards=required_guards)
    runtime = host.build_runtime(config, project=project, guards=guards, tools=tools)
    return runtime.turn(
        host.compose(project),
        message=message,
        policy=host.policy(),
        operation_context=InvocationScope('blueprint-turn'),
    )


@pytest.fixture
def provider():
    from lab_runner.rule_admission.fixtures import scripted_provider

    with scripted_provider() as scripted:
        yield scripted


@pytest.fixture
def lab():
    return SimpleNamespace(
        ids=IDS,
        agent=AGENT,
        companion=COMPANION,
        happy_message=HAPPY_MESSAGE,
        happy_answer=HAPPY_ANSWER,
        failure=failure,
        queue_happy=queue_happy,
        copy_project=copy_project,
        run_turn=run_turn,
    )
