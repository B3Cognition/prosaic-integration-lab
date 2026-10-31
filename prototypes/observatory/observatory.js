import { RUNS, COMPONENTS, stateAt, usageAt, eventsFor } from './sample-runs.js';
import { createExecutionScene } from './scene-renderer.js';
import { observedRun, formatDuration, reportedTokenText, displayUsage, messagePreview } from './live-model.js';
import { connectLab } from './lab-connection.js';

const $ = selector => document.querySelector(selector);
const $$ = selector => [...document.querySelectorAll(selector)];
const format = value => Number.isFinite(value) ? value.toLocaleString('en-US') : '—';
const gsap = globalThis.gsap;
const motionPreference = matchMedia('(prefers-reduced-motion: reduce)');
let reducedMotion = motionPreference.matches;
let run = RUNS.success, view = 'live', selectedComponent = null, selectedSpan = 'provider-2';
let playing = false, speed = 1, tween = null, graphics = null, currentPhase = '';
let lab = null;
const playhead = { time: reducedMotion ? 15.2 : 0 };

function text(selector, value) { const element = $(selector); if (element.textContent !== String(value)) element.textContent = value; }
function announce(value) { text('#announcement', value); }
function setGraphicsUnavailable(message) {
  selectComponent(null, false);
  $('.scene-shell').classList.add('no-webgl');
  $('#graphics-message').hidden = false;
  $('#graphics-message').classList.add('error');
  text('#graphics-message', message);
  text('#render-mode', 'Timeline available');
  text('#renderer-info', 'Sample timeline · no provider calls');
  $$('.camera-controls button').forEach(button => { button.disabled = true; });
  setView('inspect');
}

function selectComponent(component, focus = true) {
  selectedComponent = component;
  $$('.scene-label').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.component === component)));
  $('#component-card').classList.toggle('is-visible', Boolean(component));
  $('.scene-shell').classList.toggle('is-focused', Boolean(component));
  if (component) {
    const info = component==='tool'&&run.source==='observed'?{...COMPONENTS.tool,name:run.toolName,description:'Host-registered tool observed by Runtime.'}:COMPONENTS[component];
    text('#component-role', info.role); text('#component-name', info.name); text('#component-description', info.description);
    $('#component-card').style.borderTopColor = info.color;
    announce(info.name + ' selected');
  }
  if (focus) graphics?.focus(component);
  render();
}

function setView(next) {
  view = next;
  for (const name of ['live', 'inspect']) {
    $('#' + name + '-tab').setAttribute('aria-selected', String(name === next));
    $('#' + name + '-panel').hidden = name !== next;
  }
  if (next === 'inspect') { lab?.pauseFollowing(); pause(); }
  text('#playback-mode', run.source==='observed'?'Recorded lab run':next === 'live' ? 'Sample replay' : 'Inspect recorded sample');
}

function selectSpan(id, focus = true) {
  const span = run.spans.find(item => item.id === id);
  if (!span) return;
  selectedSpan = id;
  $$('.timeline-span').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.span === id)));
  text('#span-name', span.label);
  const duration = span.endUnknown?'Completion unobserved':span.instant?'Point event':formatDuration(span.end - span.start);
  const detail = span.kind === 'provider' && Number.isFinite(span.inputTokens) ? `${duration} · ${format(span.inputTokens)} input + ${format(span.outputTokens)} output` :
    `${duration}${span.pending?' so far':''} · ${span.httpStatus?'HTTP '+span.httpStatus:span.outcome.replaceAll('_',' ')}${span.kind==='provider'&&run.source==='observed'?' · usage at run level':''}`;
  text('#span-value', detail);
  if (focus) { selectComponent(span.component); seek(span.start); }
}

