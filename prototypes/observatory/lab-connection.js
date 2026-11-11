// Same-origin Lab client. The fixture API credential lives only in this closure.
export function connectLab({onRun,onStatus,onMessages=()=>{},onModel=()=>{},onConnection=()=>{},onRuns=()=>{},onFreshness=()=>{}}) {
  const $=selector=>document.querySelector(selector);
  let token='',context=null,timer=null,discoveryTimer=null,generation=0,discovering=false;
  let visible=true,followLatest=true,runs=[],starting=false,authenticating=false;
  const hosted=location.pathname.startsWith('/observatory/');
  function disconnected() {
    token='';generation++;clearInterval(timer);clearInterval(discoveryTimer);context=null;runs=[];
    $('#lab-start').disabled=true;$('#lab-run').hidden=true;$('#lab-connect').hidden=false;
    onRuns([]);onMessages([]);onConnection(false);
    onStatus('Disconnected. Use this Lab instance’s API token or a fresh launcher link.');
  }
  async function api(path,options={}) {
    const own=generation;
    const response=await fetch(path,{...options,credentials:'same-origin',cache:'no-store',
      headers:{'Content-Type':'application/json','Authorization':'Bearer '+token,...options.headers}});
    if(!response.ok){
      const error=Error(response.status===401?'Lab connection rejected. Use a Lab API token, not an oMLX/provider key, or a fresh launcher link.':'Lab request returned HTTP '+response.status+'.');
      error.authentication=response.status===401;
      if(error.authentication&&own===generation)disconnected();
      throw error;
    }
    return response.json();
  }
  function emit() {
    if(context?.feed&&visible)onRun(context.feed,{following:context.following,requestPending:context.inFlight});
  }
  async function choose(item) {
    if(starting||context?.inFlight)return;
    if(!item)return;
    clearInterval(timer);onMessages([]);
    context={id:item.runId,kind:item.kind,inFlight:false,settlement:0,following:true,polling:false};
    await poll(context);
    if(context?.kind==='conversation')await readMessages(context);
  }
  async function discover() {
    if(!token||discovering)return;
    discovering=true;const own=generation;
    try {
      const result=await api('/observations/runs');
      if(own!==generation)return;
      runs=result.runs||[];onRuns(runs);onFreshness({ok:true,at:Date.now(),count:runs.length,maxRuns:result.maxRuns});
      if(starting||context?.inFlight)return;
      const latest=runs[0];
      if(followLatest&&latest&&latest.runId!==context?.id)await choose(latest);
      else if(context)await poll(context);
    } catch(error) {
      if(own!==generation)return;
      onFreshness({ok:false});onStatus(error.message+' Monitoring will reconnect automatically; no run was dispatched.');
    } finally {discovering=false;}
  }
  async function poll(current,afterSettlement=false) {
    if(current!==context)return;
    if(current.polling){if(afterSettlement){await current.pollingDone;return poll(current,true);}return;}
    current.polling=true;
    let finished;
    current.pollingDone=new Promise(resolve=>finished=resolve);
    const settlement=current.settlement;
    try {
      const feed=await api(current.kind==='workflow'?'/observations/runs/'+current.id:'/conversations/'+current.id+'/observations');
      if(current!==context||settlement!==current.settlement)return;
      current.feed=feed;emit();
      if(!feed.active&&!current.inFlight&&current.kind==='conversation')await readMessages(current);
      const cadence=current.inFlight||feed.active?500:2000;
      if(current.cadence!==cadence){clearInterval(timer);current.cadence=cadence;timer=setInterval(()=>poll(current),cadence);}
      if(!current.inFlight&&!feed.active&&!feed.waiting)clearInterval(timer);
    } catch(error) {
      if(current!==context||settlement!==current.settlement)return;
      onFreshness({ok:false});
      onStatus(error.authentication?error.message:'Trace update unavailable. Retained history is still available; no request was repeated.');
    } finally {current.polling=false;finished();}
  }
  async function start(event) {
    event.preventDefault();
    if(!token||starting||context?.inFlight)return;
    starting=true;
    clearInterval(timer);context=null;visible=true;followLatest=true;
    const own=generation;
    $('#lab-start').disabled=true;
    onMessages([]);
    onStatus('Creating an owned lab conversation…');
    try {
      const session=await api('/conversations',{method:'POST',headers:{'Idempotency-Key':'observatory-'+crypto.randomUUID()},body:'{}'});
      if(own!==generation)return;
      context={id:session.sessionId,kind:'conversation',inFlight:true,settling:false,settlement:0,following:true,polling:false,cadence:500,
        feed:{runId:session.sessionId,elapsed:0,active:false,events:[],usage:{input:null,output:null,available:false}}};
      emit();
      timer=setInterval(()=>poll(context),500);
      await poll(context);
      if(!token)return;
      onStatus('Lab request running. The page follows actual Runtime observations.');
      const reply=await api('/conversations/'+session.sessionId+'/messages',{method:'POST',body:JSON.stringify({
        messageId:'observatory-'+crypto.randomUUID(),message:$('#lab-message').value.trim(),expectedRevision:session.revision})});
      context.inFlight=false;context.settling=true;context.settlement++;
      await poll(context,true);
      await readMessages(context);
      if(token)onStatus(reply.status==='needsResolution'?'Execution outcome requires resolution. Inspect the retained trace.':reply.pendingInteraction?'Waiting for workflow input.':reply.failureCode?'Turn failed: '+reply.failureCode:'Lab turn completed.');
    } catch(error) {
      if(context){context.inFlight=false;context.settling=true;context.settlement++;}
      onStatus(error.message+(error.authentication?' No request was repeated.':' Inspect the retained trace before deciding what to do next.'));
      if(context&&token)await poll(context,true);
    } finally {starting=false;if(context){context.inFlight=false;context.settling=false;}$('#lab-start').disabled=!token;}
  }
  async function readMessages(current) {
    try {
      const history=await api('/conversations/'+current.id+'/history');
      if(current===context)onMessages(history.messages||[]);
    } catch(error) {if(current===context)onMessages(null);}
  }
  function connected(label) {
    $('#lab-connect').hidden=true;$('#lab-run').hidden=false;
    $('#lab-start').disabled=false;onModel(label);onConnection(true);onStatus('Connected · monitoring your Lab runs, including Chat and API traffic.');
    clearInterval(discoveryTimer);discoveryTimer=setInterval(discover,2000);discover();
  }
  $('#lab-run').addEventListener('submit',start);
  $('#lab-connect').addEventListener('submit',async event=>{
    event.preventDefault();if(authenticating||starting||context?.inFlight)return;
    const candidate=$('#lab-token').value.trim();$('#lab-token').value='';
    if(!candidate)return;
    disconnected();
    const own=generation;authenticating=true;$('#lab-connect button').disabled=true;
    onStatus('Verifying Lab credential…');
    try{
      const response=await fetch('/chat/session',{method:'POST',credentials:'same-origin',cache:'no-store',
        headers:{'X-Chat-Session':'connect','Authorization':'Bearer '+candidate}});
      if(!response.ok)throw Error('Lab connection rejected. Enter the Lab API token from this launcher’s chat-service.json, not your oMLX/provider key.');
      const result=await response.json();if(own!==generation)return;
      token=result.token;context=null;connected(result.label);}
    catch(error){if(own===generation)onStatus(error.message);}
    finally{authenticating=false;$('#lab-connect button').disabled=false;}
  });
  function follow(){visible=true;followLatest=true;onRuns(runs);if(context){context.following=true;emit();}discover();}
  $('#lab-follow').addEventListener('click',follow);
  $('#lab-runs').addEventListener('change',event=>{
    visible=true;followLatest=event.target.value==='latest';
    if(followLatest){follow();return;}
    choose(runs.find(item=>item.kind+':'+item.runId===event.target.value));
  });
  async function bootstrap() {
    if(!hosted)return;
    const own=generation;authenticating=true;$('#lab-connect button').disabled=true;
    $('#lab-controls').hidden=false;
    const code=new URLSearchParams(location.hash.slice(1)).get('connect');
    history.replaceState(null,'',location.pathname);
    try {
      const response=await fetch(code?'/chat/bootstrap':'/chat/session',{method:'POST',credentials:'same-origin',
        headers:code?{'X-Chat-Launch':code}:{'X-Chat-Session':'restore'}});
      if(!response.ok)throw Error(code?'Launch link expired or already used.':'No active launcher session.');
      const result=await response.json();if(own!==generation)return;
      token=result.token;connected(result.label);
    } catch(error){if(own===generation)onStatus(error.message+' Use a fresh launch link or connect below.');}
    finally{authenticating=false;$('#lab-connect button').disabled=false;}
  }
  bootstrap();
  return {pauseFollowing(){followLatest=false;if(context)context.following=false;onRuns(runs);},
    hide(){visible=false;if(context)context.following=false;},
    follow,
    status:()=>({connected:!!token,inFlight:!!(starting||context?.inFlight||context?.settling),following:!!context?.following,followLatest,selected:context?context.kind+':'+context.id:null,runId:context?.id||null}),
  };
}
