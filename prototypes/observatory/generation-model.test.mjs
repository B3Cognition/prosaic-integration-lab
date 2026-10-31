import test from 'node:test';
import assert from 'node:assert/strict';
import { generationAt, generationPackets } from './generation-model.js';

const call={spanId:'event-2',start:1,end:5,mode:'streamed',outcome:'completed',
  firstOutputAt:2,lastOutputAt:4,chunks:3,characters:12,preview:'Hello 🌍there',
  maxGap:1.5,samplesTruncated:false,previewTruncated:false,
  samples:[{index:1,at:2,characters:6,totalCharacters:6},
    {index:2,at:2.5,characters:1,totalCharacters:7},
    {index:3,at:4,characters:5,totalCharacters:12}]};
const run={source:'observed',status:'completed',generation:{calls:[call],truncated:false}};

test('replay reveals actual chunks at their times with Unicode-safe provisional text',()=>{
  const before=generationAt(run,1.9);
  assert.equal(before.chunks,0);assert.equal(before.preview,'');assert.equal(before.firstOutput,null);
  const middle=generationAt(run,2.5);
  assert.equal(middle.chunks,2);assert.equal(middle.characters,7);assert.equal(middle.preview,'Hello 🌍');
  assert.equal(middle.firstOutput,1);assert.equal(middle.largestGap,.5);
  assert.deepEqual(middle.arrivals.map(p=>p.at),[2,2.5]);
  const complete=generationAt(run,5);
  assert.equal(complete.preview,'Hello 🌍there');assert.equal(complete.largestGap,1.5);
  assert.equal(complete.phase,'complete');assert.equal(complete.chunks,3);
});

test('default selection follows the current provider and explicit selection survives later calls',()=>{
  const second={...call,spanId:'event-9',start:7,firstOutputAt:8,lastOutputAt:8,end:9,
    preview:'New',characters:3,chunks:1,samples:[{index:1,at:8,characters:3,totalCharacters:3}]};
  const two={...run,generation:{calls:[call,second]}};
  assert.equal(generationAt(two,5).call.spanId,'event-2');
  assert.equal(generationAt(two,8).call.spanId,'event-9');
  assert.equal(generationAt(two,8,'event-2').call.spanId,'event-2');
});

test('a quiet stream exposes the real current gap without inventing tokens or progress',()=>{
  const active={...run,status:'running',generation:{calls:[{...call,end:null,outcome:'running'}]}};
  const gap=generationAt(active,3.8);
  assert.equal(gap.phase,'generating');assert.ok(Math.abs(gap.sinceLastOutput-1.3)<1e-8);
  assert.equal(gap.chunks,2);assert.equal(gap.characters,7);
  assert.equal(gap.tokensPerSecond,undefined);
  assert.equal(gap.firstOutput,1);
});

test('missing, buffered and single-chunk streams do not invent timing or token rates',()=>{
  assert.equal(generationAt({generation:{calls:[]}},0).phase,'empty');
  const buffered=generationAt({generation:{calls:[{...call,mode:'buffered',samples:[],chunks:0,characters:0,preview:'',firstOutputAt:null,lastOutputAt:null}]}},5);
  assert.equal(buffered.phase,'unavailable');assert.equal(buffered.firstOutput,null);
  const single=generationAt({generation:{calls:[{...call,chunks:1,characters:6,lastOutputAt:2,samples:[call.samples[0]]}]}},5);
  assert.equal(single.largestGap,null);assert.equal(single.chunks,1);
});

test('truncated timing keeps final counters but cannot invent intermediate replay data',()=>{
  const limited={...call,samplesTruncated:true,samples:[call.samples[0]]};
  const trace={...run,generation:{calls:[limited],truncated:true}};
  const partial=generationAt(trace,3);
  assert.equal(partial.chunks,1);assert.equal(partial.partial,true);
  const final=generationAt(trace,5);
  assert.equal(final.chunks,3);assert.equal(final.characters,12);assert.equal(final.truncated,true);
});

test('failed streams remain provisional and do not become successful completed output',()=>{
  const failed={...run,generation:{calls:[{...call,outcome:'unknown'}]}};
  assert.equal(generationAt(failed,5).phase,'interrupted');
});

test('visible packets travel out once then return only for real recent arrivals',()=>{
  const waiting=generationAt(run,1.4);
  assert.deepEqual(generationPackets(waiting,1.4).map(p=>p.direction),['request']);
  assert.deepEqual(generationPackets(waiting,1.4,{reducedMotion:true}),[]);
  assert.deepEqual(generationPackets(waiting,1.9),[]);
  const producing=generationAt(run,2.5);
  const packets=generationPackets(producing,2.5);
  assert.equal(packets.length,2);assert.ok(packets.every(p=>p.direction==='output'));
  assert.ok(packets[0].position<packets[1].position);
  assert.deepEqual(generationPackets(producing,4),[]);
  const burst={...producing,arrivals:Array.from({length:150},()=>({at:2.5}))};
  assert.equal(generationPackets(burst,2.5).length,90);
});

test('a truncated stream uses known live tail timing and marks unrecorded history',()=>{
  const limited={...call,end:null,outcome:'running',samplesTruncated:true,
    lastOutputAt:20,chunks:600,characters:6000,maxGap:.3,
    samples:[{index:512,at:15,characters:10,totalCharacters:5120}]};
  const trace={...run,status:'running',generation:{calls:[limited]}};
  const live=generationAt(trace,20.1);
  assert.ok(Math.abs(live.sinceLastOutput-.1)<1e-8);
  assert.deepEqual(live.unknownInterval,{start:15,end:20});
  assert.deepEqual(live.tail,{at:20,totalCharacters:6000});
  const past=generationAt(trace,18);
  assert.equal(past.sinceLastOutput,null);assert.equal(past.tail,null);
  assert.deepEqual(past.unknownInterval,{start:15,end:18});
});
