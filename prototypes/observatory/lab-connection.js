// Same-origin Lab client. The fixture API credential lives only in this closure.
export function connectLab({onRun,onStatus,onMessages=()=>{},onModel=()=>{}}) {
  const $=selector=>document.querySelector(selector);
  let token='',context=null,timer=null,generation=0;
  const hosted=location.pathname.startsWith('/observatory/');
  async function api(path,options={}) {
    const response=await fetch(path,{...options,credentials:'same-origin',cache:'no-store',
      headers:{'Content-Type':'application/json','Authorization':'Bearer '+token,...options.headers}});
    if(!response.ok)throw Error('Lab request returned HTTP '+response.status+'.');
    return response.json();
  }
  function emit() {
    if(context?.feed&&context.visible)onRun(context.feed,{following:context.following,requestPending:context.inFlight});
  }
  async function poll(current,afterSettlement=false) {
    if(current!==context)return;
    if(current.polling){if(afterSettlement){await current.pollingDone;return poll(current,true);}return;}
    current.polling=true;
    let finished;
    current.pollingDone=new Promise(resolve=>finished=resolve);
    const settlement=current.settlement;
    try {
      const feed=await api('/conversations/'+current.id+'/observations');
      if(current!==context||settlement!==current.settlement)return;
      current.feed=feed;emit();
      const cadence=current.inFlight||feed.active?500:2000;
      if(current.cadence!==cadence){clearInterval(timer);current.cadence=cadence;timer=setInterval(()=>poll(current),cadence);}
      if(!current.inFlight&&!feed.active&&!feed.waiting)clearInterval(timer);
    } catch(error) {
      if(current!==context||settlement!==current.settlement)return;
      current.following=false;
      onStatus('Trace update unavailable. Retained history is still available; no request was repeated.');
    } finally {current.polling=false;finished();}
  }
  async function start(event) {
    event.preventDefault();
    if(!token||context?.inFlight)return;
    clearInterval(timer);generation++;
    const own=generation;
    $('#lab-start').disabled=true;
    onMessages([]);
    onStatus('Creating an owned lab conversation…');
    try {
      const session=await api('/conversations',{method:'POST',headers:{'Idempotency-Key':'observatory-'+crypto.randomUUID()},body:'{}'});
      if(own!==generation)return;
      context={id:session.sessionId,inFlight:true,settling:false,settlement:0,following:true,visible:true,polling:false,cadence:500,
        feed:{runId:session.sessionId,elapsed:0,active:false,events:[],usage:{input:null,output:null,available:false}}};
      emit();
      timer=setInterval(()=>poll(context),500);
      await poll(context);
      onStatus('Lab request running. The page follows actual Runtime observations.');
      const reply=await api('/conversations/'+session.sessionId+'/messages',{method:'POST',body:JSON.stringify({
        messageId:'observatory-'+crypto.randomUUID(),message:$('#lab-message').value.trim(),expectedRevision:session.revision})});
      context.inFlight=false;context.settling=true;context.settlement++;
      await poll(context,true);
      await readMessages(context);
      onStatus(reply.status==='needsResolution'?'Execution outcome requires resolution. Inspect the retained trace.':reply.pendingInteraction?'Waiting for workflow input.':reply.failureCode?'Turn failed: '+reply.failureCode:'Lab turn completed.');
    } catch(error) {
      if(context){context.inFlight=false;context.settling=true;context.settlement++;}
      onStatus(error.message+' Inspect the retained trace before deciding what to do next.');
      if(context)await poll(context,true);
    } finally {if(context)context.settling=false;$('#lab-start').disabled=!token;}
  }
  async function readMessages(current) {
    try {
      const history=await api('/conversations/'+current.id+'/history');
      if(current===context)onMessages(history.messages||[]);
    } catch(error) {if(current===context)onMessages(null);}
  }
  function connected(label) {
    $('#lab-connect').hidden=true;$('#lab-run').hidden=false;
    $('#lab-start').disabled=false;onModel(label);onStatus('Connected · '+label);
  }
  $('#lab-run').addEventListener('submit',start);
  $('#lab-connect').addEventListener('submit',event=>{
    event.preventDefault();token=$('#lab-token').value.trim();$('#lab-token').value='';
    if(token)connected('Lab API credential in browser memory');
  });
  $('#lab-follow').addEventListener('click',()=>{if(context){context.following=true;context.visible=true;emit();}});
  async function bootstrap() {
    if(!hosted)return;
    $('#lab-controls').hidden=false;
    const code=new URLSearchParams(location.hash.slice(1)).get('connect');
    history.replaceState(null,'',location.pathname);
    if(!code){onStatus('Connect with the lab launch link or a lab API token.');return;}
    try {
      const response=await fetch('/chat/bootstrap',{method:'POST',credentials:'same-origin',headers:{'X-Chat-Launch':code}});
      if(!response.ok)throw Error('Launch link expired or already used.');
      const result=await response.json();token=result.token;connected(result.label);
    } catch(error){onStatus(error.message+' Use a fresh launch link or connect below.');}
  }
  bootstrap();
  return {pauseFollowing(){if(context)context.following=false;},
    hide(){if(context){context.visible=false;context.following=false;}},
    follow(){if(context){context.visible=true;context.following=true;emit();}},
    status:()=>({connected:!!token,inFlight:!!(context?.inFlight||context?.settling),following:!!context?.following,runId:context?.id||null}),
  };
}
