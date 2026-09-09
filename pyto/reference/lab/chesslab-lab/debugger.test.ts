import {test} from 'node:test';
import assert from 'node:assert/strict';
import {analyzeFrame,analyzePosition} from '../src/chess/analysis.ts';
import {runDebugger} from '../src/chess/debugger.ts';
import {loadCartridge} from '../src/lab/host.ts';
import {chessCartridge} from '../src/chess/cartridge.ts';
import {famousGame} from '../src/famousGame.ts';
import {learningCases,operaGame} from '../src/learningCases.ts';

const ids=(side:ReturnType<typeof analyzeFrame>['activeSide'])=>side.legalMoves.map(move=>move.id).sort();

test('replay oracle preserves 34...Qe3 threat and historical final mate',()=>{
 for (const frame of famousGame.frames) {
  const replay=analyzeFrame(frame);
  assert.deepEqual(ids(replay.activeSide),[...frame.legalMoves].sort());
  assert.equal(replay.activeSide.inCheck,frame.check);
  assert.equal(replay.activeSide.checkmate,frame.checkmate);
 }
 const before=analyzeFrame(famousGame.frames[2]);
 const mateMove=before.activeSide.candidates.find(move=>move.id==='e4h7');
 assert.ok(mateMove?.legal);
 assert.equal(mateMove.givesMate,true);

 const final=analyzeFrame(famousGame.frames[3]);
 assert.equal(final.activeSide.side,'black');
 assert.equal(final.activeSide.inCheck,true);
 assert.equal(final.activeSide.checkmate,true);
 assert.equal(final.activeSide.legalMoves.length,0);
 assert.equal(final.source.frameCheckmate,true);
});

test('Opera Game learning frames preserve the python-chess legal-move oracle',()=>{
 assert.deepEqual(learningCases.map(game=>game.id),['fritz-kramnik-2006','opera-game-1858']);
 assert.match(operaGame.source,/chessbase\.com/);
 assert.match(operaGame.secondarySource,/chess\.com/);
 for (const frame of operaGame.frames) {
  const replay=analyzeFrame(frame);
  assert.deepEqual(ids(replay.activeSide),[...frame.legalMoves].sort());
  assert.equal(replay.activeSide.inCheck,frame.check);
  assert.equal(replay.activeSide.checkmate,frame.checkmate);
  assert.equal(frame.fen.split(' ')[2],'k');
 }
 assert.equal(operaGame.frames[1].change?.san,'Qb8+');
 assert.deepEqual(operaGame.frames[1].legalMoves,['d7b8']);
 assert.equal(operaGame.frames[3].change?.san,'Rd8#');
 assert.equal(operaGame.frames[3].checkmate,true);
});

test('attack geometry remains distinct from legal moves under a pin',()=>{
 const analysis=analyzePosition({
  pieces:[
   {square:'e1',label:'Kw'}, {square:'e2',label:'Qw'},
   {square:'a8',label:'Kb'}, {square:'e8',label:'Qb'}
  ],sideToMove:'white'
 });
 const queen=analysis.activeSide.relations.find(relation=>relation.piece.square==='e2');
 assert.ok(queen);
 assert.ok(queen.attacks.some(attack=>attack.target==='a6'));
 const pinnedMove=analysis.activeSide.candidates.find(move=>move.id==='e2a6');
 assert.ok(pinnedMove);
 assert.equal(pinnedMove.legal,false);
 assert.deepEqual(pinnedMove.reasons,['king-safety']);
 assert.notEqual(queen.attacks.some(attack=>attack.target==='a6'),pinnedMove.legal);
});

test('capture simulation exposes the line after a king capture attempt',()=>{
 const analysis=analyzePosition({
  pieces:[
   {square:'a1',label:'Kw'}, {square:'h1',label:'Qw'},
   {square:'h7',label:'Qw'}, {square:'h8',label:'Kb'}
  ],sideToMove:'black'
 });
 const capture=analysis.activeSide.candidates.find(move=>move.id==='h8h7');
 assert.ok(capture);
 assert.equal(capture.captured?.square,'h7');
 assert.equal(capture.legal,false);
 assert.deepEqual(capture.reasons,['king-safety']);
});

