// Client-observed output chunks. No tokenizer guesses or server phase inference.
export function generationPackets(model,time,{reducedMotion=false}={}) {
  if(reducedMotion||!model.call)return [];
  const output=model.arrivals.filter(p=>time>=p.at&&time-p.at<1.1).slice(-90)
    .map(p=>({direction:'output',position:1-(time-p.at)/1.1}));
  const age=time-model.call.start;
  if(!output.length&&age>=0&&age<.8&&
      (model.call.firstOutputAt===null||time<model.call.firstOutputAt))
    output.push({direction:'request',position:age/.8});
  return output;
}

export function generationAt(run, time, preferredSpan = null) {
  const calls = run.generation?.calls || [];
  const call = calls.find(c => c.spanId === preferredSpan) ||
    calls.filter(c => c.start <= time).at(-1) || calls[0];
  if (!call) return {phase:'empty', call:null, calls, arrivals:[], recent:[],
    chunks:0, characters:0, preview:'', firstOutput:null, largestGap:null,
    uncorrelated:!!run.generation?.uncorrelated};
  const arrivals = (call.samples || []).filter(s => s.at <= time);
  const last = arrivals.at(-1), atTail = call.lastOutputAt !== null && time >= call.lastOutputAt;
  const partial = !!(call.samplesTruncated && last && !atTail && time > last.at);
  const unknownInterval=call.samplesTruncated&&last&&Math.min(time,call.lastOutputAt)>last.at?
    {start:last.at,end:Math.min(time,call.lastOutputAt)}:null;
  const tail=call.samplesTruncated&&atTail?{at:call.lastOutputAt,totalCharacters:call.characters}:null;
  const chunks = atTail ? call.chunks : last?.index || 0;
  const characters = atTail ? call.characters : last?.totalCharacters || 0;
  const firstOutput = call.firstOutputAt !== null && time >= call.firstOutputAt ?
    Math.max(0,call.firstOutputAt-call.start) : null;
  const gaps = arrivals.slice(1).map((p,i) => Math.max(0,p.at-arrivals[i].at));
  const largestGap = atTail && call.chunks > 1 && Number.isFinite(call.maxGap) ? call.maxGap :
    gaps.length ? Math.max(...gaps) : null;
  const finished = call.end !== null && time >= call.end;
  const unavailable = ['buffered','unavailable'].includes(call.mode);
  const phase = time < call.start ? 'queued' : finished&&call.outcome!=='completed'?'interrupted':
    unavailable||run.generation?.uncorrelated?'unavailable':finished?'complete':firstOutput===null?'waiting':'generating';
  const lastOutput=atTail?call.lastOutputAt:last?.at;
  return {call, calls, phase, arrivals, chunks, characters, firstOutput, largestGap, partial,unknownInterval,tail,
    preview:Array.from(call.preview || '').slice(0,characters).join(''),
    sinceLastOutput:!finished && !partial && Number.isFinite(lastOutput) ? Math.max(0,time-lastOutput) : null,
    recent:arrivals.filter(s => s.at >= time-1.1),
    duration:Math.max(.001,(call.end ?? Math.max(time,call.start+.001))-call.start),
    elapsed:Math.max(0,Math.min(time,call.end ?? time)-call.start),
    truncated:!!(run.generation?.truncated || call.samplesTruncated || call.previewTruncated),
    uncorrelated:!!run.generation?.uncorrelated,
  };
}