function buildRecordedView() {
  const focusedSpan=document.activeElement?.dataset?.span;
  text('#run-id', run.id);
  const axisDuration=Math.max(run.duration,.001);
  const duration = run.spans.filter(s => s.kind === 'provider').reduce((total, s) => total + s.end - s.start, 0);
  const observedFinding=run.status==='needs_resolution'?'Execution outcome requires resolution. Inspect the retained evidence before any retry.':run.incomplete?'Trace has missing observations. Only captured spans are shown.':run.status==='waiting'?'Waiting for workflow input. The completed model turn is recorded below.':run.status==='running'?`Run in progress · ${formatDuration(duration)} of provider transport observed.`:run.status==='failed'||run.status==='timed_out'?'Execution failed. Select a span or event to inspect its recorded outcome.':run.spans.length?`Provider transport accounts for ${Math.round(duration / axisDuration * 100)}% of observed elapsed time.`:'No execution observations yet.';
  text('#finding', run.source==='observed'?observedFinding:run.outcome === 'timed_out' ? 'Tool deadline ended the run. No second provider call was started.' : `Provider transport accounts for ${Math.round(duration / axisDuration * 100)}% of elapsed time.`);
  $('#finding').classList.toggle('trace-incomplete',!!run.incomplete);
  text('#duration-total', formatDuration(run.duration)+(run.source==='observed'?' observed':' total'));
  $('#scrubber').max = run.duration;
  const ticks = $('#time-ticks'); ticks.replaceChildren();
  for (let i = 0; i < 5; i++) { const tick = document.createElement('span'); tick.textContent = (run.duration * i / 4).toFixed(i === 0 ? 0 : 1) + (i === 0 || i === 4 ? ' s' : ''); ticks.append(tick); }
  const timeline = $('#timeline'); timeline.replaceChildren();
  for (const component of run.source==='observed'?['harness','runtime','provider','tool']:['lab','harness','runtime','provider','tool']) {
    const lane = document.createElement('div'); lane.className = 'timeline-lane';
    const label = document.createElement('span'); label.textContent = component === 'lab' ? 'Application' : component==='tool'&&run.source==='observed'?'Tools':COMPONENTS[component].name;
    const track = document.createElement('div'); track.className = 'lane-track';
    for (const span of run.spans.filter(item => item.component === component)) {
      const button = document.createElement('button'); button.type = 'button'; button.className = 'timeline-span';
      button.dataset.span = span.id; button.dataset.kind = span.kind;
      button.style.left = span.start / axisDuration * 100 + '%'; button.style.width = (span.end - span.start) / axisDuration * 100 + '%';
      button.setAttribute('aria-label', `${span.label}, ${span.start.toFixed(1)} to ${span.end.toFixed(1)} seconds, ${span.outcome.replaceAll('_', ' ')}`);
      button.classList.toggle('is-error', !['running','completed','waiting','unknown'].includes(span.outcome));
      button.classList.toggle('is-unknown',span.outcome==='unknown');
      button.classList.toggle('is-instant',!!span.instant);
      if (span.end - span.start > axisDuration * .15) button.textContent = span.kind === 'provider' ? run.source==='observed'?span.label:span.id === 'provider-1' ? 'Call 1' : 'Call 2' : span.kind === 'tool' && span.outcome === 'timed_out' ? 'Timeout' : '';
      button.addEventListener('click', () => selectSpan(span.id)); track.append(button);
    }
    const cursor = document.createElement('div'); cursor.className = 'cursor-line'; track.append(cursor);
    lane.append(label, track); timeline.append(lane);
  }
  const usage = displayUsage(usageAt(run)), known=Number.isFinite(usage.input)&&Number.isFinite(usage.output), total = known?usage.input + usage.output:null;
  text('#total-tokens', reportedTokenText(usage)); text('#input-tokens', format(usage.input)); text('#output-tokens', format(usage.output));
  $('#input-bar').style.width = total>0?usage.input / total * 100 + '%':'0%'; $('#output-bar').style.width = total>0?usage.output / total * 100 + '%':'0%';
  $('.usage-bar').setAttribute('aria-label', `${format(usage.input)} input tokens and ${format(usage.output)} output tokens`);
  const events = eventsFor(run), list = $('#events'); list.replaceChildren();
  text('#event-count', events.length + ' events');
  for (const event of events) {
    const li = document.createElement('li'), time = document.createElement('time'), name = document.createElement(event.spanId?'button':'span'), outcome = document.createElement('span');
    if(event.spanId){name.type='button';name.className='event-name';name.addEventListener('click',()=>selectSpan(event.spanId));}
    time.textContent = formatDuration(event.at); name.textContent = event.label; outcome.textContent = event.outcome.replaceAll('_', ' ');
    li.append(time, name, outcome); list.append(li);
  }
  if (!run.spans.some(s => s.id === selectedSpan)) selectedSpan = run.spans.find(s => s.kind === 'provider')?.id;
  selectSpan(selectedSpan, false);
  if(!selectedSpan){text('#span-name','No span selected');text('#span-value','Awaiting observations');}
  if(focusedSpan)$(`.timeline-span[data-span="${focusedSpan}"]`)?.focus({preventScroll:true});
  const toolButton=$('.scene-label[data-component="tool"]');
  toolButton.childNodes[1].textContent=run.source==='observed'?run.toolName:'read_file';
  text('.sample-tag',run.source==='observed'?'Lab observations':'Sample telemetry');
  text('label[for="scenario"]','Run source');
  text('.inspect-heading .eyebrow',run.source==='observed'?'Recorded lab run':'Recorded sample');
  text('.scene-footer>span:last-child',run.source==='observed'?'Illustrative geometry / observed activity':'Illustrative geometry / sample activity');
  text('.usage-detail p',run.source==='observed'?usage.available===false?'Recorder data unavailable. Token usage is unknown.':usage.unqualified?`† Provider-reported counts include ${usage.unqualifiedCalls} unsupported usage report(s). Accounting remains unqualified.${usage.unknownCalls?' Additional calls have unknown usage.':''} Latest totals, independent of replay.`:usage.unknownCalls?`${usage.completeCalls} completed reports; ${usage.unknownCalls} unresolved. Totals are the known subtotal.`:'Latest recorder totals, independent of replay position.':'Complete sample reports. Independent of playback position.');
}

