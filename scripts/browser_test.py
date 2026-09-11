"""Browser interaction/export checks. CI uses HTTP and real origin storage.
--embedded uses a disclosed localStorage test double for restricted local environments.
"""
import argparse, base64, functools, hashlib, http.server, json, os, socketserver, struct, sys, threading
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tests'))
from embedded_harness import mount
parser=argparse.ArgumentParser()
parser.add_argument('--embedded', action='store_true')
parser.add_argument('--url', default='http://127.0.0.1:4173/')
parser.add_argument('--out', default=str(ROOT/'test-results'))
a=parser.parse_args();out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
checks=[]
def record(name): checks.append(name); print('PASS:',name,flush=True)
def route(page,name):
    page.evaluate('(r)=>location.hash="/"+r',name)
    page.wait_for_timeout(120)
def change(page,selector,value):
    page.locator(selector).fill(str(value));page.locator(selector).dispatch_event('change')
def assert_world(page,js): assert page.evaluate('()=>'+js),js
with sync_playwright() as p:
    launch={'headless':True,'args':['--no-sandbox']}
    if a.embedded:
        # the first Chromium that exists: this checkout's bundled Playwright browser,
        # $CHROMIUM, the Debian path; else Playwright's own default
        found=next((c for c in ('/opt/pw-browsers/chromium',os.environ.get('CHROMIUM'),'/usr/bin/chromium') if c and os.path.exists(c)),None)
        if found: launch['executable_path']=found
    browser=p.chromium.launch(**launch)
    context=browser.new_context(viewport={'width':1536,'height':960},accept_downloads=True)
    page=context.new_page();page.set_default_timeout(10000)
    errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    page.on('dialog',lambda d:d.accept('Test state' if d.type=='prompt' else None))
    if a.embedded:mount(page)
    else:page.goto(a.url,wait_until='networkidle')
    page.wait_for_selector('.app-header')
    route(page,'components')
    assert page.locator('[data-path="disc.mold.name"]').is_visible()
    assert page.locator('[data-path="disc.mold.manufacturer.name"]').is_visible()
    assert page.locator('[data-path="disc.mold.manufacturer.name"]').bounding_box()['y']<800
    page.locator('[data-path="disc.mold.manufacturer.name"]').click()
    change(page,'[data-control="node-number"][data-key="size"]',16)
    assert_world(page,'discStudio.world.presets.broadcast.nodes.find(n=>n.id==="maker").size===16')
    page.locator('[data-path="disc.mold.name"]').click()
    node=page.locator('[data-node-select="mold"]').last;rect=node.bounding_box()
    before=page.evaluate('discStudio.world.presets.broadcast.nodes.find(n=>n.id==="mold").x')
    page.mouse.move(rect['x']+rect['width']/2,rect['y']+rect['height']/2)
    page.mouse.down();page.mouse.move(rect['x']+rect['width']/2+16,rect['y']+rect['height']/2+8,steps=3);page.mouse.up()
    assert_world(page,f'discStudio.world.presets.broadcast.nodes.find(n=>n.id==="mold").x>{before}')
    record('Manufacturer/mold first-class bindings; styling and pointer dragging edit the real preset')
    page.locator('[data-action="field-new"]').click()
    page.locator('#new-field-label').fill('My rating')
    page.locator('[data-control="new-field-type"]').select_option('number')
    page.locator('[data-action="field-register"]').click()
    assert page.locator('[data-path="disc.myRating"]').count()==1
    route(page,'shelf');change(page,'[data-control="disc-field"][data-key="myRating"]',9)
    assert_world(page,'discStudio.world.objects.Disc["buzzz-mint"].myRating===9')
    route(page,'components');page.locator('[data-path="disc.myRating"]').click()
    assert_world(page,'discStudio.world.presets.broadcast.nodes.some(n=>n.binding==="disc.myRating")')
    page.locator('[data-search="fields"]').fill('');page.locator('[data-path="disc.mold.name"]').click()
    record('Schema-added field automatically appears in both fact editing and the customizer')
    route(page,'course')
    assert page.locator('[data-action="export-png"]').bounding_box()['y']<500
    page.locator('[data-action="score-step"][data-id="entry-1"][data-value="1"]').click()
    assert_world(page,'discStudio.world.battle.states[0].scores["entry-1"]===1')
    page.locator('[data-action="state-add"]').click()
    page.locator('[data-action="score-step"][data-id="entry-1"][data-value="1"]').click()
    page.locator('[data-action="state-select"][data-id="state-1"]').click()
    assert_world(page,'discStudio.world.battle.states[0].scores["entry-1"]===1 && discStudio.world.battle.states[1].scores["entry-1"]===2')
    assert_world(page,'discStudio.preview.run.trace.filter(t=>t.call==="fn.disc.art").every(t=>t.reused)')
    record('Independent comparison states and scores reuse actual upstream PxC art')
    # A deliberately synthetic upload exercises the exact-photo path without third-party assets.
    data=page.evaluate('''()=>{const c=document.createElement('canvas');c.width=c.height=64;const x=c.getContext('2d');x.fillStyle='#d47d54';x.beginPath();x.arc(32,32,28,0,7);x.fill();return c.toDataURL('image/png').split(',')[1]}''')
    page.locator('#photo-file').set_input_files({'name':'test-disc.png','mimeType':'image/png','buffer':base64.b64decode(data)})
    page.wait_for_function('discStudio.world.objects.Disc["buzzz-mint"].photo?.startsWith("data:image/webp")')
    page.locator('#footage-file').set_input_files({'name':'test-still.png','mimeType':'image/png','buffer':base64.b64decode(data)})
    page.wait_for_selector('.footage-layer img')
    svg=page.evaluate('discStudio.preview.svg')
    assert 'data:image/webp' in svg and 'blob:' not in svg
    page.locator('[data-action="toggle-trace"]').first.click()
    assert page.locator('.trace-panel.open .trace-row').count()>2
    page.locator('[data-action="toggle-trace"]').first.click()
    with page.expect_download() as d: page.locator('[data-action="export-png"]').click()
    download=d.value;download.save_as(str(out/'overlay.png'))
    png=(out/'overlay.png').read_bytes();assert png[:8]==b'\x89PNG\r\n\x1a\n'
    assert struct.unpack('>II',png[16:24])==(1920,1080)
    receipt=page.evaluate('discStudio.world.exports.at(-1)')
    assert receipt['pngHash']==hashlib.sha256(png).hexdigest()
    alpha=page.evaluate('''async data=>{const img=new Image();img.src='data:image/png;base64,'+data;await img.decode();const c=document.createElement('canvas');c.width=1920;c.height=1080;const x=c.getContext('2d');x.drawImage(img,0,0);return [x.getImageData(960,100,1,1).data[3],x.getImageData(0,0,1,1).data[3]]}''',base64.b64encode(png).decode())
    assert alpha==[0,0]
    assert 'photo' not in receipt['sourceSnapshot']['objects']['buzzz-mint']['disc']
    record('Exact uploaded photo reaches SVG/PNG; transparent 1920×1080 export hash matches actual bytes; footage excluded')
    # Item comments use the real neat custom element and its original inspection contract.
    review=page.locator('neat-review');review.locator('#open').click()
    comment=review.locator('textarea[data-review-id="bindings"]')
    comment.fill('Keep manufacturer distinct; move it a little higher.')
    review.locator('[data-t="presentations"][data-p="bindings"]').check()
    review.locator('[aria-label="Reviewer name"]').fill('Automated test inspector')
    with page.expect_download() as d:review.locator('#export').click()
    d.value.save_as(str(out/'inspection.json'));inspection=json.loads((out/'inspection.json').read_text())
    assert inspection['inspected']['bindings'] and inspection['comments']['bindings'].startswith('Keep manufacturer')
    assert inspection['acceptance']=='not-recorded' and inspection['contexts']['bindings']['route']=='#/course'
    review.locator('#hide').click()
    record('Specific neat comments export with inspected flags, context and checkpoint; no acceptance is fabricated')
    # Rehydrate either actual origin storage or the explicitly disclosed memory double.
    if a.embedded:
        saved=page.evaluate('Object.fromEntries(testStorage)');page.close();page=context.new_page();page.on('pageerror',lambda e:errors.append(str(e)));mount(page,saved)
    else:page.reload(wait_until='networkidle')
    assert_world(page,'discStudio.world.objects.Disc["buzzz-mint"].myRating===9 && discStudio.world.exports.length===1')
    review=page.locator('neat-review');review.locator('#open').click()
    assert review.locator('textarea[data-review-id="bindings"]').input_value().startswith('Keep manufacturer')
    review.locator('#hide').click()
    record('Workspace, uploaded photo, presets and item comments rehydrate'+(' (memory storage double)' if a.embedded else ' (actual localStorage/page reload)'))
    route(page,'competition')
    for team in ['team-luna','team-zone']:
        for _ in range(3):page.locator(f'[data-action="throw-record"][data-id="{team}"]').click()
    assert page.locator('.section-heading .result-status.pass').count()==1
    page.locator('[data-action="throw-record"][data-id="team-luna"]').click()
    assert page.locator('.section-heading .result-status.fail').count()==1
    record('Competition UI records real team throws and changes composed status from pending to pass to fail')
    # The studio builds the Tick render page from the viewer's own three files, read
    # over its origin, so this block drives the real app on a real local origin
    # (Python standard library, no new dependency). The page it produces is then
    # opened over file:// with no server at all, which is the claim being checked.
    quiet=type('Quiet',(http.server.SimpleHTTPRequestHandler,),{'log_message':lambda *a,**k:None})
    server=socketserver.TCPServer(('127.0.0.1',0),functools.partial(quiet,directory=str(ROOT)))
    threading.Thread(target=server.serve_forever,daemon=True).start()
    studio=context.new_page();studio.set_default_timeout(10000)
    studio.on('pageerror',lambda e:errors.append(str(e)))
    studio.goto(f'http://127.0.0.1:{server.server_address[1]}/',wait_until='load')
    studio.wait_for_selector('.app-header')
    route(studio,'course?trace=1')
    with studio.expect_download() as d: studio.locator('[data-action="record-export"]').click()
    d.value.save_as(str(out/'run-record.json'));run_record=json.loads((out/'run-record.json').read_text())
    assert run_record['schema']=='pyto-run-record@1' and run_record['pcr']=='on-the-course'
    assert run_record['source']['runtime']=='discstudio'
    pql=studio.evaluate('discStudio.preview.run.composition.Ticks')
    assert [t['name'] for t in run_record['ticks']]==[t['name'] for t in pql]
    assert [len(t['invocations']) for t in run_record['ticks']]==[len(t['Calculations']) for t in pql]
    assert run_record['counters']['invocations']==sum(len(t['invocations']) for t in run_record['ticks'])
    # Kept as a Part at the reserved `run` second segment; never written into a fact.
    # JSON round-trip inside the page, matching downloadJson's own serialization: an
    # `undefined` node.field (e.g. the cascade's static sponsor lockup text node, which
    # has no bound domain field) is dropped by JSON.stringify but would otherwise come
    # back from evaluate() as an explicit null, which is a Playwright serialization
    # artifact, not a difference in what was actually recorded.
    assert studio.evaluate('JSON.parse(JSON.stringify(discStudio.runtime.pxc.get("px.run.on-the-course")))')==run_record
    assert studio.evaluate('discStudio.runtime.parts().some(p=>p.address==="px.run.on-the-course")')
    assert not studio.evaluate('discStudio.runtime.parts().some(p=>p.address.startsWith("px.domain.")&&p.value&&p.value.schema)')
    with studio.expect_download() as d: studio.locator('[data-action="record-render"]').click()
    d.value.save_as(str(out/'tick-render.html'))
    assert '<script type="application/json" id="record">' in (out/'tick-render.html').read_text()
    viewer=context.new_page();viewer.set_default_timeout(10000)
    viewer.on('pageerror',lambda e:errors.append(str(e)))
    viewer.goto((out/'tick-render.html').resolve().as_uri())
    viewer.wait_for_selector('section.tick')
    assert viewer.locator('section.tick').count()==len(run_record['ticks'])
    assert viewer.locator('section.tick .tick-name').all_text_contents()==[t['name'] for t in run_record['ticks']]
    assert viewer.evaluate("performance.getEntriesByType('resource').length")==0,'the standalone page fetched something'
    # The same sample composition with parallel: true -- one Tick per stage, every
    # card's branch of that stage at once (src/runtime.js sceneParallel). The record
    # carries the schedule the Python kernel writes and the Tick page draws the Tick
    # side by side.
    parallel=studio.evaluate("""async()=>{await discStudio.runtime.sceneParallel({});const {address,record}=discStudio.runtime.runRecord('on-the-course-parallel');return {address,record};}""")
    prec=parallel['record']
    assert prec['parallel'] is True,prec.get('parallel')
    assert prec['budget']=={'limit_ms':None,'stopped_after_tick':None,'completed':True},prec['budget']
    assert parallel['address']=='px.run.on-the-course-parallel'
    assert all(t['latency_ms'] is not None for t in prec['ticks'])
    # A Tick is a true fan (independent branches, drawn "parallel") only when every
    # invocation shares one calculation address; the cascade's own "Cascade" Tick now
    # merges N entries' two-Calculation chains (fn.cards.effective -> fn.cards.apply)
    # into one Tick with >1 invocations across two addresses, which is genuinely a
    # chain, not a fan, and the viewer marks it .chain accordingly.
    is_fan=lambda t:len(t['invocations'])>1 and len({i['calculation']['address'] for i in t['invocations']})==1
    fan=next(t for t in prec['ticks'] if is_fan(t))
    assert [i['placement']['worker'] for i in fan['invocations']]==list(range(len(fan['invocations']))),fan
    assert all(i['placement']['started_ms']>=0 for t in prec['ticks'] for i in t['invocations'])
    html=studio.evaluate("record=>discStudio.renderRecordPage(record)",prec)
    (out/'parallel-tick-render.html').write_text(html)
    branches=context.new_page();branches.set_default_timeout(10000)
    branches.on('pageerror',lambda e:errors.append(str(e)))
    branches.goto((out/'parallel-tick-render.html').resolve().as_uri())
    branches.wait_for_selector('section.tick.parallel')
    assert branches.locator('section.tick.parallel').count()==sum(1 for t in prec['ticks'] if is_fan(t))
    assert branches.locator('section.tick.parallel[data-tick="%d"] .branches .branch'%fan['index']).count()==len(fan['invocations'])
    box=[branches.locator('section.tick.parallel[data-tick="%d"] .branches .branch'%fan['index']).nth(i).bounding_box() for i in range(len(fan['invocations']))]
    assert len({round(b['y']) for b in box})==1,'the branches of a parallel Tick are drawn side by side, on one row'
    record('The sample composition runs with parallel: true, its exported record validates and carries parallel, placement, latency_ms and budget, and the Tick page draws the parallel Tick side by side')
    server.shutdown();server.server_close()
    record('Export run record writes a validated pyto-run-record@1 Part and file; its Tick render page opens over file:// with one section per Tick and no requests')
    # The studio's own receipts, read back on the Inspect page through the PQL
    # prefix query px.receipt.* (src/core/exec.js), with an Undo taken in the
    # browser as the invocation that has to show up there.
    route(page,'shelf')
    depth=page.evaluate('discStudio.runtime.undo.depth()')
    discs=page.evaluate('Object.keys(discStudio.world.objects.Disc).length')
    page.locator('[data-action="disc-duplicate"]').click()
    assert page.evaluate('Object.keys(discStudio.world.objects.Disc).length')==discs+1
    assert page.evaluate('discStudio.runtime.undo.depth()')==depth+1,'the edit was not recorded on px.undo.studio'
    page.locator('[data-action="undo"]').click()
    assert page.evaluate('Object.keys(discStudio.world.objects.Disc).length')==discs,'undo did not restore the exact previous world'
    assert_world(page,'discStudio.world.objects.Disc["buzzz-mint"].myRating===9')
    assert page.evaluate('discStudio.runtime.undo.depth()')==depth
    assert page.evaluate('discStudio.runtime.pxc.get("px.undo.studio").scope')=='studio'
    route(page,'course')
    # Open, close, open: the query runs at render time, so the first opening writes
    # its own px.receipt.studio-receipts and the next one lists it like any other.
    for _ in range(3):page.locator('[data-action="toggle-trace"]').first.click()
    rows=page.locator('.receipts-row[data-receipt]')
    listed=page.evaluate('discStudio.runtime.pxc.get("px.studio.receipts")')
    names=sorted(page.evaluate('discStudio.runtime.parts().map(p=>p.address).filter(a=>a.startsWith("px.receipt.")).map(a=>a.slice(11))'))
    assert [r['name'] for r in listed]==names,(listed,names)
    assert rows.count()==len(names),(rows.count(),names)
    assert [t.strip() for t in rows.locator('span:first-child').all_text_contents()]==names
    undone=next(r for r in listed if r['name']=='studio-undo')
    assert undone['produces']==['px.studio.world','px.undo.studio'],undone
    assert rows.locator('[data-digest="studio-undo"]').inner_text().strip()==undone['digest']
    assert page.evaluate('discStudio.runtime.pxc.get("px.studio.receipts.summary").receipts')==len(names)
    page.locator('[data-action="toggle-trace"]').first.click()
    record('Inspect lists the studio own receipts through the px.receipt.* PQL query, one row per receipt with its consumes, produces and result digest; an Undo taken in the browser restores the exact previous value and is itself a listed receipt')
    # The Course route (#/course-build): one capture through the LAB Stages, one
    # composition per Stage on the studio's own board. What is asserted is what
    # the record says -- px.exp.lab.pipeline, the produce Parts, the receipts --
    # and then that the raster carries a mark for every object the Stages found.
    route(page,'course-build')
    stages=page.evaluate('discStudio.lab().state.stages')
    assert len(stages)>=5,stages
    assert all(s['status']=='not-run' for s in stages),stages
    assert page.locator('[data-lab-stage]').count()==len(stages)
    page.locator('[data-action="lab-sample"]').first.click()
    page.wait_for_function('!!document.querySelector("[data-lab-canvas]")?.dataset.painted')
    page.locator('[data-action="lab-run"]').first.click()
    page.wait_for_function('!discStudio.lab().state.stages.some(s=>s.status==="not-run")',timeout=120000)
    state=page.evaluate('discStudio.lab().state')
    assert all(s['status']=='produced' for s in state['stages']),[(s['stage'],s['status'],s['reason']) for s in state['stages']]
    assert [s['composition'] for s in state['stages']][:5]==['lab-s0','lab-s1','lab-s2','lab-s3','lab-route']
    for stage in state['stages']:
        assert stage['produced'],stage
        for part in stage['produced']:
            assert page.evaluate('a=>discStudio.runtime.pxc.has(a)',part['address']),part
    assert page.locator('[data-lab-stage][data-status="produced"]').count()==len(state['stages'])
    # every Stage's produce is on the one raster: badges read, baskets, tees, the round's holes
    views=page.evaluate('discStudio.lab().views.map(v=>({key:v.key,kind:v.kind,tone:v.tone,n:v.objects.length,labels:v.objects.map(o=>o.label)}))')
    by_key={v['key']:v for v in views}
    assert set(by_key)>= {'s0','s1','s2','s3','route'},list(by_key)
    assert by_key['s1']['labels']==['hole 10','hole 1'],by_key['s1']
    assert by_key['route']['labels']==['hole 1','hole 10'],by_key['route']  # the order is the badge reading, not the position
    for key in ['s1','s2','s3']:
        assert page.locator('.lab-mark.tone-%s'%by_key[key]['tone']).count()==by_key[key]['n'],key
    assert page.locator('.lab-leg').count()==len(page.evaluate('discStudio.lab().views.find(v=>v.kind==="path").legs'))
    assert page.locator('.lab-overlay').get_attribute('viewBox')=='0 0 %d %d'%tuple(page.evaluate('[discStudio.runtime.lab.raster().widthPx,discStudio.runtime.lab.raster().heightPx]'))
    record('The Course route runs one capture through every landed Stage as lab-s0 … lab-route, each producing its Parts, and draws every produced object on the one canonical raster')
    # The selected object's Part, with the Calculation that published it, read off the receipts.
    page.locator('.lab-mark.tone-badge').first.click()
    assert page.locator('.inspector h2').inner_text().startswith('hole')
    assert page.locator('.inspector .binding-path').inner_text()=='px.exp.lab.badges.objects'
    provenance=page.evaluate('discStudio.runtime.lab.provenance("px.exp.lab.badges.objects")')
    assert provenance['composition']=='lab-s1' and provenance['call']=='fn.lab.s1.badges.declareownership',provenance
    assert provenance['tick'] in page.locator('.inspector').inner_text()
    # and the same Inspect panel every other route opens, now listing the Stage receipts
    page.locator('[data-action="toggle-trace"]').first.click()
    listed=page.evaluate('discStudio.runtime.pxc.get("px.studio.receipts").map(r=>r.name)')
    for name in ['lab-s0','lab-s1','lab-s2','lab-s3','lab-route']:
        assert name in listed,listed
        assert page.locator('.receipts-row[data-receipt="%s"]'%name).count()==1,name
    record('The inspector names the Part a selected object came from and the composition, Tick and Calculation that published it; Inspect lists every Stage receipt beside the studio\'s own')
    with page.expect_download() as d: page.locator('[data-action="record-export"]').click()
    d.value.save_as(str(out/'lab-run-record.json'));lab_record=json.loads((out/'lab-run-record.json').read_text())
    assert lab_record['schema']=='pyto-run-record@1' and lab_record['pcr'].startswith('lab-'),lab_record['pcr']
    assert [t['name'] for t in lab_record['ticks']]==page.evaluate('discStudio.runtime.pxc.get("px.pql.%s").Ticks.map(t=>t.name)'%lab_record['pcr'])
    page.locator('[data-action="toggle-trace"]').first.click()
    page.screenshot(path=str(out/'course-build.png'))
    record('A Stage run exports a validated pyto-run-record@1 the Tick viewer draws, Tick for Tick with its PQL document')
    # Reset screenshot state without erasing the verified export/review artifacts.
    page.evaluate('discStudio.runtime.dispatch({type:"battle.state.select",id:"state-1"})')
    for name in ['shelf','course','course-build','components','competition']:
        route(page,name);page.screenshot(path=str(out/(name+'.png')))
        assert not page.evaluate('document.documentElement.scrollWidth>innerWidth'),name
    page.set_viewport_size({'width':390,'height':844})
    for name in ['shelf','course','course-build','components','competition']:
        route(page,name);assert not page.evaluate('document.documentElement.scrollWidth>innerWidth'),name+' mobile overflow'
    page.screenshot(path=str(out/'mobile.png'))
    record('Five routes render at desktop and mobile widths without horizontal page overflow')
    page.set_viewport_size({'width':1536,'height':960})
    # Card cascade editor (task 79: the preset IS the projection layer, folded into
    # the Component Editor's "All cards" tab plus the DisplayCard inspector's "The
    # whole card" / "This disc, this projection" sections -- no more #/cards route).
    # `runtime.cards.recompose` is the acceptance test itself: a global edit changes
    # every projection that inherits the token, a preset edit changes exactly the
    # projections composing with that preset, and an instance edit changes one.
    route(page,'components')
    projections=['shelf','bag','single','competition']
    page.locator('[data-action="component"][data-value="AllCards"]').click();page.wait_for_timeout(60)
    page.screenshot(path=str(out/'cards.png'))
    assert page.locator('[data-projection-preview]').count()==4
    radius_global='[data-control="cascade-token"][data-layer="global"][data-token="radius"]'
    change(page,radius_global,'40')
    assert_world(page,'discStudio.world.cards.global.radius===40')
    changed={p:page.locator(f'[data-projection-preview="{p}"]').get_attribute('data-changed') for p in projections}
    assert all(v=='true' for v in changed.values()),changed
    assert all('40' in page.locator(f'[data-projection-preview="{p}"] svg').first.evaluate('e=>e.outerHTML') for p in projections)
    record('Editing the global radius recomposes all four projections; the preview grid marks every one "recomposed" and every composed SVG carries the new value')
    # The seed gives buzzz-mint an instance override on shelf.accent, so a global accent edit
    # reaches three projections and the shelf card keeps its own: the cascade, not a broadcast.
    accent_global='[data-control="cascade-token"][data-layer="global"][data-token="accent"]'
    change(page,accent_global,'#112233')
    assert_world(page,'discStudio.world.cards.global.accent==="#112233"')
    changed={p:page.locator(f'[data-projection-preview="{p}"]').get_attribute('data-changed') for p in projections}
    assert changed=={'shelf':'false','bag':'true','single':'true','competition':'true'},changed
    record('A global edit stops at an instance override: shelf keeps buzzz-mint\'s own accent and the other three recompose')
    # DisplayCard tab: edit broadcast's own accent (the preset IS the projection layer),
    # then back to All cards to see it land on exactly the projections that compose with it.
    page.locator('[data-action="component"][data-value="DisplayCard"]').click();page.wait_for_timeout(60)
    accent_preset='[data-control="preset-color"][data-key="accent"]'
    change(page,accent_preset,'#654321')
    assert_world(page,'discStudio.world.presets.broadcast.accent==="#654321"')
    ctx_js="{bagId:'everyday',competitionId:'putterwarz',roundId:'hole-1'}"
    assert page.evaluate(f"discStudio.runtime.cards.effective('single','buzzz-mint',{ctx_js}).tokens.accent")=='#654321'
    page.locator('[data-action="component"][data-value="AllCards"]').click();page.wait_for_timeout(60)
    changed={p:page.locator(f'[data-projection-preview="{p}"]').get_attribute('data-changed') for p in projections}
    assert changed=={'shelf':'false','bag':'false','single':'true','competition':'true'},changed
    assert all('#654321' in page.locator(f'[data-projection-preview="{p}"] svg').first.evaluate('e=>e.outerHTML') for p in ['single','competition'])
    record('Editing the preset accent control on the DisplayCard tab reaches both single and competition (they compose with broadcast) and leaves shelf/bag alone; both SVGs carry the new accent, and the grid marks both recomposed')
    # Reset to inherited, from the DisplayCard tab's "The whole card" section.
    page.locator('[data-action="component"][data-value="DisplayCard"]').click();page.wait_for_timeout(60)
    assert page.locator(accent_preset).input_value()=='#654321'
    page.locator('[data-action="cascade-reset"][data-layer="preset"][data-preset="broadcast"][data-token="accent"]').click()
    assert_world(page,'discStudio.world.presets.broadcast.accent===null')
    assert page.locator(accent_preset).input_value()==page.evaluate('discStudio.world.cards.global.accent'),'cleared override shows the inherited global value'
    record('Reset to inherited clears the preset\'s own override; the control shows the global value again')
    # Take the reset's own recompose on the All cards tab before the next edit: one edit, one recompose.
    page.locator('[data-action="component"][data-value="AllCards"]').click();page.wait_for_timeout(60)
    page.locator('[data-action="component"][data-value="DisplayCard"]').click();page.wait_for_timeout(60)
    instance_projection='[data-control="instance-projection"]'
    page.locator(instance_projection).select_option('single')
    radius_instance='[data-control="cascade-token"][data-layer="instance"][data-projection="single"][data-disc="buzzz-mint"][data-token="radius"]'
    change(page,radius_instance,'77')
    assert_world(page,'discStudio.world.cards.instances.single["buzzz-mint"].radius===77')
    page.locator('[data-action="component"][data-value="AllCards"]').click();page.wait_for_timeout(60)
    changed={p:page.locator(f'[data-projection-preview="{p}"]').get_attribute('data-changed') for p in projections}
    assert [p for p,v in changed.items() if v=='true']==['single'],changed
    receipt=page.evaluate('discStudio.cards().edit')
    assert receipt['layer']=='instance' and receipt['token']=='radius' and receipt['value']==77 and receipt['projection']=='single',receipt
    record('An instance edit on single recomposes exactly that card, and window.discStudio.cards() carries the edit')
    assert not page.evaluate('document.documentElement.scrollWidth>innerWidth'),'All cards tab overflow'
    page.set_viewport_size({'width':390,'height':844})
    assert not page.evaluate('document.documentElement.scrollWidth>innerWidth'),'All cards tab mobile overflow'
    page.locator('[data-action="component"][data-value="DisplayCard"]').click();page.wait_for_timeout(60)
    assert not page.evaluate('document.documentElement.scrollWidth>innerWidth'),'DisplayCard tab mobile overflow'
    page.set_viewport_size({'width':1536,'height':960})
    record('The Component Editor\'s All cards and DisplayCard tabs render at desktop and mobile widths without horizontal page overflow')
    assert not errors,errors
    record('No browser JavaScript errors')
    report={'mode':'embedded DOM; memory storage double; run-record block on a real local origin and file://' if a.embedded else 'HTTP; real origin storage','checks':checks,'count':len(checks),'errors':errors}
    (out/'browser-report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2),flush=True)
    browser.close()
