"""Private pilot evidence rendering; no retrieval or source access.

Only ``display`` is operator-visible. The returned ID/offset fields are control
metadata derived solely from displayed content. Caller owns provenance checks,
operation/time limits, and isolation of raw responses. Strings are Unicode;
all limits and accounting are UTF-8 bytes. Do not display inputs or raw logs.
"""
from collections import defaultdict
import json

OMITTED = '[omitted]\n'


def _size(value):
    return len(value.encode('utf-8'))


def _clip(value, byte_limit):
    return value.encode('utf-8')[:max(0, byte_limit)].decode('utf-8', errors='ignore')


def _label(value):
    # Quote metadata so embedded newlines/control characters cannot forge frames.
    return json.dumps(str(value), ensure_ascii=False)


def _omission(heading, cap):
    if cap < _size(OMITTED):
        return ''
    return _clip(str(heading) + '\n', cap - _size(OMITTED)) + OMITTED


def source_heading(record):
    """Use the original radius-only source receipt, byte for byte."""
    return (f'source={json.dumps(record["path"])} sourceSha256={record["sourceFileSha256"]} '
        f'sourceId={record["sourceId"]} wing={record["wing"]} revision={record["revision"]} '
        f'namespace={record["namespace"]}')


def document_frame(heading, seed_record, records, omitted=False):
    """Pure whole-record frame construction; callers bound and charge bytes.

    Local receipts retain their legacy layout. Roles stay control metadata;
    a related group has its own source receipt and an explicit group marker.
    """
    text=str(heading)+'\n';spans=[];retained=[];groups={}
    for record in records:
        groups.setdefault(record['sourceId'],[]).append(record)
    local=groups.pop(seed_record['sourceId'],[])
    ordered=([local] if local else [])+list(groups.values())
    legacy=str(heading).startswith('source=')
    def receipt(record):
        if legacy:return source_heading(record)
        return 'source '+' '.join(f'{k}={_label(record[k])}' for k in
            ('path','sourceId','sourceFileSha256','wing','revision','namespace'))
    if local and not legacy:
        text+=receipt(seed_record)+'\n'
    for rows in ordered:
        first=rows[0]
        identity=('path','sourceId','sourceFileSha256','wing','revision','namespace')
        if any(any(r[k]!=first[k] for k in identity) for r in rows):
            raise ValueError('ambiguous context source group')
        if first['sourceId']!=seed_record['sourceId']:
            text+='[related source introduction]\n'+receipt(first)+' contextRole="relatedIntroduction"\n'
        previous=None
        for r in sorted(rows,key=lambda r:r['startChar']):
            if previous is not None and r['startChar']!=previous['endChar']:
                if r['startChar']<previous['endChar']:
                    raise ValueError('overlapping context source bounds')
                text+=f'[gap chars={previous["endChar"]}:{r["startChar"]}]\n'
            bounds=''.join(f' {key}={_label(r[key])}' for key in
                ('startLine','endLine','startChar','endChar') if key in r)
            text+=f'@{r["recordId"]} sha256={r["textSha256"]}{bounds}\n'
            start=len(text);text+=r['text'];end=len(text);text+='\n'
            spans.append(dict(start=start,end=end,recordId=r['recordId']))
            retained.append(r['recordId']);previous=r
    if omitted:text+=OMITTED
    return dict(display=text,bytes=_size(text),omitted=omitted,
        retainedIds=retained,bodySpans=spans)


def lf_lines(text):
    """Exact source lines using rg's LF delimiter, preserving all other bytes."""
    parts = text.split('\n')
    return [part+'\n' for part in parts[:-1]] + ([parts[-1]] if parts[-1] else [])


