"""Guards this host registers. Markdown can bind them by name; it can never define one.

Copy this file, replace ``loan_period_within_policy`` with your own domain guard
and keep ``registry()`` as the single list you pass to ``ProsaicRuntime``.
"""

import math

from prosaic_runtime import Guard, Verdict, generic_guards

LOAN_TOOL = 'place_loan'
# Feedback carries refused values; Runtime refuses (as a guard fault) any it cannot deliver.
_REFUSABLE = 10**15


def _number(value):
    """A finite JSON number, compared by value; None for anything else, including bools.

    JSON Schema's ``integer`` admits whole-number floats such as ``28.0``, so a
    policy check must never assume ``int``: checking the type would wave them through.
    ``isfinite`` is applied to floats only: it converts ints to float, which
    overflows for very large ints such as ``10**400``.
    """
    if type(value) is int or (type(value) is float and math.isfinite(value)):
        return value
    return None


def _refused(days):
    """Report a refused period only when it is small enough to deliver as feedback."""
    return (days,) if abs(days) < _REFUSABLE else ()


def _loan_period(stage, context):
    """A loan placed by the agent never exceeds the policy's ``max_days``.

    before_tool: a request above the limit is repaired to the limit (``fix``).
    after_tool: a placed loan must report a readable period within the limit.
    It is never repaired, because the loan already exists, and a period the
    desk does not report, or reports unreadably, fails closed; bind it with
    ``fail`` or ``retry``. A result without a placed loan (a tool error, or an
    ``error`` result with no ``loanDays``) is not a loan and passes.
    Guards are trusted host code: keep them quick, bounded and side-effect free.
    """
    if context.tool_name != LOAN_TOOL:
        return Verdict(True)
    limit = context.settings['max_days']
    if stage == 'before_tool':
        arguments = context.arguments
        days = _number(arguments.get('days'))
        if days is None or days <= limit:
            return Verdict(True)  # The tool schema owns type checks; this guard owns policy.
        return Verdict(
            False, reason='loan period above policy', refused_values=_refused(days), fixed={**arguments, 'days': limit}
        )
    outcome = context.tool_result
    if not isinstance(outcome, dict) or outcome.get('status') != 'ok':
        return Verdict(True)  # The tool did not complete, so no loan was placed.
    result = outcome.get('result')
    if isinstance(result, dict) and 'error' in result and 'loanDays' not in result:
        return Verdict(True)  # The desk refused the loan.
    days = _number(result.get('loanDays')) if isinstance(result, dict) else None
    if days is None:
        return Verdict(False, reason='loan desk reported no readable loan period')
    if days > limit:
        return Verdict(False, reason='loan desk reported a period above policy', refused_values=_refused(days))
    return Verdict(True)


LOAN_PERIOD = Guard(
    'loan_period_within_policy',
    'loan-period-v1',  # Change the version whenever the check's behaviour changes: it is in the fingerprint.
    ('before_tool', 'after_tool'),
    _loan_period,
    fixes=True,
    settings_schema={
        'type': 'object',
        'additionalProperties': False,
        'required': ['max_days'],
        'properties': {'max_days': {'type': 'integer', 'minimum': 1, 'maximum': 365}},
    },
)


# Runtime's ``fixes=True`` covers a whole guard, so it would admit ``fix`` at
# after_tool, where this guard never returns a repair. The host narrows it per
# stage: ``host.compose`` refuses ``fix`` anywhere else, before any request.
REPAIR_STAGES = {LOAN_PERIOD.name: ('before_tool',)}


def registry():
    """Fresh registrations: the four generic Runtime guards plus this blueprint's domain guard."""
    return [*generic_guards(), LOAN_PERIOD]