for (const selector of ['#provider-strip', '#tool-strip']) for (let i = 0; i < 27; i++) $(selector).append(document.createElement('i'));

function render() {
  const state = stateAt(run, playhead.time), active = state.active?.component;
  const providerActive = active === 'provider', toolActive = active === 'tool';
  text('#phase', (run.source==='observed'?'Lab events / ':state.done ? 'Sample ended / ' : 'Sample replay / ') + state.label);
  $('#status-light').style.background = state.toolFailed||state.providerFailed||['failed','timed_out'].includes(state.outcome) ? 'var(--red)' : state.done ? 'var(--muted)' : 'var(--teal)';
  text('#clock', run.source==='observed'&&lab?.status().following?formatDuration(state.time)+' elapsed':`${state.time.toFixed(1)} / ${run.duration.toFixed(1)} s`);
  $('#scrubber').value = state.time; $('#scrubber').style.setProperty('--progress', state.time / Math.max(run.duration,.001) * 100 + '%');
  text('#elapsed', state.time<1?Math.round(state.time*1000):state.time.toFixed(1)); const unit = document.createElement('small'); unit.textContent = state.time<1?'ms':'s'; $('#elapsed').append(unit);
  text('#calls', state.calls); text('#tokens',reportedTokenText(state.reports));
  text('#usage-note',run.source==='observed'?state.reports.available===false?'Recorder unavailable':state.reports.providerReported?'† Provider counts · accounting unqualified':state.reports.unknownCalls?'Known reports · unresolved calls remain':'Latest recorder totals':state.reports.input ? 'Completed provider reports' : 'No completed usage report');
  text('#live-title', state.label);
  const past = eventsFor(run).filter(e => e.at <= state.time), latest = past[past.length - 1];
  text('#latest-event', latest ? latest.label + (latest.outcome === 'timed_out' ? ' · timed out' : '') : 'Waiting for sample start');
  const outcomeLabels={completed:'Completed',waiting:'Waiting',failed:'Failed',timed_out:'Timed out',needs_resolution:'Resolve',ready:'Ready',running:'Running'};
  text('#run-outcome',outcomeLabels[state.outcome]||state.outcome);
  $('#run-outcome').classList.toggle('is-error', state.toolFailed||state.providerFailed||['failed','timed_out'].includes(state.outcome));
  text('#play-icon', playing ? 'Ⅱ' : state.done ? '↺' : '▶');
  $('#play').setAttribute('aria-label', playing ? 'Pause playback' : state.done ? 'Replay recorded run' : 'Play recorded run');
  $$('.cursor-line').forEach(line => { line.style.left = Math.min(99.9, state.time / Math.max(run.duration,.001) * 100) + '%'; });
  for (const [selector, activeNow] of [['#provider-strip', providerActive], ['#tool-strip', toolActive]]) {
    [...$(selector).children].forEach((mark, i) => {
      mark.classList.toggle('is-on', activeNow);
      mark.style.height = (activeNow ? 5 + (Math.sin(i * 1.7 + state.time * (reducedMotion ? 0 : 4)) + 1) * 9 : 3) + 'px';
    });
  }
  if (selectedComponent) {
    const componentSpans = run.spans.filter(s => s.component === selectedComponent), last = componentSpans.filter(s => s.end <= state.time).at(-1);
    const status = selectedComponent === 'runtime' ? state.done ? run.outcome.replaceAll('_', ' ') : active&&['runtime','provider','tool'].includes(active) ? 'Active invocation' : 'Ready' : active === selectedComponent ? 'Active' : last ? last.outcome.replaceAll('_', ' ') : 'Ready';
    text('#component-state', status);
  }
  const phaseKey = state.active?.id || state.outcome;
  if (phaseKey !== currentPhase) { currentPhase = phaseKey; announce(state.label); }
  graphics?.update(state, playing);
}

