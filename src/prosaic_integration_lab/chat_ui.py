"""A static, same-origin client for the authenticated public conversation API."""
import base64
import hashlib

from fastapi.responses import HTMLResponse


STYLE = '''
:root{color-scheme:light;font:16px/1.5 system-ui,sans-serif;color:#24312e;background:#f4f5ef}
*{box-sizing:border-box}body{margin:0}button,input,textarea{font:inherit}button{cursor:pointer;border:1px solid #ccd4cb;border-radius:10px;padding:10px 16px;background:white;color:#24312e}button:hover{background:#edf1e9}button:disabled{opacity:.45;cursor:default}
.primary{background:#244e40;color:white;border-color:#244e40}.primary:hover{background:#34614f}main{max-width:960px;margin:auto;padding:26px 24px;height:100dvh;display:flex;flex-direction:column;gap:16px}header{display:flex;align-items:center;justify-content:space-between;gap:12px}h1{font-size:25px;letter-spacing:-1px;margin:0}.eyebrow{font-size:11px;letter-spacing:2px;text-transform:uppercase;color:#63806e}.subtle{color:#66776e;font-size:13px}#connect{display:flex;gap:10px}input{min-width:0;width:100%;border:1px solid #ccd4cb;border-radius:10px;padding:10px;background:white}#messages{flex:1;overflow:auto;min-height:120px;background:#fffef9;border:1px solid #e0e4da;border-radius:18px;padding:24px}.empty{max-width:440px;margin:12vh auto;text-align:center}.empty h2{font-weight:500;font-size:28px;letter-spacing:-1px}.message{margin-bottom:20px;display:flex;flex-direction:column;align-items:flex-start}.message.user{align-items:flex-end}.role{font-size:11px;text-transform:uppercase;letter-spacing:1px;color:#758177;margin:0 5px 6px}.bubble{max-width:85%;white-space:pre-wrap;overflow-wrap:anywhere;background:#edf1e9;border-radius:14px;padding:12px 16px}.user .bubble{background:#244e40;color:white}.tool .bubble{font-size:13px;background:#f2f0e7}.failed{color:#9b3e31;font-size:12px}#interaction{border:1px solid #d3c4a1;border-radius:12px;padding:16px;background:#faf3df}#choices{display:flex;flex-wrap:wrap;gap:8px;margin-top:12px}#composer{display:flex;gap:10px;align-items:flex-end}textarea{resize:none;flex:1;min-height:64px;max-height:160px;padding:14px;border:1px solid #ccd4cb;border-radius:14px;background:white}footer{display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap}.actions{display:flex;gap:8px}#notice{font-size:13px;min-height:20px;color:#744d21}.hidden{display:none!important}#session{font-size:11px;overflow-wrap:anywhere}@media(max-width:600px){main{padding:16px 12px}#messages{padding:16px}header{align-items:flex-start}.bubble{max-width:95%}.actions button{padding:8px}#connect{flex-wrap:wrap}}
'''