class EvidenceBudget:
    def __init__(self, limit=32768, used=0):
        if type(limit) is not int or type(used) is not int or not 0 <= used <= limit:
            raise ValueError('invalid byte budget')
        self._limit = limit
        self._used = used

    @property
    def limit(self):
        return self._limit

    @property
    def used(self):
        return self._used

    @property
    def remaining(self):
        return self.limit - self.used

    def charge(self, display):
        """Charge an already bounded display atomically; never silently clip it."""
        amount = _size(display)
        if amount > self.remaining:
            raise ValueError('visible evidence budget exceeded')
        self._used += amount
        return amount

    def _cap(self, value):
        if type(value) is not int or value < 0:
            raise ValueError('invalid response cap')
        return min(value, self.remaining)

    def _result(self, display, omitted, **visible):
        return dict(display=display, bytes=self.charge(display), omitted=omitted, **visible)

    def _source_spans(self, heading, items, retained, offsets):
        """Offsets supplied by construction, never found by searching source text."""
        result=[]
        position=len(str(heading)+'\n')
        for item_id,text in items:
            if item_id in retained and item_id in offsets:
                start,end,identity=offsets[item_id]
                result.append(dict(start=position+start,end=position+end,**identity))
            position+=len(text)
        return result

    def _items(self, heading, items, cap):
        """Fit whole items, reserving an omission marker; return visible IDs."""
        header = str(heading) + '\n'
        complete = header + ''.join(text for _, text in items)
        if _size(complete) <= cap:
            return complete, [item_id for item_id, _ in items], False
        if cap < _size(OMITTED):
            return '', [], True
        body_cap = cap - _size(OMITTED)
        if _size(header) > body_cap:
            return _clip(header, body_cap) + OMITTED, [], True
        display, ids = header, []
        for item_id, text in items:
            if _size(display) + _size(text) > body_cap:
                break
            display += text
            ids.append(item_id)
        return display + OMITTED, ids, True

    def render_search(self, heading, files, previews, maxBytes=6144):
        """Broad file discovery, then previews round-robin across sorted paths.

        Preview records: selectionId, path, line, preview. File records: path,
        count. Preview strings are limited to 160 Unicode characters. Other
        input fields never enter the returned operator view.
        """
        paths = sorted(files, key=lambda f: f['path'])
        groups = defaultdict(list)
        for p in previews:
            groups[p['path']].append(p)
        items = [(None, f'file {_label(f["path"])} matches={int(f["count"])}\n') for f in paths]
        offsets={}
        for i in range(max((len(groups[f['path']]) for f in paths), default=0)):
            for f in paths:
                group = groups[f['path']]
                if i < len(group):
                    p = group[i]
                    prefix=(f'[{_label(p["selectionId"])}] {_label(p["path"])}:{int(p["line"])}\n')
                    body=p['preview'][:160]
                    text=prefix+body+'\n'
                    offsets[p['selectionId']]=(len(prefix),len(prefix)+len(body),
                        dict(selectionId=p['selectionId'],path=p['path']))
                    items.append((p['selectionId'], text))
        display, ids, omitted = self._items(heading, items, self._cap(maxBytes))
        return self._result(display, omitted, visibleSelectionIds=[x for x in ids if x is not None],
            bodySpans=self._source_spans(heading,items,ids,offsets))

    def render_memory_search(self, heading, previews, maxBytes=6144):
        """Preserve exact supplied FTS order; only whitelisted metadata is shown.

        preview is the actual provider excerpt. Parent supplies its existing
        800-character bound; this renderer does not invent a new snippet.
        """
        items,offsets = [],{}
        for p in previews:
            fields = ' '.join(f'{key}={_label(p[key])}' for key in
                              ('path', 'line', 'endLine', 'startChar', 'endChar',
                               'recordId', 'textSha256',
                               'sourceFileSha256', 'sourceId', 'wing', 'revision',
                               'namespace') if key in p)
            prefix=f'[{_label(p["selectionId"])}] {fields}\n'
            items.append((p['selectionId'], prefix+p['preview']+'\n'))
            offsets[p['selectionId']]=(len(prefix),len(prefix)+len(p['preview']),
                dict(recordId=p.get('recordId',p['selectionId'])))
        display, ids, omitted = self._items(heading, items, self._cap(maxBytes))
        return self._result(display, omitted, visibleSelectionIds=ids,
            bodySpans=self._source_spans(heading,items,ids,offsets))

    def render_records(self, heading, seedId, records, limitBytes=5120):
        """Whole verified chunks only, seed/-1/+1/-2/+2 priority.

        records must be immediate source-order neighbors verified by the host.
        Text is never clipped here; callers supply the verified 800-char slices.
        Arbitrary extra metadata is not exposed; common provenance goes in the
        trusted heading. A missing seed or duplicate record identity is an error.
        """
        ids = [r['recordId'] for r in records]
        if len(set(ids)) != len(ids) or seedId not in ids:
            raise ValueError('missing or ambiguous seed')
        seed = ids.index(seedId)
        candidate = [i for i in (seed, seed-1, seed+1, seed-2, seed+2) if 0 <= i < len(records)]
        cap = self._cap(limitBytes)
        frames = {}
        for i in candidate:
            bounds = ''.join(f' {key}={_label(records[i][key])}' for key in
                             ('startLine', 'endLine', 'startChar', 'endChar')
                             if key in records[i])
            frames[i] = (f'@{records[i]["recordId"]} sha256={records[i]["textSha256"]}'
                         f'{bounds}\n{records[i]["text"]}\n')
        def frame(selected):
            omitted = len(selected) != len(records)
            parts, previous = [str(heading) + '\n'], None
            for i in sorted(selected):
                if previous is not None and i != previous + 1:
                    parts.append('[gap]\n')
                parts.append(frames[i])
                previous = i
            if omitted:
                parts.append(OMITTED)
            return ''.join(parts), omitted
        selected = list(candidate)
        while selected:
            display, omitted = frame(selected)
            if _size(display) <= cap:
                spans=[];position=len(str(heading)+'\n');previous=None
                for i in sorted(selected):
                    if previous is not None and i!=previous+1:position+=len('[gap]\n')
                    prefix_length=len(frames[i])-len(records[i]['text'])-1
                    spans.append(dict(start=position+prefix_length,
                        end=position+prefix_length+len(records[i]['text']),recordId=ids[i]))
                    position+=len(frames[i]);previous=i
                return self._result(display, omitted, retainedIds=[ids[i] for i in sorted(selected)],bodySpans=spans)
            selected.pop()  # Furthest/lowest-priority chunks disappear first.
        display = _omission(heading, cap)
        return self._result(display, True, retainedIds=[],bodySpans=[])

    def render_document_context(self,heading,seedId,records,limitBytes=5120):
        """Whole independently verified records, explicit per-source identities.

        Input order is the frozen context planner's priority. Groups display in
        first-source order, records in exact source order. No cross-source text
        is labelled adjacent. No metadata or status becomes quotable evidence.
        """
        ids=[r['recordId'] for r in records]
        if not ids or len(set(ids))!=len(ids) or ids[0]!=seedId or len(ids)>8:
            raise ValueError('invalid document context candidates')
        cap=self._cap(limitBytes)
        selected=list(records)
        while selected:
            result=document_frame(heading,records[0],selected,len(selected)!=len(records))
            if result['bytes']<=cap:
                self.charge(result['display'])
                return result
            selected.pop()
        return self._result(_omission(heading,cap),True,retainedIds=[],bodySpans=[])

    def render_window(self, heading, source, path, line, limitBytes=5120, anchorChar=None):
        """Exact contiguous source slice around a selected 1-based line.

        Offsets are Python Unicode character offsets, not UTF-8 byte offsets.
        Returned text is byte-bounded after path/offset wrappers and markers.
        """
        lines = lf_lines(source)
        if type(line) is not int or not 1 <= line <= len(lines):
            raise ValueError('invalid source line')
        line_start = sum(map(len, lines[:line-1]))
        line_end = line_start + len(lines[line-1])
        if anchorChar is None:
            anchor = line_start + len(lines[line-1].rstrip('\r\n')) // 2
        elif type(anchorChar) is int and line_start <= anchorChar < line_end:
            anchor = anchorChar
        else:
            raise ValueError('match anchor must be within selected line')
        cap = self._cap(limitBytes)
        def frame(start, end):
            omitted = start != 0 or end != len(source)
            text = (f'{heading}\n{_label(path)} chars={start}:{end} anchorLine={line}\n'
                    + source[start:end] + ('\n' + OMITTED if omitted else ''))
            return text, omitted
        lo, hi, best = 0, len(source), None
        # Radius is monotone except small offset-digit changes; retain exact fit.
        while lo <= hi:
            radius = (lo + hi) // 2
            start, end = max(0, anchor-radius), min(len(source), anchor+radius+1)
            display, omitted = frame(start, end)
            if _size(display) <= cap:
                best = display, omitted, start, end
                lo = radius + 1
            else:
                hi = radius - 1
        if best is None:
            display = _omission(heading, cap)
            return self._result(display, True, startChar=None, endChar=None,bodySpans=[])
        display, omitted, start, end = best
        prefix=f'{heading}\n{_label(path)} chars={start}:{end} anchorLine={line}\n'
        return self._result(display, omitted, startChar=start, endChar=end,
            bodySpans=[dict(start=len(prefix),end=len(prefix)+end-start,path=path)])
