import {createExecBoard,trackAccess} from './board.ts';
import type {PxC} from './board.ts';
import type {FrozenCalculation,OperationSpec,Receipt} from './contract.ts';
import {sha256HexSyncText} from './sha256.ts';
export interface Cartridge {
 id:string;
 stages:readonly {id:string;variant:string;operation:OperationSpec;execute:(px:PxC)=>void}[];
}
/** First synchronous cartridge host. Shares ChainSpot's OperationSpec and access tracking.
 * This is not yet its compiled gateway/PCR, stage discovery, or tidy integration.
 */
export function loadCartridge(cartridge:Cartridge){
 const px=createExecBoard();
 const ticks:({stage:string;variant:string;operation:string}&Receipt)[]=[];
 return {px,ticks,run(stageId:string,variant='clean'){
  const stage=cartridge.stages.find(s=>s.id===stageId&&s.variant===variant);
  if(!stage)throw Error(`Unknown stage: ${stageId}/${variant}`);
  for(const key of stage.operation.consumes)if(!px.has(key))throw Error('Missing input: '+key);
  const startedAtMs=Date.now();
  const access=trackAccess(px,stage.operation);
  stage.execute(access.tracked);
  if(stage.operation.accessConformance==='exact'){
   const mismatch=(declared:readonly string[],actual:ReadonlySet<string>)=>declared.length!==actual.size||declared.some(address=>!actual.has(address));
   if(mismatch(stage.operation.consumes,access.consumed)||mismatch(stage.operation.produces,access.produced)){
    throw Error(`PxC: Tick '${stage.operation.id}' actual access differs from its exact declaration.`);
   }
  }
  const frozenCalculations:FrozenCalculation[]=[...access.called].map(address=>{
   const calculate=access.registered.get(address);
   if(!calculate)throw Error(`PxC: Tick '${stage.operation.id}' called '${address}' without registering its implementation in this Tick.`);
   return {address,implementationHash:sha256HexSyncText(calculate.toString()),identityScope:'runtime-function-body',limitation:'called helpers, constants, templates, and assets are not covered'};
  });
  const receipt:Receipt={opId:stage.operation.id,frozenCalculations,startedAtMs,durationMs:Date.now()-startedAtMs,
   declaredConsumes:stage.operation.consumes,declaredProduces:stage.operation.produces,
   actualConsumes:[...access.consumed],actualProduces:[...access.produced],writes:access.writes,probes:[],artifacts:[]};
  const record={stage:stage.id,variant:stage.variant,operation:stage.operation.id,...receipt};ticks.push(record);return record;
 }};
}