SCRIPT = r'''
const $=id=>document.getElementById(id);
let token='',session=null,busy=false,lastRequest=null,createKey=null;
const uuid=()=>crypto.randomUUID();
function notice(text){$('notice').textContent=text;}
function updateControls(){
 $('send').disabled=busy||!session||session.status==='needsResolution';
 $('new').disabled=busy||!token;
 $('refresh').disabled=busy||!session;
 $('recover').disabled=busy||!session;
 $('retry-request').classList.toggle('hidden',!lastRequest);
 for(const button of $('choices').children)button.disabled=busy;
}
function state(value){busy=value;updateControls();}
async function api(path,options={}){
 let response;
 try{response=await fetch(path,{...options,credentials:'same-origin',cache:'no-store',headers:{'Authorization':'Bearer '+token,'Content-Type':'application/json',...options.headers}});}
 catch(error){throw new Error('Connection lost. Refresh status or retry the same request; do not assume it failed.');}
 const data=await response.json().catch(()=>({}));
 if(!response.ok){const detail=data.detail;const code=typeof detail==='string'?detail:detail?.code;const error=new Error(code||'Request failed ('+response.status+').');error.definitiveRejection=[400,401,403,404,413,422].includes(response.status)||(response.status===409&&['revision_conflict','interactionStale','interaction_stale','idempotency_conflict','session_busy','run_busy'].includes(code));throw error;}
 return data;
}
function renderHistory(messages){
 $('messages').replaceChildren();
 if(!messages.length){const welcome=document.createElement('div');welcome.className='empty';const title=document.createElement('h2');title.textContent='What would you like to explore?';const text=document.createElement('p');text.textContent='Talk with the assistant, then try “Find players” to see a workflow that asks for your approval.';welcome.append(title,text);$('messages').append(welcome);}
 for(const entry of messages){const item=document.createElement('article');item.className='message '+entry.role;const role=document.createElement('div');role.className='role';role.textContent=entry.role==='assistant'?'Prosaic':entry.role;const bubble=document.createElement('div');bubble.className='bubble';bubble.textContent=typeof entry.content==='string'?entry.content:Array.isArray(entry.content)?entry.content.map(block=>block.type==='text'?block.text:JSON.stringify(block,null,2)).join('\n'):JSON.stringify(entry.content,null,2);item.append(role,bubble);if(entry.turnStatus==='failed'){const failure=document.createElement('div');failure.className='failed';failure.textContent='Unsuccessful turn · '+(entry.failureCode||'failed');item.append(failure);} $('messages').append(item);}
 $('messages').scrollTop=$('messages').scrollHeight;
}
function renderInteraction(){
 const pending=session?.pendingInteraction;
 $('interaction').classList.toggle('hidden',!pending);$('choices').replaceChildren();
 if(!pending)return;
 $('question').textContent=pending.question||'Your response is needed.';
 for(const [index,choice] of (pending.choices||[]).entries()){
  const button=document.createElement('button');button.textContent=pending.stepId==='select'?(index+1)+'. '+choice:choice;
  if(choice==='approve')button.className='primary';
  button.addEventListener('click',()=>send(pending.stepId==='select'?(index===0?'the first result':'the second result'):choice));
  $('choices').append(button);
 }
}
async function refresh(){
 if(!session)return;
 const id=session.sessionId;
 const current=await api('/conversations/'+id);
 const history=await api('/conversations/'+id+'/history');
 session=current;renderHistory(history.messages||[]);renderInteraction();
 $('session').textContent='Session '+id+' · '+(session.status||'ready');
 try{const usage=await api('/conversations/'+id+'/usage');$('usage').textContent='Conversation: '+(usage.conversation?.total_calls||0)+' calls · Workflow: '+(usage.workflow?.total_calls||0)+' calls';}catch(error){$('usage').textContent='Usage temporarily unavailable';}
 updateControls();
}
async function newConversation(){
 if(busy)return;state(true);notice('Creating conversation…');
 createKey=createKey||uuid();
 try{session=await api('/conversations',{method:'POST',headers:{'Idempotency-Key':createKey},body:'{}'});createKey=null;lastRequest=null;await refresh();notice('Connected. Messages use the configured model.');}
 catch(error){notice(error.message);}finally{state(false);}
}
async function send(text){
 if(busy||!session)return;
 text=typeof text==='string'?text:$('message').value.trim();if(!text)return;
 if(lastRequest){notice('An earlier request is unresolved. Retry that exact request or refresh status first.');return;}
 const body={messageId:uuid(),message:text,expectedRevision:session.revision};
 if(session.pendingInteraction)body.interactionRef=session.pendingInteraction.reference;
 lastRequest={path:'/conversations/'+session.sessionId+'/messages',body};
 await dispatch();
}
async function dispatch(){
 if(!lastRequest||busy)return;state(true);notice('Thinking…');
 try{const request=lastRequest;const reply=await api(request.path,{method:'POST',body:JSON.stringify(request.body)});session=reply;lastRequest=null;$('message').value='';await refresh();notice(reply.failureCode?'Turn failed: '+reply.failureCode:'');}
 catch(error){if(error.definitiveRejection){lastRequest=null;try{await refresh();}catch(refreshError){}notice(error.message+'. This request was rejected; edit your message and send again.');}else{notice(error.message);}}finally{state(false);}
}
$('composer').addEventListener('submit',event=>{event.preventDefault();send();});
$('message').addEventListener('keydown',event=>{if(event.key==='Enter'&&!event.shiftKey){event.preventDefault();send();}});
$('new').addEventListener('click',newConversation);
$('retry-request').addEventListener('click',dispatch);
$('refresh').addEventListener('click',async()=>{state(true);try{await refresh();notice(lastRequest?'Status refreshed. An uncertain request can only be replayed with its original ID.':'Status refreshed.');}catch(error){notice(error.message);}finally{state(false);}});
$('recover').addEventListener('click',async()=>{state(true);try{session=await api('/conversations/'+session.sessionId+'/recover',{method:'POST',body:'{}'});await refresh();notice('Recovery inspected. Uncertain effects require operator resolution.');}catch(error){notice(error.message);}finally{state(false);}});
$('connect').addEventListener('submit',event=>{event.preventDefault();token=$('token').value.trim();$('token').value='';$('connect').classList.add('hidden');newConversation();});
async function bootstrap(){
 const code=new URLSearchParams(location.hash.slice(1)).get('connect');history.replaceState(null,'',location.pathname);
 if(!code){updateControls();return;}
 try{const response=await fetch('/chat/bootstrap',{method:'POST',credentials:'same-origin',headers:{'X-Chat-Launch':code}});if(!response.ok)throw new Error('Launch link expired. Restart the local launcher or connect with an API token.');const data=await response.json();token=data.token;$('model').textContent=data.label;$('connect').classList.add('hidden');await newConversation();}
 catch(error){notice(error.message);}
}
bootstrap();
'''


