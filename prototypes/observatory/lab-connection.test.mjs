import test from 'node:test';
import assert from 'node:assert/strict';
import {connectLab} from './lab-connection.js';

function browser(t,{hosted=false}={}) {
  const keys=['document','location','history','fetch','setInterval','clearInterval'];
  const originals=keys.map(key=>[key,Object.getOwnPropertyDescriptor(globalThis,key)]);
  t.after(()=>{for(const[key,descriptor]of originals){if(descriptor)Object.defineProperty(globalThis,key,descriptor);else delete globalThis[key];}});
  const elements=new Map(),timers=new Map();let next=0;
  const element=key=>{if(!elements.has(key))elements.set(key,{value:'',addEventListener(type,fn){this[type]=fn;}});return elements.get(key);};
  globalThis.document={querySelector:element};globalThis.location={pathname:hosted?'/observatory/':'/standalone/',hash:''};
  globalThis.history={replaceState(){}};
  globalThis.setInterval=fn=>{timers.set(++next,fn);return next;};globalThis.clearInterval=id=>timers.delete(id);
  return {element,timers};
}

test('reloading restores an authorized launcher session without dispatching a run',async t=>{
  const {element}=browser(t,{hosted:true});const requests=[];
  globalThis.fetch=async(path,options)=>{requests.push([path,options]);return {ok:true,json:async()=>path==='/chat/session'?{token:'fixture-secret',label:'Owned synthetic fixture'}:{runs:[],maxRuns:32}};};
  const client=connectLab({onRun(){},onStatus(){}});
  await new Promise(resolve=>setImmediate(resolve));
  assert.equal(client.status().connected,true);
  assert.equal(element('#lab-start').disabled,false);
  assert.deepEqual(requests.map(r=>r[0]),['/chat/session','/observations/runs']);
  assert.equal(requests[0][1].headers['X-Chat-Session'],'restore');
});

test('manual authentication is serialized so stale responses cannot replace a principal or cookie',async t=>{
  const {element}=browser(t),requests=[],labels=[];
  let resolve;
  const pending=new Promise(done=>resolve=done);
  globalThis.fetch=async(path,options)=>{
    requests.push([path,options]);
    return path==='/chat/session'?pending:{ok:true,json:async()=>({runs:[]})};
  };
  connectLab({onRun(){},onStatus(){},onModel:label=>labels.push(label)});
  element('#lab-token').value='alice';
  const first=element('#lab-connect').submit({preventDefault(){}});
  element('#lab-token').value='bob';
  const second=element('#lab-connect').submit({preventDefault(){}});
  const count=requests.filter(([path])=>path==='/chat/session').length;
  resolve({ok:true,json:async()=>({token:'alice',label:'Alice'})});
  await Promise.all([first,second]);
  assert.equal(count,1,'Only one session handshake may be in flight, including Set-Cookie responses');
  assert.deepEqual(labels,['Alice']);
});

test('initial session restoration cannot race a manual principal switch',async t=>{
  const {element}=browser(t,{hosted:true}),requests=[],labels=[];
  let resolve;
  const restore=new Promise(done=>resolve=done);
  globalThis.fetch=async(path,options)=>{
    requests.push([path,options]);
    if(path==='/chat/session'&&options.headers['X-Chat-Session']==='restore')return restore;
    return {ok:true,json:async()=>path==='/chat/session'?{token:'bob',label:'Bob'}:{runs:[]}};
  };
  connectLab({onRun(){},onStatus(){},onModel:label=>labels.push(label)});
  element('#lab-token').value='bob';
  await element('#lab-connect').submit({preventDefault(){}});
  const count=requests.filter(([path])=>path==='/chat/session').length;
  resolve({ok:true,json:async()=>({token:'alice',label:'Alice'})});
  await new Promise(done=>setImmediate(done));
  assert.equal(count,1,'Restoration must settle before a manual handshake can write another cookie');
  assert.deepEqual(labels,['Alice']);
  element('#lab-token').value='bob';
  await element('#lab-connect').submit({preventDefault(){}});
  assert.deepEqual(labels,['Alice','Bob']);
});

test('a rejected credential exposes reconnect controls and cannot dispatch a message',async t=>{
  const {element,timers}=browser(t);const requests=[];
  globalThis.fetch=async path=>{requests.push(path);return {ok:false,status:401};};
  const client=connectLab({onRun(){},onStatus(){}});
  element('#lab-token').value='rejected-token';await element('#lab-connect').submit({preventDefault(){}});
  await element('#lab-run').submit({preventDefault(){}});
  assert.equal(client.status().connected,false);
  assert.equal(element('#lab-connect').hidden,false);
  assert.equal(element('#lab-start').disabled,true);
  assert.ok(!requests.some(path=>path.endsWith('/messages')));
  assert.equal(timers.size,0);
});

