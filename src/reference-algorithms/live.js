/** Live orchestration over LAB's existing executor. No algorithm arithmetic here. */
import { prepareDecisionTree } from './decision-tree.js';
import { preparePerceptron } from './perceptron.js';
import { prepareTransformer } from './transformer.js';
import { digestOf } from '../lab/lab.js';
import { freeze } from '../domain.js';
import { fromDiscStudioReceipt, validate } from '../../pyto/viewer/adapters.js';

const snapshot = value => freeze(structuredClone(value));
const frameRegistered = new WeakSet();
const preparers = { tree: prepareDecisionTree, perceptron: preparePerceptron, transformer: prepareTransformer };
export const REFERENCE_FIELDS = Object.freeze({
 tree: [['Input snapshot','input'],['Parameter snapshot','parameters'],['Root comparison','root'],['Branch comparison','branch'],['Path','path'],['Leaf / output','leaf']],
 perceptron: [['Features','features'],['Weights','weights'],['Bias','bias'],['Threshold','threshold'],['Contributions','contributions'],['Weighted sum','weightedSum'],['Activation','activation'],['Output','output']],
 transformer: [['Input tokens','input'],['Weights','weights'],['Parameters','parameters'],['Q projection','query'],['K projection','key'],['V projection','value'],['Attention scores','scores'],['Scaled scores','scaledScores'],['Attention softmax','softmax'],['Context','context'],['Attention output','attentionOutput'],['First residual','residual1'],['First normalization','norm1'],['FFN hidden','ffnHidden'],['ReLU activation','ffnActivated'],['FFN projection','ffnOutput'],['Second residual','residual2'],['Second normalization','norm2'],['Output','output']]
});

/** Only presentation calculations: copy real values, determine visual widths and labels. */
export function projectReferenceFrame({ spec, ...values }) {
 const nodes=spec.fields.map(field=>({ ...field, value:values[field.key], highlight:spec.produces.includes(field.address) }));
 const byKey=Object.fromEntries(nodes.map(node=>[node.key,node]));
 const contributions=byKey.contributions ? {
  address:byKey.contributions.address,
  rows:byKey.contributions.value.map(row=>({...row, width:Math.abs(row.product)/Math.max(1,...byKey.contributions.value.map(item=>Math.abs(item.product)))}))
 } : null;
 const attention=byKey.softmax ? {
  address:byKey.softmax.address, shape:byKey.softmax.value.shape, values:byKey.softmax.value.values,
  rowLabels:byKey.softmax.value.values.map((_,i)=>`Query ${i+1}`),
  columnLabels:Array.from({length:byKey.softmax.value.shape[1]},(_,i)=>`Token ${i+1}`)
 } : null;
 return snapshot({ kind:spec.kind, number:spec.number, label:spec.label, nodes, edges:spec.edges,
  highlights:spec.produces, contributions, attention, sourceAddresses:nodes.map(node=>node.address) });
}