test('capturing a king is represented as a rejected candidate',()=>{
 const analysis=analyzePosition({
  pieces:[{square:'f6',label:'Kw'},{square:'g7',label:'Qw'},{square:'h8',label:'Kb'}],
  sideToMove:'white'
 });
 const capture=analysis.activeSide.candidates.find(move=>move.id==='g7h8');
 assert.ok(capture);
 assert.equal(capture.legal,false);
 assert.deepEqual(capture.reasons,['king-capture']);
 assert.match(capture.reasonText[0],/king/i);
});

test('scores and explanations are deterministic while rule omissions stay explicit',()=>{
 const input={fen:'4k3/8/8/8/8/8/8/4K3 w KQ e3 0 1',pieces:[{square:'e1',label:'Kw'},{square:'e8',label:'Kb'}],sideToMove:'white' as const};
 const cleanA=analyzePosition(input,'clean');
 const cleanB=analyzePosition(input,'clean');
 assert.deepEqual(cleanA,cleanB);
 assert.equal(cleanA.limitations.rules.castling.supported,false);
 assert.equal(cleanA.limitations.rules.castling.status,'omitted');
 assert.equal(cleanA.limitations.rules.enPassant.supported,false);
 assert.equal(cleanA.limitations.rules.enPassant.status,'omitted');
 assert.match(cleanA.limitations.rules.castling.reason,/rook|history|state/i);
 assert.match(cleanA.limitations.rules.enPassant.reason,/previous move|history|frame/i);
 const scored=cleanA.activeSide.legalMoves.find(move=>move.id==='e1d2');
 assert.ok(scored?.score);
 assert.equal(scored.score.explanation.length>0,true);
 assert.equal(typeof scored.score.total,'number');
 const cleanFrame=analyzeFrame(famousGame.frames[2],'clean');
 const experimental=analyzeFrame(famousGame.frames[2],'exp');
 assert.deepEqual(ids(cleanFrame.activeSide),ids(experimental.activeSide));
 assert.notDeepEqual(cleanFrame.activeSide.legalMoves.map(move=>move.score?.total),experimental.activeSide.legalMoves.map(move=>move.score?.total));
 assert.match(experimental.policy.description,/facts and legality are unchanged/i);
});

test('debugger keeps observations, policy, and PxC receipts separately labeled',()=>{
 const clean=runDebugger(famousGame.frames[2]);
 const exp=runDebugger(famousGame.frames[2],'exp');
 assert.equal(clean.schema,'chesslab-debugger@1');
 assert.equal(clean.ticks.length,2);
 assert.deepEqual(clean.ticks.map(t=>t.stage),['S0','S1']);
 assert.deepEqual(clean.ticks.map(t=>t.variant),['clean','clean']);
 assert.deepEqual(exp.ticks.map(t=>t.variant),['exp','exp']);
 const observed=(clean.snapshot as any).observed;
 const policy=(clean.snapshot as any).policy;
 assert.ok(observed.attacks.white);
 assert.ok(observed.checkStatus.black);
 assert.equal(policy.variant,'clean');
 assert.equal(policy.sides.white.candidates.find((move:any)=>move.id==='e4h7').givesMate,true);
 assert.equal((exp.snapshot as any).observed.checkStatus.black.checkmate,observed.checkStatus.black.checkmate);
 assert.notDeepEqual(
  policy.sides.white.candidates.map((move:any)=>move.score?.total),
  (exp.snapshot as any).policy.sides.white.candidates.map((move:any)=>move.score?.total)
 );
});

test('S1 receipt is downstream of the materialized S0 object slot',()=>{
 const host=loadCartridge(chessCartridge);
 const frame=famousGame.frames[2];
 host.px.set('px.chess.frame',frame);
 host.run('S0','clean');
 const objects=host.px.get<any>('px.chess.objects');
 assert.equal(objects.pieces.length,frame.pieces.length);
 assert.deepEqual(objects.pieces.map((piece:any)=>piece.square).sort(),frame.pieces.map(piece=>piece.square).sort());
 const s1=host.run('S1','clean');
 assert.deepEqual([...s1.actualConsumes].sort(),['px.chess.frame','px.chess.objects']);
 assert.equal(s1.actualProduces.includes('px.chess.analysis'),true);
});
