"""Atomic batch admission and sanitized partial observations for live runs."""
import time

from lab_runner.live_allowance import AllowanceExhausted
from . import grade


def execute_batch(*, runtime, artifacts, kind, profile, policy, allowance, cwd):
    rows, failure, reservation = [], None, None
    total, unknown = 0, False
    try:
        # Checking remaining capacity without reserving it would race other runs.
        reservation = allowance.reserve(maximum_requests=len(artifacts))
    except AllowanceExhausted:
        failure = 'allowance_exhausted'
    except (OSError, ValueError):
        failure = 'allowance_unavailable'
    if reservation is not None:
        try:
            for artifact in artifacts:
                actual = None
                started = time.monotonic()
                row = dict(effort=artifact.frontmatter['effort'], completed=False,
                    formatCorrect=False, answerCorrect=False, timedOut=False,
                    providerRequests=None, nativeInvocations=None if kind == 'native' else 0,
                    reportedTokens=None)
                try:
                    options = {'profile': profile} if kind == 'native' else {}
                    result = runtime.run(artifact, cwd=cwd, policy=policy, **options)
                    if kind == 'api':
                        actual = result.metadata.get('invocation_budgets_v1', {}).get('provider_requests')
                    else:
                        attempts = result.metadata.get('native_execution_v1', {}).get('attempts')
                        actual = len(attempts) if isinstance(attempts, list) else None
                    actual = actual if type(actual) is int and 0 <= actual <= 1 else None
                    format_correct, answer_correct = grade(result.stdout)
                    row.update(completed=result.exit_code == 0, formatCorrect=format_correct,
                        answerCorrect=answer_correct, timedOut=result.timed_out,
                        providerRequests=actual if kind == 'api' else None,
                        nativeInvocations=actual if kind == 'native' else 0,
                        reportedTokens=result.token_usage)
                    if result.exit_code != 0:
                        failure = 'cancelled' if result.exit_code == 130 else 'execution_failed'
                except KeyboardInterrupt:
                    failure = 'cancelled'
                except Exception:
                    # No SDK exception/configuration/model text enters the receipt.
                    failure = 'execution_exception'
                finally:
                    if actual is None:
                        unknown = True
                    else:
                        total += actual
                    row['durationMs'] = (time.monotonic() - started) * 1000
                    rows.append(row)
                if failure is not None:
                    break
        except KeyboardInterrupt:
            failure = 'cancelled'
        finally:
            try:
                allowance.finish(reservation, actual_requests=None if unknown else total)
            except (OSError, ValueError):
                failure = 'allowance_unavailable'
    try:
        status = allowance.status()
    except (OSError, ValueError):
        status, failure = None, 'allowance_unavailable'
    passed = failure is None and len(rows) == len(artifacts) and all(
        row['completed'] and row['formatCorrect'] and row['answerCorrect'] for row in rows)
    return dict(schemaVersion=1, origin='live_provider', passed=passed, controlsVerified=False,
        modelQualityQualified=False, kind=kind, requestedSamples=len(artifacts), samples=rows,
        allowance=status, failureReason=failure)