test('authentication lost at the first observation cannot dispatch the message',async t=>{
  const {element,timers}=browser(t);const requests=[];
  globalThis.fetch=async path=>{requests.push(path);return path.endsWith('/observations')?{ok:false,status:401}:
    {ok:true,json:async()=>path==='/conversations'?{sessionId:'owned',revision:'r1'}:path==='/chat/session'?{token:'fixture',label:'Lab'}:{runs:[]}};};
  const client=connectLab({onRun(){},onStatus(){}});
  element('#lab-token').value='fixture';await element('#lab-connect').submit({preventDefault(){}});
  await element('#lab-run').submit({preventDefault(){}});
  assert.equal(client.status().connected,false);assert.equal(timers.size,0);
  assert.equal(requests.filter(path=>path.endsWith('/messages')).length,0);
  assert.equal(client.status().inFlight,false);
});

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
    if(path==='/chat/session')return response({token:'fixture-token',label:'Lab'});
    if(path==='/observations/runs')return response({runs:[]});
    if(path.endsWith('/history'))return response({messages:[]});
    if(path==='/conversations')return response({sessionId:'abc',revision:'r1'});
    if(path.endsWith('/messages')){postRequested.resolve();return post.promise;}
    if(++reads===1)return response(idle);
    if(reads===2){stalePollRequested.resolve();return stalePoll.promise;}
    return response({...idle,elapsed:1,waiting:true});
  };
  const client=connectLab({onRun:feed=>lastFeed=feed,onStatus:()=>{}});
  element('#lab-token').value='fixture-token';await element('#lab-connect').submit({preventDefault(){}});
  element('#lab-message').value='Find players';
  const submitted=element('#lab-run').submit({preventDefault(){}});
  await postRequested.promise;
  const outstandingPoll=[...intervals.values()].at(-1)();await stalePollRequested.promise;
  post.resolve(response({pendingInteraction:{reference:'selection'}}));
  for(let i=0;i<20;i++)await Promise.resolve();
  stalePoll.resolve(response(idle));await Promise.all([submitted,outstandingPoll]);
  assert.equal(client.status().following,true);
  assert.equal(lastFeed.waiting,true,'A fresh, post-settlement observation must win');
  assert.ok(intervals.size>0,'Waiting workflows must remain observable');
});

test('idle monitoring discovers external traffic and keeps watching after completion without POSTing',async t=>{
  const {element,timers}=browser(t,{hosted:true});const requests=[],feeds=[];
  let runs=[];
  globalThis.fetch=async(path,options)=>{
    requests.push([path,options.method||'GET']);
    return {ok:true,json:async()=>path==='/chat/session'?{token:'fixture',label:'Lab'}:
      path==='/observations/runs'?{runs,maxRuns:32}:path.endsWith('/history')?{messages:[]}:
      {runId:path.split('/')[2],active:false,events:[],elapsed:3}};
  };
  const client=connectLab({onRun:feed=>feeds.push(feed),onStatus(){}});
  await new Promise(resolve=>setImmediate(resolve));
  assert.equal(client.status().runId,null);assert.equal(feeds.length,0);
  runs=[{runId:'outside-chat',kind:'conversation',active:false}];
  await [...timers.values()][0]();
  assert.equal(client.status().runId,'outside-chat');assert.equal(feeds.at(-1).runId,'outside-chat');
  assert.ok(timers.size>0,'Discovery survives completed turns');
  runs=[{runId:'outside-workflow',kind:'workflow',active:true},...runs];
  await [...timers.values()][0]();
  assert.ok(requests.some(([path])=>path==='/observations/runs/outside-workflow'));
  assert.equal(client.status().runId,'outside-workflow');
  assert.deepEqual(requests.filter(([,method])=>method==='POST').map(([path])=>path),['/chat/session']);
  assert.equal(element('#lab-start').disabled,false);
});

test('paused replay stays pinned when another run arrives until Follow live is chosen',async t=>{
  const {timers}=browser(t,{hosted:true});
  let runs=[{runId:'one',kind:'conversation'}];
  globalThis.fetch=async path=>({ok:true,json:async()=>path==='/chat/session'?{token:'fixture',label:'Lab'}:
    path==='/observations/runs'?{runs}:path.endsWith('/history')?{messages:[]}:
      {runId:path.split('/')[2],events:[],active:false}});
  const client=connectLab({onRun(){},onStatus(){}});
  await new Promise(resolve=>setImmediate(resolve));
  assert.equal(client.status().runId,'one');
  client.pauseFollowing();
  runs=[{runId:'two',kind:'conversation'},...runs];
  await [...timers.values()][0]();
  assert.equal(client.status().runId,'one');
  assert.equal(client.status().following,false);
  client.follow();
  await new Promise(resolve=>setImmediate(resolve));
  assert.equal(client.status().runId,'two');
  assert.equal(client.status().following,true);
});

test('an explicit demo or selected run is not replaced by background discovery',async t=>{
  const {element,timers}=browser(t,{hosted:true});let runs=[{runId:'one',kind:'conversation'}],emits=0;
  globalThis.fetch=async path=>({ok:true,json:async()=>path==='/chat/session'?{token:'fixture',label:'Lab'}:
    path==='/observations/runs'?{runs}:path.endsWith('/history')?{messages:[]}:{runId:path.split('/')[2],events:[]}});
  const client=connectLab({onRun(){emits++;},onStatus(){}});
  await new Promise(resolve=>setImmediate(resolve));
  client.hide();const before=emits;runs=[{runId:'two',kind:'workflow'},...runs];
  await [...timers.values()][0]();assert.equal(emits,before);
  client.follow();await new Promise(resolve=>setImmediate(resolve));assert.ok(emits>before);
  await element('#lab-runs').change({target:{value:'conversation:one'}});
  await new Promise(resolve=>setImmediate(resolve));assert.equal(client.status().runId,'one');
  await [...timers.values()][0]();assert.equal(client.status().runId,'one');
});
