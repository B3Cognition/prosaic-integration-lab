// Convert allowlisted SDK observations into spans without inventing timestamps.
export function observedRun(feed, {requestPending=false} = {}) {
  const events = [...(feed.events || [])].sort((a,b)=>a.at-b.at || a.id-b.id);
  const elapsed = Math.max(0, Number(feed.elapsed) || 0);
  const spans = [], open = new Map(), eventLog = [];
  let incomplete = Boolean(feed.truncated), providerCount = 0, invocationCount = 0;
  const key = (event, kind) => `${event.invocation_id || 'unknown'}:${kind}:${kind==='runtime'?'':event.turn??0}:${kind==='tool'?event.name||'unknown':''}`;
  for (const event of events) {
    const entry = {at:event.at,label:event.event,component:event.source==='harness'?'harness':'runtime',outcome:event.outcome||event.status||'observed'};
    let kind = event.event.startsWith('provider_request_') ? 'provider' : event.event.startsWith('tool_') ? 'tool' : event.event.startsWith('invocation_') ? 'runtime' : null;
    if (kind) {
      entry.component=kind;
      const identity=key(event,kind);
      if (event.event.endsWith('_started')) {
        const label=kind==='provider'?`Provider call ${++providerCount}`:kind==='tool'?event.name||'Registered tool':`Runtime invocation ${++invocationCount}`;
        const span={id:'event-'+event.id,invocationId:event.invocation_id,component:kind,kind:kind==='runtime'?'host':kind,label,
          start:event.at,end:elapsed,pending:true,outcome:'running'};
        spans.push(span); entry.spanId=span.id;
        if(!open.has(identity))open.set(identity,[]);open.get(identity).push(span);
      } else {
        const span=open.get(identity)?.shift();
        if(span) {
          span.end=Math.max(span.start,event.at);span.pending=false;
          span.outcome=event.http_status>=400?'http_error':event.status==='error'?'execution_failure':event.outcome||'completed';
          if(event.http_status)span.httpStatus=event.http_status;
          entry.spanId=span.id;
        } else incomplete=true;
        if(kind==='runtime')for(const list of open.values())for(const child of list){
          if(child.pending&&child.invocationId===event.invocation_id){
            child.pending=false;child.endUnknown=true;child.observedUntil=event.at;
            child.end=child.start;child.outcome='unknown';incomplete=true;
          }
        }
      }
    } else if(event.source==='harness') {
      const point={id:'event-'+event.id,component:'harness',kind:'host',label:event.event.replaceAll('_',' '),
        start:event.at,end:event.at,instant:true,pending:false,outcome:event.outcome||'completed'};
      spans.push(point);entry.spanId=point.id;
    }
    eventLog.push(entry);
  }
  const lastInvocation=[...events].reverse().find(event=>event.event==='invocation_completed');
  const status=feed.sessionStatus==='needsResolution'?'needs_resolution':feed.active||requestPending?'running':feed.waiting?'waiting':feed.sessionStatus==='failed'||lastInvocation&&lastInvocation.outcome!=='completed'?
    lastInvocation?.outcome==='timed_out'||feed.failureCode==='timeout'?'timed_out':'failed':lastInvocation?'completed':'ready';
  if(status==='needs_resolution')for(const span of spans)if(span.pending){
    span.pending=false;span.endUnknown=true;span.observedUntil=elapsed;span.end=span.start;span.outcome='unknown';incomplete=true;
  }
  return {id:feed.runId,name:'Recorded lab run',duration:elapsed,outcome:status,status,source:'observed',
    spans,observedEvents:eventLog,observedUsage:feed.usage||{input:null,output:null,available:false},
    incomplete,toolName:[...spans].reverse().find(span=>span.kind==='tool')?.label||'Registered tool'};
}

export function formatDuration(seconds) {
  if(seconds>=1)return seconds.toFixed(1)+' s';
  if(seconds<.001)return '<1 ms';
  return (seconds*1000).toFixed(seconds<.01?1:0)+' ms';
}

export function reportedTokenText(usage) {
  usage=displayUsage(usage);
  if(usage.available===false||!Number.isFinite(usage.input)||!Number.isFinite(usage.output))return '—';
  return (usage.unknownCalls?'≥':'')+(usage.input+usage.output).toLocaleString('en-US')+(usage.unqualified?'†':'');
}

export function displayUsage(usage) {
  return usage.providerReported?{...usage,...usage.providerReported,unqualified:true}:usage;
}

export function messagePreview(messages) {
  return (Array.isArray(messages)?messages:[]).filter(m=>m&&['user','assistant'].includes(m.role)).slice(-6).map(m=>{
    const content=typeof m.content==='string'?m.content:Array.isArray(m.content)?m.content.filter(b=>b?.type==='text'&&typeof b.text==='string').map(b=>b.text).join('\n'):'';
    return {role:m.role,text:content.length>4096?content.slice(0,4096)+'…':content};
  }).filter(m=>m.text);
}
