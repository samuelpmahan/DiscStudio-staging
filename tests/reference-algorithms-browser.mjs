#!/usr/bin/env node
/**
 * Browser check for the standalone reference page. It only talks to an
 * existing server: `node tests/reference-algorithms-browser.mjs --url
 * http://127.0.0.1:4173/`.
 */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import process from 'node:process';

const supplied = process.argv.indexOf('--url');
const externalUrl = supplied >= 0 ? process.argv[supplied + 1] : 'http://127.0.0.1:4173/';
if (supplied >= 0 && !externalUrl) throw new Error('--url needs a value');

// Keep the harness self-contained in the Codex runtime used by CI. An
// explicit module or executable override remains useful on another machine.
const playwrightModules = process.env.PLAYWRIGHT_MODULE
  ? [process.env.PLAYWRIGHT_MODULE]
  : ['playwright', '/Users/samuelmahan/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs'];
let browserApi;
let playwrightError;
for (const moduleName of playwrightModules) {
  try { browserApi = await import(moduleName); break; }
  catch (error) { playwrightError = error; }
}
if (!browserApi) throw new Error(`This browser check needs Playwright (tried ${playwrightModules.join(', ')}): ${playwrightError.message}`);

const executable = process.env.CHROME || process.env.CHROMIUM || process.env.BROWSER_EXECUTABLE
  || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
if (!fs.existsSync(executable)) throw new Error(`Chrome executable not found: ${executable}`);

const pageUrl = new URL('/public/algorithm-references/index.html', externalUrl).href;
const submit = async (page, form) => {
  await page.locator(form).evaluate(node => node.requestSubmit());
};
const addressesIn = async (page, cardIndex) => page.locator(`[data-run-card="${cardIndex}"] [data-part-address]`).evaluateAll(nodes => nodes.map(node => node.dataset.partAddress));

