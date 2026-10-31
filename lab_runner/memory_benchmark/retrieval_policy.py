"""Explicit host-frozen keyword interpretation and bounded candidate selection."""
import re
import subprocess
import json

from .storage import require
from .budget_views import lf_lines

LEGACY_POLICY = 'literal-first-v1'
BALANCED_POLICY = 'terms-round-robin-v2'
POLICIES = (LEGACY_POLICY, BALANCED_POLICY)


def validate_policy(value):
    require(type(value) is str and value in POLICIES, 'unknown retrieval policy')
    return value


def keywords(query):
    terms = []
    seen = set()
    for term in re.findall(r'[^\W_]+', query):
        folded = term.casefold()
        if folded not in seen:
            seen.add(folded)
            terms.append(term)
    require(bool(terms), 'query has no alphanumeric keywords')
    return terms


def round_robin(groups, *, key=lambda item: item, limit=5):
    queues = [iter(group) for group in groups]
    selected, seen = [], set()
    while len(selected) < limit:
        added = False
        for queue in queues:
            for item in queue:
                identity = key(item)
                if identity in seen:
                    continue
                selected.append(item)
                seen.add(identity)
                added = True
                break
            if len(selected) == limit:
                break
        if not added:
            break
    return selected


def keyword_file_candidates(texts, terms, remaining):
    """Top five whole-word OR line anchors, ranked without source/key inspection.

    Only the selected candidate bodies/counts are returned to the renderer.
    Scanning remains within the caller's frozen corpus and task deadline.
    """
    best, counts = [], {}
    rank = lambda item: (-item['termCount'], item['path'], item['line'])
    for path in sorted(texts):
        lines = lf_lines(texts[path])
        starts, position = [], 0
        for line in lines:
            starts.append(position)
            position += len(line)
        masks, anchors = [0]*len(lines), [None]*len(lines)
        # rg's combined OR submatches do not enumerate overlapping patterns.
        # Independent scans keep coverage in rg's own Unicode semantics.
        for index, term in enumerate(terms):
            result = subprocess.run(['rg','--json','-i','-F','-w','-e',term,'--'],
                input=texts[path].encode(),capture_output=True,timeout=min(10,remaining()))
            remaining()
            require(result.returncode in (0, 1), 'rg failed')
            for raw in result.stdout.decode('utf-8').split('\n'):
                if not raw:
                    continue
                event = json.loads(raw)
                if event['type'] != 'match':
                    continue
                match = event['data']
                number = match['line_number']
                line = lines[number-1]
                require(match['lines'] == {'text':line} and bool(match['submatches']), 'exact rg source line')
                raw_line = line.encode('utf-8')
                positions = []
                for submatch in match['submatches']:
                    start, end = submatch['start'], submatch['end']
                    require(type(start) is int and type(end) is int and 0 <= start < end <= len(raw_line)
                        and submatch['match']['text'].encode('utf-8') == raw_line[start:end], 'exact rg matched bytes')
                    positions.append(len(raw_line[:start].decode('utf-8')))
                first = min(positions)
                masks[number-1] |= 1 << index
                previous = anchors[number-1]
                anchors[number-1] = first if previous is None else min(previous,first)
        count = 0
        for number,(mask,anchor) in enumerate(zip(masks,anchors),1):
            if not mask:
                continue
            line = lines[number-1]
            count += 1
            best.append(dict(path=path, line=number, preview=line.rstrip('\r\n')[:160],
                anchorChar=starts[number-1]+anchor, termCount=mask.bit_count()))
            best.sort(key=rank)
            del best[5:]
        if count:
            counts[path] = count
        remaining()
    files = [dict(path=path, count=counts[path]) for path in sorted({p['path'] for p in best})]
    return best, files
