"""Private local trace; receipts remain the authority for dispatch and usage."""
import os
from pathlib import Path
from threading import RLock
from prosaic_runtime.accounting import MemoryRecorder
from lab_runner.quality.allowance import private_directory,private_write
from lab_runner.quality.contracts import decode,encode


class TraceRecorder(MemoryRecorder):
    # Snapshot persistence is local evidence, not a production billing recorder.
    durable=False
    def __init__(self,path,*,provider_id='openai-compatible'):
        self.path=Path(path);private_directory(self.path.parent)
        self._lock=RLock();self._proposals=[];self._events=[];self._failures=None
        try:fd=os.open(str(self.path)+'.claim',os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
        except FileExistsError:raise ValueError('existing scoped execution requires receipt-only recovery') from None
        os.close(fd)
        super().__init__(namespace='scoped-memory',environment='qualification',provider_id=provider_id)
        self._save()

    def _save(self):
        private_write(self.path,dict(version=1,intents=self.intents,observations=self.observations,
            proposals=self._proposals,events=self._events,receiptFailures=self._failures))

    def prepare(self,intent):
        with self._lock:super().prepare(intent);self._save()

    def observe(self,call_id,observation):
        with self._lock:super().observe(call_id,observation);self._save()

    def proposals(self,rows):
        with self._lock:self._proposals=decode(encode(rows));self._save()

    def event(self,event):
        event=decode(encode(event))
        if 'tool_outcome' in event:
            from prosaic_runtime import ToolOutcome
            raw=event.pop('tool_outcome')
            try:outcome=ToolOutcome.from_dict(raw).to_dict()
            except (ValueError,TypeError):outcome=None
            if outcome is not None:event['tool_outcome']=outcome
        with self._lock:self._events.append(event);self._save()

    def finish(self,receipts):
        with self._lock:
            self._failures=[]
            for receipt in receipts:
                result=receipt['result']
                if result['exit_code']:
                    self._failures.append(dict(invocationId=receipt['id'],kind='invocation',
                        reason=result.get('metadata',{}).get('failure_reason') or 'unclassified'))
                for event in receipt['events']:
                    if event.get('event')=='tool_completed' and event.get('status')!='ok':
                        from prosaic_runtime import ToolOutcome
                        try:outcome=ToolOutcome.from_dict(event.get('tool_outcome')).to_dict()
                        except (ValueError,TypeError):outcome=None
                        self._failures.append(dict(invocationId=receipt['id'],kind='tool',
                            reason=outcome['code'] if outcome is not None else 'unclassified',
                            callId=event.get('call_id'),**({'toolOutcome':outcome} if outcome is not None else {})))
            self._save()
