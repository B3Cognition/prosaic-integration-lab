import { generationAt } from './generation-model.js';
import { displayUsage, reportedOutputText } from './live-model.js';
import { usageAt } from './sample-runs.js';

const number = n => Number.isFinite(n) ? n.toLocaleString('en-US') : '—';
const seconds = n => Number.isFinite(n) ? n < 1 ? Math.round(n*1000)+' ms' : n.toFixed(2)+' s' : '—';

export function createGenerationView(root, onSelect) {
  const $ = selector => root.querySelector(selector);
  const put = (selector,value) => { const node=$(selector);if(node.textContent!==String(value))node.textContent=value; };
  const select=$('#generation-call');
  select.addEventListener('change',()=>onSelect(select.value || null));
  let callKey='',frameKey='';

  function plot(model,time) {
    const svg=$('#generation-chart'),width=Math.max(300,svg.clientWidth || 420);
    svg.setAttribute('viewBox',`0 0 ${width} 166`);
    const left=44,top=25,height=96,right=width-14,span=right-left;
    const max=model.call?.characters || 0;
    const unit=Math.max(5,10**Math.floor(Math.log10(Math.max(1,max))));
    const ceiling=Math.max(10,Math.ceil(max/unit)*unit);
    const duration=model.duration || 1,start=model.call?.start || 0;
    const x=t=>left+Math.min(1,Math.max(0,(t-start)/duration))*span;
    const y=n=>top+height-Math.min(1,n/ceiling)*height;
    $('#generation-grid').setAttribute('d',[0,.5,1].map(f=>`M${left},${top+height*f}H${right}`).join(''));
    for (const [index,value] of [ceiling,ceiling/2,0].entries()) {
      const label=$('#generation-y'+index);label.setAttribute('x',left-9);label.setAttribute('y',top+index*height/2+4);label.textContent=number(value);
    }
    for (let i=0;i<3;i++) {
      const label=$('#generation-x'+i);label.setAttribute('x',left+span*i/2);label.textContent=(duration*i/2).toFixed(1)+' s';
    }
    $('#generation-x0').setAttribute('text-anchor','start');$('#generation-x2').setAttribute('text-anchor','end');
    const cursor=x(time),first=model.call?.firstOutputAt;
    const waiting=$('#generation-wait');waiting.setAttribute('x',left);waiting.setAttribute('y',top);
    waiting.setAttribute('height',height);waiting.setAttribute('width',Math.max(0,x(Math.min(time,first ?? time))-left));
    let d=`M${left},${y(0)}`;
    for(const point of model.arrivals)d+=`H${x(point.at).toFixed(2)}V${y(point.totalCharacters).toFixed(2)}`;
    if(model.unknownInterval) {
      if(model.tail)d+=`M${x(model.tail.at)},${y(model.tail.totalCharacters)}H${cursor.toFixed(2)}`;
    } else d+=`H${cursor.toFixed(2)}`;
    $('#generation-curve').setAttribute('d',model.call?d:'');
    const unknown=$('#generation-unknown');
    unknown.setAttribute('x',model.unknownInterval?x(model.unknownInterval.start):left);
    unknown.setAttribute('width',model.unknownInterval?x(model.unknownInterval.end)-x(model.unknownInterval.start):0);
    unknown.setAttribute('y',top);unknown.setAttribute('height',height);
    const tail=$('#generation-tail');tail.setAttribute('visibility',model.tail?'visible':'hidden');
    if(model.tail){tail.setAttribute('cx',x(model.tail.at));tail.setAttribute('cy',y(model.tail.totalCharacters));}
    $('#generation-arrivals').setAttribute('d',model.arrivals.map(p=>
      `M${x(p.at).toFixed(2)},128v${Math.min(12,4+Math.log2(1+p.characters)*2).toFixed(1)}`).join(''));
    $('#generation-cursor').setAttribute('d',model.call?`M${cursor},${top}V142`:'');
    put('#generation-chart-title',model.call?`${number(model.characters)} characters in ${number(model.chunks)} output chunks. Client-observed arrival timings.`:'No generation observations.');
  }

  let lastRender;
  const view={render(run,time,preferred,playing,reducedMotion) {
    lastRender=[run,time,preferred,playing,reducedMotion];
    const model=generationAt(run,time,preferred),call=model.call;
    const nextCallKey=model.calls.map(c=>c.spanId).join('|');
    if(nextCallKey!==callKey) {
      callKey=nextCallKey;select.replaceChildren();
      const automatic=document.createElement('option');automatic.value='';automatic.textContent='Follow latest call';select.append(automatic);
      model.calls.forEach((c,i)=>{const option=document.createElement('option');option.value=c.spanId;option.textContent='Provider call '+(i+1);select.append(option);});
    }
    select.value=preferred && model.calls.some(c=>c.spanId===preferred)?preferred:'';
    const nextFrame=[run.id,call?.spanId,model.chunks,model.phase,Math.floor(time*10),playing,reducedMotion,preferred].join('|');
    if(frameKey===nextFrame)return model;frameKey=nextFrame;
    root.dataset.phase=model.phase;root.dataset.motion=playing&&!reducedMotion?'on':'off';
    const phases={empty:'Awaiting a provider call',queued:'Provider call not started',waiting:'Waiting for first output',generating:'Output is arriving',complete:'Output stream finished',interrupted:'Stream interrupted',unavailable:'Generation timing unavailable'};
    put('#generation-state',!playing&&model.phase==='generating'?'Paused at recorded output':phases[model.phase]);
    put('#generation-source',run.source==='observed'?'Observed output':'Scripted sample');
    put('#generation-first',seconds(model.firstOutput));
    put('#generation-count',(model.partial?'≥':'')+number(model.chunks));
    put('#generation-gap',seconds(model.largestGap));
    const usage=displayUsage(usageAt(run));
    put('#generation-tokens',reportedOutputText(usage));
    put('#generation-token-scope',usage.available===false?'Unavailable':usage.unknownCalls?'Known subtotal':'Reported total');
    put('#generation-age',model.phase==='generating'&&model.sinceLastOutput>.5?
      seconds(model.sinceLastOutput)+' since the last output':model.phase==='waiting'?
      seconds(model.elapsed)+' elapsed · includes transport and model work':
      model.phase==='unavailable'?'The provider returned no visible text stream.':
      !playing&&model.phase==='generating'?'Playback paused':call?'Arrival marks follow the recorded timing.':'Run a lab test or play the sample.');
    const ribbon=$('#generation-ribbon');ribbon.replaceChildren();
    const preview=Array.from(call?.preview || '');
    for(const sample of model.arrivals.slice(-18)) {
      const mark=document.createElement('span');mark.className='generation-chunk';
      const piece=preview.slice(sample.totalCharacters-sample.characters,sample.totalCharacters).join('');
      mark.textContent=piece?piece.replaceAll('\n','↵').replaceAll(' ','␠'):'+'+sample.characters;
      mark.title=`Chunk ${sample.index} · ${seconds(sample.at-call.start)} · ${sample.characters} characters`;
      mark.classList.toggle('is-fresh',playing&&!reducedMotion&&time-sample.at<.65);
      ribbon.append(mark);
    }
    if(!model.arrivals.length){const empty=document.createElement('span');empty.className='generation-empty';empty.textContent=model.phase==='waiting'?'No output has arrived yet.':'Output chunks appear here.';ribbon.append(empty);}
    const output=$('#generation-preview');
    const atBottom=output.scrollHeight-output.scrollTop-output.clientHeight<6;
    put('#generation-preview',model.preview || '');
    output.hidden=!model.preview;
    if(playing&&atBottom)output.scrollTop=output.scrollHeight;
    put('#generation-evidence',model.uncorrelated?'Some output could not be safely attributed. Only identified chunks are shown.':
      model.truncated?'Capture limit reached. Counts remain cumulative; hatched timing intervals are unknown.':
      model.phase==='interrupted'?'Partial output is provisional. Completion was not confirmed.':
      'Provisional text · committed messages remain in conversation history.');
    plot(model,time);
    return model;
  }};
  const resize=new ResizeObserver(()=>{frameKey='';if(lastRender)view.render(...lastRender);});
  resize.observe(root);
  return view;
}
