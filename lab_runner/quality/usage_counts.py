"""Count completeness is independent of format/pricing support in SDK evidence."""


def complete_counts(usage):
    """Return normalized input/output/total, or None without guessing missing data."""
    if type(usage) is not dict or usage.get('status') not in ('reported','unsupported'):
        return None
    values=tuple(usage.get(k) for k in ('input_tokens','output_tokens','total_tokens'))
    if any(type(n) is not int or not 0<=n<=2**63-1 for n in values):return None
    return values if values[0]+values[1]==values[2] else None