const browser = await browserApi.chromium.launch({ headless: true, executablePath: executable });
const output='test-results/algorithm-references-live';fs.mkdirSync(output,{recursive:true});
try {
 const context=await browser.newContext({viewport:{width:1360,height:1000},acceptDownloads:true});
 const page=await context.newPage(),errors=[];page.on('pageerror',error=>errors.push(error.message));
 await page.goto(pageUrl,{waitUntil:'networkidle'});
 const buildResponse=await page.request.get(new URL('/build-info.json',externalUrl).href);
 assert.equal(buildResponse.ok(),true);const build=await buildResponse.json();
 if(process.env.SOURCE_COMMIT)assert.equal(build.commit,process.env.SOURCE_COMMIT);
 const card=()=>page.locator('[data-run-card="0"]');
 const inspect=()=>page.evaluate(()=>{const c=algorithmReferences.cards[0],s=c.session;return {state:s.state,frame:s.frame(c.transport.cursor),record:s.record,outputExists:algorithmReferences.lab.has(s.addresses.output||s.addresses.leaf)};});
 const idle=()=>page.waitForFunction(()=>!algorithmReferences.cards[0].busy);
 const next=async()=>{await card().locator('[data-action="next"]').click();await idle();};
 const checkParts=async()=>{
  const values=await page.evaluate(()=>[...document.querySelectorAll('[data-run-card="0"] [data-part-address]')].map(node=>({address:node.dataset.partAddress,text:node.querySelector('pre').textContent,actual:algorithmReferences.lab.get(node.dataset.partAddress)})));
  for(const value of values)assert.equal(value.text,JSON.stringify(value.actual,null,2));
 };
 const initial=await inspect();assert.equal(initial.state.nextTick,0);assert.equal(initial.outputExists,false);assert.equal(initial.frame.nodes.length,4);
 await card().locator('[data-action="next"]').evaluate(button=>{button.click();button.click();button.click();});await idle();
 const first=await inspect();assert.equal(first.state.nextTick,1);assert.equal(first.outputExists,false);assert.equal(first.record.ticks.length,1);
 assert.deepEqual(first.frame.contributions.rows.map(row=>row.product),[1,-1]);
 assert.match(await card().locator('.result-line').first().textContent(),/weighted sum 0.25/);
 assert.equal(await card().locator('.activation').count(),0);await checkParts();
 await card().screenshot({path:output+'/perceptron-step-1.png'});
 const oldFrame=JSON.stringify(first.frame),firstSession=first.state;
 await next();const completed=await inspect();assert.equal(completed.state.nextTick,2);assert.equal(completed.outputExists,true);
 assert.match(await card().locator('.activation').textContent(),/0.25 ≥ 0/);assert.match(await card().locator('.output').textContent(),/Output 1/);
 await card().locator('[data-action="back"]').click();await idle();
 const reviewed=await inspect();assert.equal(reviewed.state.nextTick,2);assert.equal(JSON.stringify(reviewed.frame),oldFrame);assert.equal(await card().locator('.activation').count(),0);
 for(const index of [0,1]){
  await card().locator('[data-scrub]').evaluate((input,value)=>{input.value=String(value);input.dispatchEvent(new Event('input',{bubbles:true}));},index);
  assert.equal((await inspect()).frame.number,index);assert.equal((await inspect()).state.nextTick,2);
 }
 const downloadEvent=page.waitForEvent('download');await card().locator('[data-action="export"]').click();const download=await downloadEvent;await download.saveAs(output+'/perceptron-through-1.json');
 const exported=JSON.parse(fs.readFileSync(output+'/perceptron-through-1.json','utf8'));assert.equal(exported.ticks.length,1);
 const {validate}=await import('../pyto/viewer/adapters.js');validate(exported);
 await page.locator('#perceptron-form [name="bias"]').fill('-1');await page.locator('#perceptron-form [name="bias"]').dispatchEvent('change');
 const fork=await inspect();assert.equal(fork.state.nextTick,0);assert.equal(fork.outputExists,false);assert.equal(fork.state.parent,firstSession.addresses.features.split('.').slice(0,4).join('.')+'.session');
 await card().locator('[data-action="play"]').click();await idle();assert.equal((await inspect()).state.nextTick,2);
 assert.match(await card().locator('.output').textContent(),/Output 0/);
 assert.equal(await page.evaluate(()=>algorithmReferences.lab.get(algorithmReferences.cards[1].session.addresses.output).value),1);
 const count=await page.locator('[data-run-card]').count();
 await page.locator('#perceptron-form [name="features"]').fill('2,');await submit(page,'#perceptron-form');
 assert.match(await page.locator('#status').textContent(),/no blank entries/);assert.equal(await page.locator('[data-run-card]').count(),count);
 await page.locator('#tree-form [name="value"]').fill('12');await submit(page,'#tree-form');
 assert.equal((await inspect()).state.nextTick,0);
 for(let i=1;i<=4;i++){await next();const result=await inspect();assert.equal(result.state.nextTick,i);assert.equal(result.outputExists,i===4);}
 assert.match(await card().locator('.tree-view').textContent(),/high/);await checkParts();await card().screenshot({path:output+'/tree-step-4.png'});
 await page.locator('#transformer-form [name="input"]').fill('1, 0; 0, 1; 1, 1');await submit(page,'#transformer-form');
 assert.match(await page.locator('#status').textContent(),/prepared/);assert.equal((await inspect()).state.nextTick,0);
 assert.equal(await card().locator('.matrix tbody tr').count(),3);assert.deepEqual(errors,[]);
 await next();assert.equal(await card().locator('.attention').count(),0);assert.equal((await inspect()).outputExists,false);
 await next();const attention=await inspect();assert.deepEqual(attention.frame.attention.shape,[3,3]);assert.equal(attention.outputExists,false);
 assert.equal(await card().locator('.attention').getAttribute('data-attention-rows'),'3');assert.equal(await card().locator('.attention tbody tr').count(),3);
 assert.equal(await card().locator('.attention tbody td').count(),9);
 assert.deepEqual(await card().locator('.attention tbody th').allTextContents(),['Query 1','Query 2','Query 3']);
 assert.deepEqual((await card().locator('.attention thead th').allTextContents()).slice(1),['Token 1','Token 2','Token 3']);
 await checkParts();await card().screenshot({path:output+'/transformer-step-2.png'});
 for(let i=3;i<=5;i++){await next();assert.equal((await inspect()).state.nextTick,i);}
 const full=await inspect();validate(full.record);assert.equal(full.record.ticks.length,5);
 await card().locator('[data-action="open"]').click();await page.locator('#status a.viewer-link').waitFor();
 const popup=context.waitForEvent('page');await page.locator('#status a.viewer-link').click();const tick=await popup;
 tick.on('pageerror',error=>errors.push(error.message));await tick.waitForSelector('section.tick');
 assert.deepEqual(await tick.locator('section.tick .tick-name').allTextContents(),full.record.ticks.map(value=>value.name));
 fs.writeFileSync(output+'/transformer-through-5.json',JSON.stringify(full.record,null,2)+'\n');
 const replayUrl=await page.locator('#status a.viewer-link').getAttribute('href');
 fs.writeFileSync(output+'/transformer-ticks.html',await page.evaluate(async url=>(await fetch(url)).text(),replayUrl));
 await tick.close();
 await page.setViewportSize({width:390,height:844});
 assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true,'page must not overflow on a narrow viewport');
 assert.deepEqual(errors,[]);
 fs.writeFileSync(output+'/verification.json',JSON.stringify({pass:true,checks:['live one-Tick Next','rapid click coalescing','future Parts absent','retained frame scrub','exported partial record validates','fork preserves old output','Play executes Next','invalid input preserves runs','tree 4 steps','transformer 5 steps','3x3 query/attended-token labels','board-backed visible numbers','shared replay viewer','narrow viewport'],build,sourceState:'base commit plus uncommitted changes; fingerprint identifies src/public/tests',sourceCommit:build.commit},null,2));
 console.log('PASS: live Next/Play, absent future outputs, retained frames/forks, valid exports, tree/transformer steps, attention shape/labels and shared replay. Screenshots: '+output);
} finally {await browser.close();}
