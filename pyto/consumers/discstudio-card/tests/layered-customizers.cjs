const assert = require('node:assert/strict');
const fs = require('node:fs');
const crypto = require('node:crypto');
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || '/tmp/discstudio-browser/node_modules/playwright');
const base = process.env.CARDS_URL || 'http://127.0.0.1:8782';
const evidence = process.env.CARDS_EVIDENCE || '/mnt/d/pyto-worktrees/evidence/cards';
const sha = text => crypto.createHash('sha256').update(text).digest('hex');
(async () => {
  const browser = await chromium.launch({headless:true,args:['--no-sandbox']});
  try {
    const context = await browser.newContext({viewport:{width:1400,height:1100}});
    const page = await context.newPage();
    const errors=[]; page.on('pageerror', e=>errors.push(e.message));
    const eventRequests=[];page.on('request',r=>{if(r.url().endsWith('/api/events'))eventRequests.push(r.postDataJSON())});
    const artRequests=[]; page.on('request', r=>{if(r.url().endsWith('/api/art'))artRequests.push(r.postDataJSON())});
    await page.goto(base);
    const ready = async()=>{await page.waitForFunction(()=>!document.getElementById('save').disabled);};
    const state = ()=>page.evaluate(()=>snapshot());
    const edit = async(id,value)=>{await page.locator('#'+id).fill(String(value));await page.locator('#'+id).press('Tab');};
    const keep = async(id)=>{const response=page.waitForResponse(r=>r.url().endsWith('/api/recipes')&&r.request().method()==='POST');await page.locator('#'+id).click();const row=await(await response).json();await ready();await page.waitForFunction(saved=>document.getElementById('variantPicker').value===saved,row.id);return row};
    await ready();
    assert.equal(await page.locator('#battleStage .empty-slot').count(),1);
    assert.equal(await page.locator('#battleStage [data-presentation-id]').count(),1);
    await edit('name','Retained A');await edit('note','My exact owner words.');await edit('flight1Value',9);
    assert.equal(await page.locator('#discName').innerText(),'Retained A');
    assert.equal(await page.locator('#battleStage strong').innerText(),'Retained A');
    assert.equal(await page.locator('#stage [data-flight="flight1"] [data-value]').textContent(),'9');
    assert.equal(await page.locator('#battleStage [data-flight="flight1"] [data-value]').textContent(),'9');
    const freeWidth=(await page.locator('#stage image').boundingBox()).width;
    const battleBefore=await page.locator('#battleStage').innerHTML();
    await page.locator('#stage').screenshot({path:evidence+'/single-free.png'});
    await page.locator('#singleLayout').selectOption('gallery');
    assert((await page.locator('#stage image').boundingBox()).width>freeWidth*1.5);
    assert.equal(await page.locator('#battleStage').innerHTML(),battleBefore);
    await page.locator('#stage').screenshot({path:evidence+'/single-gallery.png'});
    await page.locator('#singleDetails').uncheck();
    assert.equal(await page.locator('#stage [data-flight]').count(),0);
    assert(await page.locator('#ownerNote').isHidden());
    assert.equal(await page.locator('#battleStage [data-flight]').count(),4);
    await page.locator('#singleDetails').check();
    const beforeSave=await state(),a=await keep('keep');
    const afterSave=await state();
    assert.equal(a.recipe.presentationId,beforeSave.presentationId);
    assert.notEqual(afterSave.presentationId,a.recipe.presentationId);
    assert.equal(afterSave.physicalDiscId,a.recipe.physicalDiscId);
    assert.notEqual(afterSave.physicalDiscId,afterSave.presentationId);
    assert.deepEqual(afterSave.cards.single.discRecipeIds,[afterSave.presentationId]);
    const baselineHtml=await page.locator('#baseline').innerHTML();
    const baselineImage=await page.locator('#baselineStage image').getAttribute('href');
    await edit('name','Current B');await edit('note','Trial words only.');await edit('seed',321);
    await page.locator('#tryArt').click();await ready();
    await page.locator('#battleParticipant').selectOption(a.id);await ready();
    assert.equal(await page.locator('#battleStage .empty-slot').count(),0);
    const first=page.locator('#battleStage [data-presentation-id]').nth(0),second=page.locator('#battleStage [data-presentation-id]').nth(1);
    assert.equal(await first.locator('strong').innerText(),'Current B');
    assert.equal(await second.locator('strong').innerText(),'Retained A');
    assert.equal(await second.locator('image').getAttribute('href'),baselineImage);
    const secondBefore=await second.innerHTML();
    await edit('name','Current C');await edit('flight1Value',8);await edit('seed',322);
    await page.locator('#tryArt').click();await ready();
    assert.equal(await first.locator('strong').innerText(),'Current C');
    assert.equal(await first.locator('image').getAttribute('href'),await page.locator('#stage image').getAttribute('href'));
    assert.notEqual(await first.locator('image').getAttribute('href'),baselineImage);
    assert.equal(await second.innerHTML(),secondBefore);
    assert.equal(await page.locator('#baseline').innerHTML(),baselineHtml);
    const singleBefore=await page.locator('#stage').innerHTML();
    const sideBoxes=await page.locator('#battleStage [data-presentation-id]').evaluateAll(nodes=>nodes.map(n=>({x:n.getBoundingClientRect().x,y:n.getBoundingClientRect().y})));
    assert(sideBoxes[1].x>sideBoxes[0].x&&Math.abs(sideBoxes[1].y-sideBoxes[0].y)<2);
    await page.locator('#battleStage').screenshot({path:evidence+'/battle-side-by-side.png'});
    await page.locator('#battleLayout').selectOption('stacked');
    const stackedBoxes=await page.locator('#battleStage [data-presentation-id]').evaluateAll(nodes=>nodes.map(n=>({x:n.getBoundingClientRect().x,y:n.getBoundingClientRect().y})));
    assert(stackedBoxes[1].y>stackedBoxes[0].y&&Math.abs(stackedBoxes[1].x-stackedBoxes[0].x)<2);
    assert.equal(await page.locator('#stage').innerHTML(),singleBefore);
    await page.locator('#battleStage').screenshot({path:evidence+'/battle-stacked.png'});
    await page.locator('#battleDetails').uncheck();
    assert.equal(await page.locator('#battleStage [data-flight]').count(),0);
    assert.equal(await page.locator('#battleStage strong').count(),0);
    assert.equal(await page.locator('#stage [data-flight]').count(),4);
    await page.locator('#battleDetails').check();
    const b=await keep('save');
    assert.equal(b.recipe.cards.single.type,'single');assert.equal(b.recipe.cards.battle.type,'battle');
    assert.equal(b.recipe.cards.battle.discRecipeIds.length,2);
    assert.equal(Object.keys(b.recipe.presentations).length,2);
    for(const [id,p] of Object.entries(b.recipe.presentations)){
      assert.equal(p.presentationId,id);assert.equal(p.cards,undefined);assert.equal(p.presentations,undefined);
      for(const size of [42,96,220]){
        const r=b.recipe.presentationRenderReceipts[id][size];
        const input={family:p.art.family,seed:p.art.seed,base:p.art.base,accent:p.art.accent,targetPx:size,label:p.art.label,version:p.art.version};
        assert.equal(r.inputSha256,sha(JSON.stringify(input)));
        assert.equal(r.seed,p.art.seed);assert.equal(r.family,p.art.family);
      }
    }
    const savedList=await(await page.request.get(base+'/api/recipes')).json();
    assert.deepEqual(savedList.find(row=>row.id===a.id),a);
    const cBeforeReplay=await page.locator('#stage image').getAttribute('href');
    await page.reload();await ready();await page.locator('#variantPicker').selectOption(b.id);await page.locator('#load').click();await ready();
    const replay=await state();
    assert.equal(replay.name,'Current C');assert.equal(replay.note,'Trial words only.');
    assert.equal(replay.cards.single.layout,'gallery');assert.equal(replay.cards.battle.layout,'stacked');
    assert.equal(replay.cards.battle.discRecipeIds[1],a.recipe.presentationId);
    assert.notEqual(replay.presentationId,b.recipe.presentationId);
    assert.equal(await page.locator('#stage image').getAttribute('href'),cBeforeReplay);
    assert.equal(await page.locator('#battleStage [data-presentation-id]').nth(1).locator('image').getAttribute('href'),baselineImage);
    for(const [id,receipts] of Object.entries(replay.presentationRenderReceipts))for(const size of [42,96,220]){
      const p=replay.presentations[id],r=receipts[size];
      assert.equal(r.inputSha256,sha(JSON.stringify({family:p.art.family,seed:p.art.seed,base:p.art.base,accent:p.art.accent,targetPx:size,label:p.art.label,version:p.art.version})));
    }
    assert.equal(await page.locator('#sizes img').count(),2);
    await page.screenshot({path:evidence+'/customizers-desktop.png',fullPage:true});
    await page.setViewportSize({width:390,height:844});
    await page.screenshot({path:evidence+'/customizers-mobile.png',fullPage:true});
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth),390);
    await page.setViewportSize({width:1400,height:1100});
    await page.locator('#singleLayout').selectOption('standard');
    const beforeDrag=(await state()).positions.disc;
    await page.locator('#stage [data-part="disc"]').scrollIntoViewIfNeeded();
    const target=await page.locator('#stage [data-part="disc"]').boundingBox();
    await page.mouse.move(target.x+target.width/2,target.y+target.height/2);await page.mouse.down();await page.mouse.move(target.x+target.width/2+15,target.y+target.height/2+20,{steps:4});await page.mouse.up();
    assert.notDeepEqual((await state()).positions.disc,beforeDrag);
    await edit('posX',60);await edit('posY',40);assert.deepEqual((await state()).positions.disc,{x:60,y:40});
    await page.locator('[data-preset="square"]').click();assert.deepEqual((await state()).positions.flight1,{x:35,y:35});
    await page.locator('#group').check();
    await page.locator('#stage [data-part="flight1"]').scrollIntoViewIfNeeded();
    const groupBefore=(await state()).positions;
    const groupTarget=await page.locator('#stage [data-part="flight1"]').boundingBox();
    await page.mouse.move(groupTarget.x+groupTarget.width/2,groupTarget.y+groupTarget.height/2);await page.mouse.down();await page.mouse.move(groupTarget.x+groupTarget.width/2+10,groupTarget.y+groupTarget.height/2+12,{steps:4});await page.mouse.up();
    const groupAfter=(await state()).positions;
    const dx=groupAfter.flight1.x-groupBefore.flight1.x,dy=groupAfter.flight1.y-groupBefore.flight1.y;
    assert(dx!==0||dy!==0);
    for(const k of ['flight2','flight3','flight4']){assert(Math.abs(groupAfter[k].x-groupBefore[k].x-dx)<.02);assert(Math.abs(groupAfter[k].y-groupBefore[k].y-dy)<.02)}
    await page.locator('#group').uncheck();
    await page.locator('#reset').click();assert.deepEqual((await state()).positions.disc,{x:50,y:43});
    await page.locator('#spin').check();assert(await page.locator('#stage .disc-spin').count());await page.locator('#spin').uncheck();
    await page.locator('#up').click();await edit('question','Does this keep both presentations?');await page.locator('#logQuestion').click();
    await page.waitForFunction(()=>document.getElementById('telemetryStatus').textContent==='Changes and reactions recorded locally.');
    const invalidResults=await page.evaluate(()=>{
      const original=snapshot(),cases=[];
      for(const [label,mutate] of [
        ['nested',r=>r.presentations[r.presentationId].cards={}],
        ['dangling',r=>r.cards.battle.discRecipeIds[1]='missing-presentation'],
        ['too-many',r=>r.presentations.extra=structuredClone(r.presentations[r.presentationId])],
        ['bad-layout',r=>r.cards.single.layout='pretend-layout'],
        ['bad-details',r=>r.cards.single.details='yes'],
        ['array-cards',r=>r.cards=[]],
        ['identity-mismatch',r=>r.physicalDiscId='different-physical-disc'],
        ['oversized',r=>r.unused='x'.repeat(64001)]
      ]){const r=structuredClone(original);mutate(r);let rejected=false;try{validate(r)}catch{rejected=true}cases.push({label,rejected})}
      return cases;
    });assert(invalidResults.every(r=>r.rejected));
    const legacy=await state();delete legacy.cards;delete legacy.presentations;delete legacy.presentationId;delete legacy.physicalDiscId;delete legacy.presentationRenderReceipts;legacy.schemaVersion=2;legacy.discId='Legacy physical disc with spaces';
    await page.locator('summary').click();
    await page.locator('#json').fill(JSON.stringify(legacy));await page.locator('#apply').click();await ready();
    assert.equal((await state()).cards.battle.discRecipeIds.length,1);
    assert.equal((await state()).cards.single.layout,'standard');
    assert.equal((await state()).physicalDiscId,legacy.discId);
    await page.setViewportSize({width:390,height:844});
    await page.screenshot({path:evidence+'/legacy-mobile.png',fullPage:true});
    const mobile=await page.evaluate(()=>({width:innerWidth,scrollWidth:document.documentElement.scrollWidth}));
    assert.equal(mobile.width,mobile.scrollWidth);
    const exactSave=await state();
    let releaseSave,arrived;
    const hold=new Promise(resolve=>releaseSave=resolve),seen=new Promise(resolve=>arrived=resolve);
    await page.route(base+'/api/recipes',async route=>{if(route.request().method()==='POST'){arrived();await hold}await route.continue()});
    const delayedResponse=page.waitForResponse(r=>r.url().endsWith('/api/recipes')&&r.request().method()==='POST');
    await page.locator('#save').click();await seen;
    await edit('name','Edited while saving');releaseSave();
    const delayedSaved=await(await delayedResponse).json();await ready();
    await page.waitForFunction(()=>document.getElementById('telemetryStatus').textContent==='Changes and reactions recorded locally.');
    assert.deepEqual(delayedSaved.recipe,exactSave);
    const saveEvent=eventRequests.filter(e=>e.action==='save').at(-1);
    assert.deepEqual(saveEvent.savedRecipe,exactSave);
    assert.equal(saveEvent.savedPresentationId,exactSave.presentationId);
    assert.equal((await state()).name,'Edited while saving');
    await page.unroute(base+'/api/recipes');
    await page.route(base+'/api/art',route=>route.fulfill({status:400,contentType:'application/json',body:JSON.stringify({error:'Deliberate browser failure fixture'})}));
    await edit('seed',9999);await page.locator('#tryArt').click();
    await page.waitForFunction(()=>document.getElementById('renderStatus').textContent.startsWith('Render failed.'));
    assert(await page.locator('#save').isDisabled());
    assert.deepEqual((await state()).renderReceipts,{});
    await page.unroute(base+'/api/art');
    await edit('seed',322);await page.locator('#tryArt').click();await ready();
    assert.equal(Object.keys((await state()).renderReceipts).length,3);
    assert.deepEqual(errors,[]);
    const report={passed:true,savedVariantA:a.id,savedVariantB:b.id,sharedActiveDisc:true,independentVisibleLayouts:true,independentDetails:true,explicitRetainedParticipant:true,immutableBaselineAndSavedVariant:true,forksPresentationKeepsPhysicalDisc:true,embeddedReplayAfterReload:true,perPresentationReceiptInputHashes:true,art42and96:true,dragAndGroupAndPositionAndPresetAndReset:true,feedbackAndObservation:true,exactSavedEventDuringConcurrentEdit:true,staleReceiptsExcludedAfterRenderFailure:true,legacyDefaults:true,invalidResults,mobile,pageErrors:errors,artRequestCount:artRequests.length};
    fs.writeFileSync(evidence+'/browser-results.json',JSON.stringify(report,null,2)+'\n');
    fs.writeFileSync(evidence+'/saved-battle-recipe.json',JSON.stringify(b,null,2)+'\n');
    console.log(JSON.stringify(report,null,2));
    await context.close();
  } finally {await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1});
