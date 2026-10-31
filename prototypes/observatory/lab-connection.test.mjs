import test from 'node:test';
import assert from 'node:assert/strict';
import {connectLab} from './lab-connection.js';

test('POST settlement requires a fresh poll before polling can stop',async t=>{
  const keys=['document','location','fetch','setInterval','clearInterval'];
  const originals=keys.map(key=>[key,Object.getOwnPropertyDescriptor(globalThis,key)]);
  t.after(()=>{for(const[key,descriptor]of originals){if(descriptor)Object.defineProperty(globalThis,key,descriptor);else delete globalThis[key];}});
  const elements=new Map();
  function element(selector){if(!elements.has(selector))elements.set(selector,{value:'',addEventListener(type,callback){this[type]=callback;}});return elements.get(selector);}
  globalThis.document={querySelector:element};globalThis.location={pathname:'/standalone/'};
  const intervals=new Map();let nextTimer=0;
  globalThis.setInterval=callback=>{intervals.set(++nextTimer,callback);return nextTimer;};
  globalThis.clearInterval=id=>intervals.delete(id);
  function deferred(){let resolve;const promise=new Promise(r=>resolve=r);return{promise,resolve};}
  const post=deferred(),stalePoll=deferred(),postRequested=deferred(),stalePollRequested=deferred();
  const response=body=>({ok:true,json:async()=>body});
  const idle={runId:'abc',elapsed:0,active:false,waiting:false,events:[]};
  let reads=0,lastFeed;
  globalThis.fetch=async path=>{
    if(path==='/conversations')return response({sessionId:'abc',revision:'r1'});
    if(path.endsWith('/messages')){postRequested.resolve();return post.promise;}
    if(++reads===1)return response(idle);
    if(reads===2){stalePollRequested.resolve();return stalePoll.promise;}
    return response({...idle,elapsed:1,waiting:true});
  };
  const client=connectLab({onRun:feed=>lastFeed=feed,onStatus:()=>{}});
  element('#lab-token').value='fixture-token';element('#lab-connect').submit({preventDefault(){}});
  element('#lab-message').value='Find players';
  const submitted=element('#lab-run').submit({preventDefault(){}});
  await postRequested.promise;
  const outstandingPoll=[...intervals.values()][0]();await stalePollRequested.promise;
  post.resolve(response({pendingInteraction:{reference:'selection'}}));
  for(let i=0;i<20;i++)await Promise.resolve();
  stalePoll.resolve(response(idle));await Promise.all([submitted,outstandingPoll]);
  assert.equal(client.status().following,true);
  assert.equal(lastFeed.waiting,true,'A fresh, post-settlement observation must win');
  assert.ok(intervals.size>0,'Waiting workflows must remain observable');
});