function pause() { tween?.kill(); tween = null; playing = false; render(); }
function seek(value) { lab?.pauseFollowing(); pause(); playhead.time = Math.max(0, Math.min(run.duration, value)); render(); }
function play() {
  if (!gsap) { announce('Animation library unavailable. Use the timeline to inspect the sample.'); return; }
  if (playhead.time >= run.duration) playhead.time = 0;
  tween?.kill(); playing = true; render();
  tween = gsap.to(playhead, { time: run.duration, duration: run.duration - playhead.time, ease: 'none', onUpdate: render,
    onComplete() { playing = false; tween = null; render(); announce(run.outcome === 'completed' ? 'Sample run completed' : 'Sample run timed out'); },
  });
  tween.timeScale(speed);
}

$('#play').addEventListener('click', () => {lab?.pauseFollowing();playing ? pause() : play();});
$('#scrubber').addEventListener('input', event => { const time = Number(event.target.value); seek(time); });
$('#speed').addEventListener('click', () => { const speeds = [.5, 1, 2]; speed = speeds[(speeds.indexOf(speed) + 1) % speeds.length]; text('#speed', speed + '×'); tween?.timeScale(speed); });
$('#scenario').addEventListener('change', event => {if(event.target.value==='observed'){lab?.follow();return;}lab?.hide();pause();run=RUNS[event.target.value];playhead.time=0;currentPhase='';selectComponent(null);buildRecordedView();render();if(!reducedMotion&&view==='live')play();});
for (const name of ['live', 'inspect']) $('#' + name + '-tab').addEventListener('click', () => setView(name));
$('.view-tabs').addEventListener('keydown', event => {
  if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
  const current = event.target.closest('[role="tab"]')?.id === 'inspect-tab' ? 'inspect' : 'live';
  event.preventDefault(); const next = event.key === 'Home' ? 'live' : event.key === 'End' ? 'inspect' : current === 'live' ? 'inspect' : 'live';
  setView(next); $('#' + next + '-tab').focus();
});
$$('.scene-label').forEach(button => button.addEventListener('click', () => selectComponent(button.dataset.component)));
$('#close-focus').addEventListener('click', () => { const previous = selectedComponent; selectComponent(null); if (previous) $(`.scene-label[data-component="${previous}"]`)?.focus(); });
$('#reset-camera').addEventListener('click', () => selectComponent(null));
for (const [id, layout] of [['section-view', 'section'], ['explode-view', 'exploded']]) $('#' + id).addEventListener('click', () => {
  $('#section-view').setAttribute('aria-pressed', String(layout === 'section')); $('#explode-view').setAttribute('aria-pressed', String(layout === 'exploded')); graphics?.setLayout(layout);
});
document.addEventListener('keydown', event => { if (event.key === 'Escape' && selectedComponent) { selectComponent(null); $('#reset-camera').focus(); } });
document.addEventListener('visibilitychange', () => { if (document.hidden) pause(); });
motionPreference.addEventListener('change', () => { reducedMotion = motionPreference.matches; if (reducedMotion) pause(); graphics?.setReducedMotion(reducedMotion); announce(reducedMotion ? 'Reduced motion enabled. Sample paused.' : 'Motion enabled.'); });
$('#scene').addEventListener('graphicslost', () => { pause(); graphics?.dispose(); graphics = null; setGraphicsUnavailable('The 3D graphics context was lost. Timing, usage and sample replay remain available below. Reload to restore 3D.'); });

