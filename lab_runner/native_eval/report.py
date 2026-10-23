"""Filtered benchmark metrics; fixture latency is integration overhead only."""
import math
import statistics

from . import SUITE_VERSION


def summarize(rows, *, origin, provenance):
    groups = []
    for selector in sorted({row['selector'] for row in rows}):
        selected = [row for row in rows if row['selector'] == selector]
        latencies = sorted(row['durationMs'] for row in selected)
        groups.append({'selector': selector, 'samples': len(selected),
            'completed': sum(row['completed'] for row in selected),
            'passRate': sum(row['passed'] for row in selected) / len(selected),
            'medianMs': statistics.median(latencies),
            'p95Ms': latencies[math.ceil(.95 * len(latencies)) - 1]})
    known = sum(row.get('knownReportedTokens', row['reportedTokens'] or 0) for row in rows)
    complete = all(row['reportedTokens'] is not None for row in rows)
    return {'suiteVersion': SUITE_VERSION, 'origin': origin,
        'passed': bool(rows) and all(row['passed'] for row in rows),
        'modelQualityQualified': False, 'providerRequests': None,
        'sampleCount': len(rows), 'nativeAttempts': (
            None if any(row.get('nativeAttemptsStatus') == 'unknown' for row in rows)
            else sum(row['nativeAttempts'] for row in rows)),
        'reportedTokens': known if complete else None, 'knownReportedTokens': known,
        'groups': groups, 'samples': rows, 'provenance': provenance,
        'measurement': 'integration_overhead' if origin == 'scripted_fixture' else 'bounded_live_pilot'}