/** Preparation reserves a fresh algorithm namespace; all future outputs remain absent. */
export function createLiveReference(lab, kind, options={}, {parent=null}={}) {
 if(!preparers[kind])throw Error(`Unknown reference '${kind}'.`);
 if(parent!==null&&!lab.has(parent))throw Error('The parent session is missing.');
 const prepared=preparers[kind](lab,options);
 const addresses=Object.fromEntries(Object.entries(prepared.addresses).map(([key,value])=>[key,typeof value==='function'?value(prepared.run):value]));
 const prefix=Object.values(addresses)[0].split('.').slice(0,4).join('.');
 const sessionAddress=prefix+'.session';
 const composition=snapshot(prepared.composition), name=prepared.name+'.live';
 const inputAddresses=Object.values(addresses).filter(address=>lab.has(address));
 const source={composition_sha256:digestOf(composition),inputs_sha256:digestOf(Object.fromEntries(inputAddresses.map(address=>[address,lab.get(address)]))),implementation_identity:'registered-address-only'};
 const read=()=>lab.get(sessionAddress);
 const write=value=>lab.put(sessionAddress,snapshot(value));
 write({kind,name,source,parent,addresses,inputAddresses,composition,nextTick:0,status:'ready',steps:[],frames:[],records:[],error:null});
 if(!frameRegistered.has(lab)){lab.register('fn.lab.reference.frame',projectReferenceFrame);frameRegistered.add(lab);}

 function project(number,step=null) {
  const current=read(), specAddress=prefix+`.frame-spec.${number}`, frameAddress=prefix+`.frame.${number}`;
  const fields=REFERENCE_FIELDS[kind].filter(([,key])=>lab.has(addresses[key])).map(([label,key])=>({label,key,address:addresses[key]}));
  const consumes=step?.actual_consumes||[],produces=step?.actual_produces||[];
  const spec={kind,number,label:step?.tick||'Inputs only',fields,produces,edges:consumes.flatMap(from=>produces.map(to=>({from,to})))};
  lab.put(specAddress,snapshot(spec));
  const frameName=name+`.frame-${number}`;
  lab.run(frameName,lab.document(frameName,[{name:'ProjectFrame',Calculations:[{
   call:'fn.lab.reference.frame',with:{spec:specAddress,...Object.fromEntries(fields.map(field=>[field.key,field.address]))},into:frameAddress
  }]}]));
  lab.runRecord(frameName);
  write({...current,frames:[...current.frames,frameAddress]});
  return lab.get(frameAddress);
 }
 project(0);
 let pending=null;
 function next() {
  if(pending)return pending;
  if(read().status==='complete')return Promise.resolve(lab.get(read().frames.at(-1)));
  if(read().status==='failed')return Promise.reject(Error(read().error));
  pending=Promise.resolve().then(()=>{
   const current=read(), index=current.nextTick, tick=composition.Ticks[index];
   write({...current,status:'executing'});
   try {
    const stepName=name+`.step-${index+1}`;
    const document=lab.document(stepName,[tick]);
    const start=performance.now();lab.run(stepName,document);const executionMs=performance.now()-start;
    const {record, address:recordAddress}=lab.runRecord(stepName);
    const invocations=record.ticks[0].invocations;
    const stepAddress=prefix+`.step.${index+1}`;
    const step=snapshot({number:index+1,tick:tick.name,composition:stepName,receiptAddress:`px.receipt.${stepName}`,recordAddress,
     actual_consumes:[...new Set(invocations.flatMap(inv=>inv.actual_consumes))],actual_produces:[...new Set(invocations.flatMap(inv=>inv.actual_produces))],
     execution_ms:executionMs,timing_scope:'LAB run including receipt settlement; excludes projection and animation'});
    lab.put(stepAddress,step);
    const steps=[...current.steps,stepAddress];
    // Adapt already-executed testimonies, preserving the original Tick order.
    const receipts=steps.map(address=>lab.get(lab.get(address).receiptAddress));
    const ticks=steps.flatMap(address=>lab.get(`px.pql.${lab.get(address).composition}`).Ticks);
    const cumulativeName=name+`.through-${index+1}`;
    const aggregate=validate(fromDiscStudioReceipt({PrincipleComponentRender:cumulativeName,Ticks:ticks},{trace:receipts.flatMap(receipt=>receipt.trace)}));
    const aggregateAddress=`px.run.${cumulativeName}`;lab.put(aggregateAddress,snapshot(aggregate));
    write({...current,nextTick:index+1,steps,records:[...current.records,aggregateAddress],status:'projecting'});
    const frame=project(index+1,step);
    write({...read(),status:index+1===composition.Ticks.length?'complete':'ready'});
    return frame;
   } catch(error) {
    write({...read(),status:'failed',error:error.cause?.message||error.message});throw error;
   }
  }).finally(()=>{pending=null;});
  return pending;
 }
 return Object.freeze({kind,addresses,sessionAddress,
  get state(){return read();},
  get record(){const address=read().records.at(-1);return address?lab.get(address):null;},
  get recordAddress(){return read().records.at(-1)||null;},
  frame(index=read().frames.length-1){if(!Number.isInteger(index)||index<0||index>=read().frames.length)throw Error('That frame has not been calculated.');return lab.get(read().frames[index]);},
  next,
  async all(){while(read().status!=='complete')await next();return this.frame();}
 });
}

/** Presentation transport. Review never calls Next; Play awaits the same Next as a click. */
export function createLiveTransport(session,{present=async()=>{}}={}) {
 let cursor=0,playing=false,pending=null;
 const show=async(index,animate)=>{const frame=session.frame(index),previous=session.frame(cursor);cursor=index;await present(frame,{previous,animate});return frame;};
 function next() {
  if(pending)return pending;
  pending=Promise.resolve().then(async()=>{
   if(session.state.status==='complete')return show(session.state.nextTick,false);
   await session.next();return show(session.state.nextTick,true);
  }).finally(()=>{pending=null;});
  return pending;
 }
 return {
  get cursor(){return cursor;},get busy(){return pending!==null;},get playing(){return playing;},
  next,
  pause(){playing=false;},
  async play(){if(playing)return;playing=true;try{while(playing&&session.state.status!=='complete')await next();}finally{playing=false;}},
  async review(index){playing=false;if(pending)await pending;return show(index,false);}
 };
}