buildRecordedView(); render();
try {
  graphics = createExecutionScene($('#scene'), { onSelect: selectComponent, labels: $$('.scene-label'), reducedMotion });
  $('#scene-labels').hidden = false;
  $('#graphics-message').hidden = true;
  render();
  if (!reducedMotion) play();
} catch (error) {
  console.warn('Observatory graphics unavailable:', error.message);
  setGraphicsUnavailable('3D rendering needs WebGL 2. You can still explore every timing span, token report and event below.');
}
lab=connectLab({onStatus:message=>text('#lab-status',message),onModel:label=>{
  text('#lab-model',label);
  if(label.startsWith('Local Qwen')&&$('#lab-message').value==='Find players')$('#lab-message').value='Reply with exactly one word: Ready. /no_think';
},onMessages:messages=>{
  const list=$('#lab-messages');list.replaceChildren();
  $('#lab-exchange').hidden=messages!==null&&!messages.length;
  if(messages===null){list.textContent='Message history unavailable. The execution was not repeated.';return;}
  for(const message of messagePreview(messages)){
    const item=document.createElement('article'),role=document.createElement('strong'),body=document.createElement('p');
    role.textContent=message.role==='user'?'User → Runtime → Provider':'Provider → Runtime → Assistant';
    body.textContent=message.text;item.append(role,body);list.append(item);
  }
},onRun:(feed,options)=>{
  const previous=playhead.time,newRun=feed.runId!==run.id,previousTool=run.toolName;
  if(newRun&&options.following)setView('live');
  run=observedRun(feed,options);
  if(newRun)selectComponent(null);
  else if(selectedComponent==='tool'&&previousTool!==run.toolName)selectComponent('tool',false);
  if(!$('#scenario option[value="observed"]')){const option=document.createElement('option');option.value='observed';option.textContent='Actual lab execution';$('#scenario').append(option);}
  $('#scenario').value='observed';
  if(options.following){tween?.kill();tween=null;playhead.time=run.duration;playing=run.status==='running'&&!reducedMotion&&view==='live';}
  else playhead.time=Math.min(previous,run.duration);
  buildRecordedView();render();
  text('#playback-mode',options.following&&run.status==='running'?'Following lab execution':'Recorded lab run');
  text('#renderer-info','Three.js + GSAP · actual Lab SDK observations');
}});
// Diagnostic surface for prototype verification, never a lab API.
Object.defineProperty(window, 'prosaicObservatory', { value: Object.freeze({
  snapshot: () => ({ runId: run.id, source:run.source||'sample',view, playing, time: playhead.time, selectedComponent, selectedSpan, state: stateAt(run, playhead.time), usage: usageAt(run),lab:lab?.status(),events:eventsFor(run),incomplete:!!run.incomplete,graphics: graphics?.info() || null }),
}), writable: false });
