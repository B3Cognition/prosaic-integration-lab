// Synthetic fixtures. Nothing here is a live run or provider estimate.
const common = [
  { id: 'request', component: 'lab', label: 'Request accepted', start: 0, end: 1.1, kind: 'host', outcome: 'completed' },
  { id: 'dispatch', component: 'harness', label: 'Workflow dispatch', start: 1.1, end: 2.4, kind: 'host', outcome: 'completed' },
  { id: 'provider-1', component: 'provider', label: 'Tool selection', start: 2.4, end: 8.6, kind: 'provider', outcome: 'completed', inputTokens: 1640, outputTokens: 128 },
  { id: 'tool-handoff', component: 'runtime', label: 'Dispatch tool', start: 8.6, end: 9, kind: 'host', outcome: 'completed' },
];
const success = {
  id: 'sample-7a41', name: 'Tool-assisted response', duration: 24, outcome: 'completed',
  spans: [...common,
    { id: 'tool', component: 'tool', label: 'read_file', start: 9, end: 12, kind: 'tool', outcome: 'completed' },
    { id: 'model-handoff', component: 'runtime', label: 'Prepare next turn', start: 12, end: 12.4, kind: 'host', outcome: 'completed' },
    { id: 'provider-2', component: 'provider', label: 'Final response', start: 12.4, end: 21.5, kind: 'provider', outcome: 'completed', inputTokens: 2460, outputTokens: 512 },
    { id: 'settle', component: 'lab', label: 'Response delivered', start: 21.5, end: 24, kind: 'host', outcome: 'completed' },
  ],
};
const timeout = {
  id: 'sample-9b02', name: 'Tool timeout', duration: 13.8, outcome: 'timed_out',
  spans: [...common,
    { id: 'tool', component: 'tool', label: 'read_file deadline', start: 9, end: 13, kind: 'tool', outcome: 'timed_out' },
    { id: 'settle', component: 'lab', label: 'Timeout recorded', start: 13, end: 13.8, kind: 'host', outcome: 'timed_out' },
  ],
};
export const RUNS = Object.freeze({ success, timeout });
export const COMPONENTS = Object.freeze({
  lab: { name: 'Integration lab', role: 'Application boundary', description: 'Accepts the request and presents the result.', color: '#a4b4aa' },
  harness: { name: 'Harness', role: 'Workflow control', description: 'Sequences the workflow and commits its transitions.', color: '#a4b4aa' },
  runtime: { name: 'Runtime', role: 'Execution chamber', description: 'Coordinates model turns and registered tools.', color: '#ff8c65' },
  provider: { name: 'Provider', role: 'Model transport', description: 'Receives requests and returns responses with usage reports.', color: '#5ce0db' },
  tool: { name: 'read_file', role: 'Registered tool', description: 'Returns file evidence for the next model turn.', color: '#e7bd72' },
});
export function usageAt(run, time = Infinity) {
  // Recorder totals have an as-of time, not a proven association with individual
  // observer spans. Do not pretend they were known at an earlier replay cursor.
  if (run.source === 'observed') return run.observedUsage;
  const completed=run.spans.filter(s=>s.kind==='provider'&&s.end<=time);
  const started=run.spans.filter(s=>s.kind==='provider'&&s.start<=time);
  if(started.length&&!completed.length)return {input:null,output:null,available:true,unknownCalls:started.length};
  return completed.reduce((a, s) => ({
    input: a.input + s.inputTokens, output: a.output + s.outputTokens,
  }), { input: 0, output: 0 });
}
export function stateAt(run, time) {
  const t = Math.max(0, Math.min(run.duration, time));
  const candidates = run.spans.filter(s => s.start <= t && (s.pending || t < s.end));
  const active = candidates.find(s=>s.kind==='tool') || candidates.find(s=>s.kind==='provider') || candidates.at(-1);
  const reports = usageAt(run, t);
  const done = t >= run.duration && run.status !== 'running';
  const outcome = done ? run.outcome : 'running';
  const labels = {completed:'Turn completed',waiting:'Waiting for input',failed:'Execution failed',timed_out:'Run timed out',needs_resolution:'Resolution required',ready:'Ready'};
  const failures=new Set(['timed_out','execution_failure','http_error','failed','budget_failure','critical_hook_error','cancelled']);
  return { time: t, active, done, reports,
    calls: run.spans.filter(s => s.kind === 'provider' && s.start <= t).length,
    outcome,
    toolFailed: run.spans.some(s => s.kind === 'tool' && !s.pending && failures.has(s.outcome) && s.end <= t),
    providerFailed: run.spans.some(s => s.kind === 'provider' && !s.pending && failures.has(s.outcome) && s.end <= t),
    label: done ? run.source==='observed'?labels[outcome]||outcome:run.outcome === 'completed'?'Response delivered':'Run timed out' : active?.label || (run.source==='observed'?'Awaiting execution events':'Runtime handoff'),
  };
}
export function eventsFor(run) {
  if(run.source==='observed')return run.observedEvents;
  return run.spans.flatMap(s => [
    { at: s.start, component: s.component, label: s.kind === 'provider' ? 'provider_request_started' : s.kind === 'tool' ? 'tool_started' : s.label, outcome: 'started', spanId: s.id },
    { at: s.end, component: s.component, label: s.kind === 'provider' ? 'provider_request_completed' : s.kind === 'tool' ? 'tool_completed' : s.label, outcome: s.outcome, spanId: s.id },
  ]).sort((a, b) => a.at - b.at);
}
