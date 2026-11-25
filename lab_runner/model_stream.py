"""Properly terminated, paced SSE for the owned synthetic conversation provider."""
import json
import time

from fastapi.responses import StreamingResponse


def conversation_stream(message, *, model, call_id, usage, delay=0):
    def frame(delta=None, *, finish=None, report=None):
        payload={'id':f'fixture-{call_id}', 'object':'chat.completion.chunk',
            'created':1, 'model':model, 'choices':[] if report else
            [{'index':0, 'delta':delta or {}, 'finish_reason':finish}]}
        if report:payload['usage']=report
        return 'data: '+json.dumps(payload,ensure_ascii=False)+'\n\n'

    def chunks():
        yield frame({'role':'assistant'})
        for index,call in enumerate(message.get('tool_calls',[])):
            function=call['function'];arguments=function['arguments']
            yield frame({'tool_calls':[{'index':index,'id':call['id'],'type':'function',
                'function':{'name':function['name'],'arguments':''}}]})
            for offset in range(0,len(arguments),8):
                if delay:time.sleep(delay)
                yield frame({'tool_calls':[{'index':index,'function':{'arguments':arguments[offset:offset+8]}}]})
        content=message.get('content') or ''
        for offset in range(0,len(content),4):
            if delay:time.sleep(delay)
            yield frame({'content':content[offset:offset+4]})
        yield frame(finish='tool_calls' if message.get('tool_calls') else 'stop')
        yield frame(report=usage)
        yield 'data: [DONE]\n\n'

    return StreamingResponse(chunks(),media_type='text/event-stream',
        headers={'Cache-Control':'no-store','X-Accel-Buffering':'no'})
