"""Bounded provisional ordinary output; client arrivals are not token evidence.

All methods run under the owning RunObservations lock. No independent dispatch,
SDK imports, prompt/argument capture, or accounting decisions belong here.
"""
from collections import deque
from copy import deepcopy


class GenerationTrace:
    def __init__(self):
        self.calls = deque(maxlen=32)
        self.truncated = False
        self.uncorrelated = False
        self.tool_after = set()

    def observe(self, event):
        kind, invocation = event['event'], event.get('invocation_id')
        if kind == 'tool_started':
            previous=next((call for call in reversed(self.calls)
                if call['invocationId']==invocation),None)
            if previous is not None and previous['end'] is not None:
                self.tool_after.add(previous['spanId'])
        elif kind == 'provider_request_started':
            if not invocation:
                self.uncorrelated=True
                return
            if len(self.calls)==self.calls.maxlen:
                oldest=self.calls[0]
                self.uncorrelated |= oldest['end'] is None
                self.tool_after.discard(oldest['spanId'])
            self.truncated |= len(self.calls) == self.calls.maxlen
            self.calls.append({'spanId':'event-'+str(event['id']),
                'invocationId':invocation, 'start':event['at'], 'end':None,
                'outcome':'running', 'mode':'waiting', 'firstOutputAt':None,
                'lastOutputAt':None, 'maxGap':None, 'chunks':0, 'characters':0, 'preview':'',
                'samples':[], 'samplesTruncated':False, 'previewTruncated':False})
        elif kind in {'provider_request_completed','invocation_completed'}:
            opened = [call for call in self.calls if call['end'] is None
                and call['invocationId'] == invocation]
            # Completion without unique identity is not permission to guess.
            if kind == 'provider_request_completed' and len(opened) != 1:
                self.uncorrelated |= any(call['end'] is None for call in self.calls)
                return
            for call in opened:
                call['end'] = event['at']
                outcome=event.get('outcome')
                call['outcome'] = ('unknown' if kind == 'invocation_completed' else
                    outcome if outcome is not None and outcome!='completed' else
                    'failed' if event.get('status') == 'error' or event.get('http_status',200) >= 400 else
                    'completed' if outcome=='completed' or event.get('status')=='ok' else 'unknown')
                if call['mode'] == 'waiting':
                    call['mode'] = 'unavailable'
            if kind=='invocation_completed' and event.get('outcome')!='completed':
                latest=next((call for call in reversed(self.calls)
                    if call['invocationId']==invocation),None)
                # HTTP completion cannot confirm a valid terminal SSE frame.
                # A later tool failure, however, does not invalidate its input stream.
                if (latest is not None and latest['outcome']=='completed' and
                        latest['spanId'] not in self.tool_after):
                    latest['outcome']='unknown'

    def output(self, event, at, *, capture_text=True):
        if (type(event) is not dict or event.get('provisional') is not True or
                event.get('event') not in {'text_delta','text'} or
                type(event.get('text')) is not str or not 0 < len(event['text']) <= 65536):
            return
        opened = [call for call in self.calls if call['end'] is None]
        if len(opened) != 1 or self.uncorrelated:
            return
        call = opened[0]
        if event['event'] == 'text':
            if not call['chunks']:
                call['mode'] = 'buffered'
            return
        call['mode'] = 'streamed'
        call['chunks'] += 1
        call['characters'] += len(event['text'])
        if call['firstOutputAt'] is None:
            call['firstOutputAt'] = at
        if call['lastOutputAt'] is not None:
            call['maxGap'] = max(call['maxGap'] or 0,round(max(0,at-call['lastOutputAt']),6))
        call['lastOutputAt'] = at
        if len(call['samples']) < 512:
            call['samples'].append({'index':call['chunks'], 'at':at,
                'characters':len(event['text']), 'totalCharacters':call['characters']})
        else:
            call['samplesTruncated'] = True
        if capture_text:
            remaining = max(0,4096-len(call['preview']))
            call['preview'] += event['text'][:remaining]
            call['previewTruncated'] |= call['characters'] > 4096
        else:
            call['previewWithheld'] = True

    def snapshot(self):
        return {'version':1, 'calls':deepcopy(list(self.calls)), 'truncated':self.truncated,
            'uncorrelated':self.uncorrelated}
