import { createReferenceLab, createLiveReference, createLiveTransport } from '../../src/reference-algorithms/index.js';
import { digestOf } from '../../src/lab/lab.js';
import { composePage, fetchPageSources } from '../../pyto/viewer/embed.mjs';
import { downloadJson } from '../../src/media.js';
const $=selector=>document.querySelector(selector), runsElement=$('#runs'),status=$('#status');
const cards=[],lab=createReferenceLab();let viewerSources;
const escapeHtml=value=>String(value).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const title=kind=>({tree:'Decision tree',perceptron:'Perceptron',transformer:'Tiny transformer block'}[kind]);
const number=(form,key)=>{const raw=String(new FormData(form).get(key)??'').trim();if(!raw||!Number.isFinite(Number(raw)))throw Error(`${key} must be a finite number.`);return Number(raw);};
const numericList=(text,label)=>{const cells=String(text).trim().split(',').map(v=>v.trim());if(cells.some(v=>!v))throw Error(`${label}: no blank entries.`);const values=cells.map(Number);if(values.some(v=>!Number.isFinite(v)))throw Error(`${label} needs finite numbers.`);return values;};
function optionsFor(kind,form){
 if(kind==='tree')return {value:number(form,'value'),parameters:{rootThreshold:number(form,'rootThreshold'),branchThreshold:number(form,'branchThreshold')}};
 if(kind==='perceptron')return {features:numericList(new FormData(form).get('features'),'Features'),weights:numericList(new FormData(form).get('weights'),'Weights'),bias:number(form,'bias'),threshold:number(form,'threshold')};
 const rows=String(new FormData(form).get('input')).split(';').map(row=>numericList(row,'Token rows'));
 return {input:rows,parameters:{epsilon:number(form,'epsilon')}};
}
const nodeFor=(frame,key)=>frame.nodes.find(node=>node.key===key);
const rawPart=node=>`<details class="part" data-part-address="${escapeHtml(node.address)}" data-highlight="${node.highlight}"><summary><span>${escapeHtml(node.label)}</span><code>${escapeHtml(node.address)}</code></summary><pre>${escapeHtml(JSON.stringify(node.value,null,2))}</pre></details>`;
function matrixView(node,attention=null){
 const values=attention?.values||(Array.isArray(node.value)?node.value:node.value.values),shape=attention?.shape||node.value.shape||[values.length,values[0].length];
 const cols=attention?.columnLabels||Array.from({length:shape[1]},(_,i)=>`Feature ${i+1}`);
 const rows=attention?.rowLabels||Array.from({length:shape[0]},(_,i)=>`Token ${i+1}`);
 return `<div class="matrix-wrap" data-source-address="${escapeHtml(node.address)}" data-highlight="${node.highlight}"><table class="${attention?'attention':'matrix'}" data-attention-rows="${shape[0]}" data-attention-columns="${shape[1]}"><caption>${escapeHtml(node.label)}${attention?' · query rows / attended-token columns':''}</caption><thead><tr><th scope="col">${attention?'Query ↓ / attended token →':'Token ↓ / feature →'}</th>${cols.map(c=>`<th scope="col">${escapeHtml(c)}</th>`).join('')}</tr></thead><tbody>${values.map((row,i)=>`<tr><th scope="row">${escapeHtml(rows[i])}</th>${row.map(value=>`<td title="${value}" style="--attention:${attention?value:0}">${escapeHtml(Number(value).toFixed(3))}</td>`).join('')}</tr>`).join('')}</tbody></table></div>`;
}
function visualFor(frame){
 const n=key=>nodeFor(frame,key),v=key=>n(key)?.value;
 if(frame.kind==='perceptron'){
  const rows=frame.contributions?.rows;
  return `<section class="explanation perceptron-view" aria-label="Live perceptron values"><div class="input-strip"><span>Features <b>${escapeHtml(JSON.stringify(v('features')))}</b></span><span>Weights <b>${escapeHtml(JSON.stringify(v('weights')))}</b></span><span>Bias <b>${v('bias').value}</b></span><span>Threshold <b>${v('threshold').value}</b></span></div>
   ${rows?`<div class="products" data-source-address="${frame.contributions.address}" data-highlight="${n('contributions').highlight}">${rows.map(row=>`<div class="contribution"><code>x${row.index+1}</code><span>${row.input} × ${row.weight} = <strong>${row.product}</strong></span><i data-product-index="${row.index}" style="--bar:${row.width*100}%;--sign:${row.product<0?'#f6a8c5':'#83d7c8'}"></i></div>`).join('')}</div><p class="result-line" data-source-address="${n('weightedSum').address}" data-highlight="${n('weightedSum').highlight}">Bias ${v('weightedSum').bias} → weighted sum <strong>${v('weightedSum').value}</strong></p>`:'<p class="pending-result">Contributions and weighted sum have not been calculated.</p>'}
   ${v('activation')?`<p class="result-line activation" data-source-address="${n('activation').address}" data-highlight="${n('activation').highlight}">${v('activation').weightedSum} ≥ ${v('activation').threshold} → <strong>${v('activation').value===1?'true':'false'}</strong></p><p class="result-line output" data-source-address="${n('output').address}" data-highlight="${n('output').highlight}">Output <strong>${v('output').value}</strong> · ${escapeHtml(v('output').class)}</p>`:'<p class="pending-result">Activation / output: not calculated.</p>'}</section>`;
 }
 if(frame.kind==='tree')return `<section class="explanation tree-view" aria-label="Live decision path"><div class="input-strip">Input <b>${v('input').value}</b> · thresholds <b>${v('parameters').rootThreshold}, ${v('parameters').branchThreshold}</b></div><div class="tree-nodes">${['root','branch','path','leaf'].map(key=>{
  const node=n(key);if(!node)return `<div class="tree-node waiting">${key}<small>Not calculated</small></div>`;
  const value=node.value, text=key==='root'?`${value.value} ${value.operator} ${value.threshold} → ${value.outcome}`:key==='branch'?(value.comparison==='bypassed'?`Bypassed → ${value.outcome}`:`${value.value} ${value.operator} ${value.threshold} → ${value.outcome}`):key==='path'?value.decisions.join(' → '):value.label;
  return `<div class="tree-node" data-source-address="${node.address}" data-highlight="${node.highlight}"><small>${key}</small><strong>${escapeHtml(text)}</strong></div>`;
 }).join('<span class="flow-arrow" aria-hidden="true">→</span>')}</div></section>`;
 const matrices=['query','key','value','norm1','ffnHidden','ffnActivated','ffnOutput','norm2','output'].map(key=>n(key)).filter(Boolean);
 return `<section class="explanation transformer-view" aria-label="Live transformer values">${frame.attention?matrixView(n('softmax'),frame.attention):'<p class="pending-result">Attention has not been calculated.</p>'}<div class="matrix-grid">${matrices.length?matrices.map(node=>matrixView(node)).join(''):matrixView(n('input'))}</div></section>`;
}
function recordFor(card){const address=card.session.state.records[card.transport.cursor-1];return address?lab.get(address):null;}
function markup(card,index){
 const s=card.session.state,frame=card.session.frame(card.transport.cursor),step=frame.number?lab.get(s.steps[frame.number-1]):null;
 const complete=s.status==='complete',atLatest=frame.number===s.nextTick;
 const reads=step?.actual_consumes||[],writes=step?.actual_produces||[];
 return `<article class="run-card" data-run-card="${index}"><header><div><p class="eyebrow">${escapeHtml(s.name)}${s.parent?' · fork':''}</p><h3>${title(card.kind)}</h3></div><div class="run-actions"><button data-action="open" data-index="${index}" ${recordFor(card)?'':'disabled'}>Replay this record</button><button data-action="export" data-index="${index}" ${recordFor(card)?'':'disabled'}>Export record</button></div></header>
  <div class="live-controls"><button data-action="next" data-index="${index}" ${card.busy||complete||s.status==='failed'?'disabled':''}>Next step${!complete?' · '+escapeHtml(s.composition.Ticks[s.nextTick].name):''}</button><button data-action="play" data-index="${index}" ${complete||card.busy?'disabled':''}>Play</button><button data-action="pause" data-index="${index}">Pause</button><button data-action="back" data-index="${index}" ${card.busy||frame.number===0?'disabled':''}>Back</button><button data-action="latest" data-index="${index}" ${card.busy||atLatest?'disabled':''}>Latest frame</button></div>
  <label class="scrub">Review retained frames <input data-scrub="${index}" type="range" min="0" max="${s.nextTick}" value="${frame.number}" step="1" ${card.busy?'disabled':''}></label>
  <p class="frame-status">Frame ${frame.number} / ${s.nextTick} calculated · ${escapeHtml(frame.label)}${atLatest?'':' · reviewing history'}</p>
  <ol class="stages">${s.composition.Ticks.map((tick,i)=>`<li class="${i<frame.number?'done':'waiting'}">${escapeHtml(tick.name)}</li>`).join('')}</ol>
  ${visualFor(frame)}
  ${step?`<div class="access-flow"><div><small>READ</small>${reads.map(address=>`<code>${escapeHtml(address)}</code>`).join('')}</div><span class="flow-arrow">→</span><div><small>WROTE</small>${writes.map(address=>`<code>${escapeHtml(address)}</code>`).join('')}</div></div><p class="address-note">LAB execution: ${step.execution_ms.toFixed(3)} ms · animation: 600 ms (presentation time). <code>${escapeHtml(step.receiptAddress)}</code></p>`:'<p class="address-note">Input snapshots only. No algorithm Calculation has run yet.</p>'}
  <details class="raw-parts"><summary>Inspect ${frame.nodes.length} source Parts</summary><div class="parts">${frame.nodes.map(rawPart).join('')}</div></details></article>`;
}
function render(){runsElement.innerHTML=cards.map(markup).join('');}
async function present(card,frame,{previous,animate}){
 render();if(!animate||matchMedia('(prefers-reduced-motion: reduce)').matches)return;
 const element=runsElement.querySelector(`[data-run-card="${cards.indexOf(card)}"]`);
 const animations=[...element.querySelectorAll('[data-highlight="true"]')].map(node=>node.animate([{opacity:.2,transform:'translateY(8px)'},{opacity:1,transform:'translateY(0)'}],{duration:600,easing:'ease-out'}).finished);
 for(const bar of element.querySelectorAll('[data-product-index]')){
  const index=Number(bar.dataset.productIndex),from=previous.contributions?.rows[index]?.width||0,to=frame.contributions?.rows[index]?.width||0;
  animations.push(bar.animate([{width:from*100+'%'},{width:to*100+'%'}],{duration:600,easing:'ease-out'}).finished);
 }
 await Promise.all(animations.map(promise=>promise.catch(error=>{if(error.name!=='AbortError')throw error;})));
}
function addRun(kind,form){
 try{
  const options=optionsFor(kind,form),inputId=digestOf(options),parent=cards.find(card=>card.kind===kind);
  if(parent?.inputId===inputId){status.textContent='These inputs already have a session; Next step continues it.';return parent;}
  for(const card of cards)card.transport.pause();
  const session=createLiveReference(lab,kind,options,{parent:parent?.session.sessionAddress||null});
  const card={kind,session,inputId,busy:false,transport:null};
  card.transport=createLiveTransport(session,{present:(frame,change)=>present(card,frame,change)});
  cards.unshift(card);render();status.textContent=`${title(kind)} prepared. Inputs frozen; no algorithm steps calculated.`;return card;
 }catch(error){status.textContent=`Could not prepare ${title(kind)}: ${error.cause?.message||error.message}`;return null;}
}
async function drive(card,action){
 if(action==='pause'){card.transport.pause();status.textContent='Paused after the current step.';return;}
 if(card.busy)return;
 card.busy=true;render();
 try{
  if(action==='next')await card.transport.next();
  if(action==='play')await card.transport.play();
  if(action==='back')await card.transport.review(Math.max(0,card.transport.cursor-1));
  if(action==='latest')await card.transport.review(card.session.state.nextTick);
 }catch(error){status.textContent=`Step stopped: ${error.cause?.message||error.message}`;}
 finally{card.busy=false;render();}
}
for(const kind of ['tree','perceptron','transformer']){
 const form=$('#'+kind+'-form');
 form.addEventListener('submit',event=>{event.preventDefault();addRun(kind,form);});
 form.addEventListener('change',()=>addRun(kind,form));
}
runsElement.addEventListener('input',async event=>{
 if(!event.target.matches('[data-scrub]'))return;
 const card=cards[Number(event.target.dataset.scrub)];if(card.busy)return;
 await card.transport.review(Number(event.target.value));
});
runsElement.addEventListener('click',async event=>{
 const button=event.target.closest('button[data-action]');if(!button||button.disabled)return;
 const card=cards[Number(button.dataset.index)],action=button.dataset.action;
 if(['next','play','pause','back','latest'].includes(action)){await drive(card,action);return;}
 const record=recordFor(card);if(!record)return;
 if(action==='export'){downloadJson(record,`${card.kind}-through-${card.transport.cursor}.json`);status.textContent='Exported the retained record at this frame.';return;}
 try{
  viewerSources??=fetchPageSources(new URL('../../pyto/viewer/',import.meta.url));
  const page=composePage({...await viewerSources,record}),url=URL.createObjectURL(new Blob([page],{type:'text/html'}));
  const link=document.createElement('a');link.className='viewer-link';link.href=url;link.target='_blank';link.rel='noopener';link.textContent='Open recorded Tick replay';
  link.addEventListener('click',()=>setTimeout(()=>URL.revokeObjectURL(url),30000),{once:true});
  status.replaceChildren(document.createTextNode('Recorded replay (does not execute) — '),link);
 }catch(error){status.textContent='Could not compose the viewer: '+error.message;}
});
window.algorithmReferences={lab,cards,addRun};
addRun('perceptron',$('#perceptron-form'));
