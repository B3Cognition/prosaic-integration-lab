import test from 'node:test';
import assert from 'node:assert/strict';
import { observedRun, reportedTokenText, displayUsage, messagePreview } from './live-model.js';
import { stateAt, usageAt } from './sample-runs.js';

const event = (id, at, name, extra = {}) => ({id,at,event:name,source:'runtime',invocation_id:'attempt',...extra});
const feed = {runId:'owned-session',elapsed:2,active:true,available:true,truncated:false,
  usage:{input:null,output:null,totalCalls:1,unknownCalls:1,completeCalls:0,available:true},events:[
    event(1,0,'invocation_started'),event(2,.1,'provider_request_started',{turn:1}),
  ]};

test('an active provider stays active at the current live boundary', () => {
  const run = observedRun(feed);
  const state = stateAt(run,run.duration);
  assert.equal(state.active.component,'provider');
  assert.equal(state.done,false);
  assert.equal(state.calls,1);
  assert.equal(usageAt(run,run.duration).input,null);
});

test('reported transport errors and invocation failures remain distinct', () => {
  const run = observedRun({...feed,active:false,sessionStatus:'failed',events:[...feed.events,
    event(3,1.9,'provider_request_completed',{turn:1,http_status:503,outcome:'completed'}),
    event(4,2,'invocation_completed',{outcome:'execution_failure'}),
  ]});
  assert.equal(run.spans.find(s=>s.component==='provider').httpStatus,503);
  assert.equal(run.spans.find(s=>s.component==='runtime').outcome,'execution_failure');
  assert.equal(stateAt(run,2).providerFailed,true);
});

test('a tool uses its observed name and millisecond duration', () => {
  const run=observedRun({...feed,active:false,waiting:true,events:[...feed.events,
    event(3,1,'provider_request_completed',{turn:1,outcome:'completed'}),
    event(4,1.001,'tool_started',{turn:1,name:'fixture_lookup'}),
    event(5,1.003,'tool_completed',{turn:1,name:'fixture_lookup',status:'ok'}),
    event(6,1.5,'invocation_completed',{outcome:'completed'}),
  ]});
  assert.equal(run.toolName,'fixture_lookup');
  assert.equal(run.status,'waiting');
  const tool=run.spans.find(s=>s.kind==='tool');
  assert.ok(Math.abs(tool.end-tool.start-.002)<1e-9);
  assert.equal(stateAt(run,run.duration).outcome,'waiting');
});

test('truncated or unmatched records never invent missing starts', () => {
  const run=observedRun({...feed,truncated:true,active:false,events:[
    event(3,1,'provider_request_completed',{turn:1,outcome:'completed'})]});
  assert.equal(run.spans.length,0);
  assert.equal(run.incomplete,true);
});

test('replay does not invent per-call token attribution', () => {
  const run=observedRun({...feed,usage:{input:120,output:30,available:true,unknownCalls:0}});
  assert.equal(usageAt(run,0).input,120);
  assert.equal(run.spans.find(s=>s.kind==='provider').inputTokens,undefined);
});

test('a durable needsResolution status is never displayed as completed',()=>{
  const run=observedRun({...feed,active:false,sessionStatus:'needsResolution',events:[
    event(1,0,'invocation_started'),event(2,2,'invocation_completed',{outcome:'completed'})]});
  assert.equal(run.status,'needs_resolution');
  assert.equal(stateAt(run,2).label,'Resolution required');
});

test('a missing tool completion cannot remain active after an invocation timeout',()=>{
  const run=observedRun({...feed,active:false,sessionStatus:'failed',events:[
    event(1,0,'invocation_started'),event(2,.5,'tool_started',{name:'fixture_lookup',turn:1}),
    event(3,2,'invocation_completed',{outcome:'timed_out'})]});
  const tool=run.spans.find(span=>span.kind==='tool');
  assert.equal(tool.pending,false);
  assert.equal(tool.endUnknown,true);
  assert.equal(tool.end,tool.start);
  assert.equal(run.incomplete,true);
  assert.equal(stateAt(run,2).active,undefined);
  assert.equal(run.observedEvents.length,3);
});

test('zero-input provider reports remain known',()=>{
  assert.equal(reportedTokenText({input:0,output:12,available:true,unknownCalls:0}),'12');
  assert.equal(reportedTokenText({input:null,output:null,available:true,unknownCalls:1}),'—');
});

test('unsupported provider counts are visibly unqualified without changing ledger usage',()=>{
  const raw={input:null,output:null,unknownCalls:1,available:true,
    providerReported:{input:520,output:31,unqualifiedCalls:1,unknownCalls:0}};
  assert.equal(reportedTokenText(raw),'551†');
  assert.equal(displayUsage(raw).unqualified,true);
  assert.equal(raw.input,null);
  assert.equal(raw.unknownCalls,1);
});

test('message previews expose only bounded user and assistant text',()=>{
  assert.deepEqual(messagePreview([
    {role:'tool',content:'private arguments'},
    {role:'user',content:[{type:'text',text:'Hello'},{type:'image',url:'private'}]},
    {role:'assistant',content:[{type:'text',text:'<script>literal</script>'},{type:'reasoning',text:'private'}]},
  ]),[{role:'user',text:'Hello'},{role:'assistant',text:'<script>literal</script>'}]);
  assert.equal(messagePreview([{role:'assistant',content:'x'.repeat(10000)}])[0].text.length,4097);
});