def response():
    def digest(value):
        return base64.b64encode(hashlib.sha256(value.encode()).digest()).decode()
    page = '''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Prosaic Chat</title>
<style>''' + STYLE + '''</style></head><body><main>
<header><div><div class="eyebrow">Prosaic integration lab</div><h1>Prosaic Chat</h1><div id="model" class="subtle">Authenticated conversation · host-configured model</div></div><button id="new" disabled>New conversation</button></header>
<form id="connect"><input id="token" type="password" autocomplete="off" placeholder="Lab API access token" aria-label="Lab API access token" required><button class="primary">Connect</button></form>
<div id="messages" role="log" aria-label="Conversation history"><div class="empty"><h2>A conversation, with context.</h2><p>Connect to start chatting. Your token stays in browser memory.</p></div></div>
<section id="interaction" class="hidden" aria-label="Workflow interaction"><strong id="question"></strong><div id="choices"></div></section>
<div id="notice" role="status" aria-live="polite"></div>
<form id="composer"><textarea id="message" placeholder="Message the assistant…" aria-label="Message" maxlength="16384" rows="2"></textarea><button id="send" class="primary" disabled>Send</button></form>
<footer><div><div id="usage" class="subtle"></div><div id="session" class="subtle"></div></div><div class="actions"><button id="retry-request" class="hidden">Retry same request</button><button id="refresh" disabled>Refresh</button><button id="recover" disabled>Inspect recovery</button></div></footer>
</main><script>''' + SCRIPT + '''</script></body></html>'''
    return HTMLResponse(page, headers={
        'Cache-Control': 'no-store', 'Referrer-Policy': 'no-referrer',
        'X-Content-Type-Options': 'nosniff',
        'Content-Security-Policy': "default-src 'none'; connect-src 'self'; script-src 'sha256-" + digest(SCRIPT) +
        "'; style-src 'sha256-" + digest(STYLE) + "'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'",
    })
