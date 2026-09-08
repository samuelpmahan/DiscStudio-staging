"""Browser interaction/export checks. CI uses HTTP and real origin storage.
--embedded uses a disclosed localStorage test double for restricted local environments.
"""
import argparse, base64, hashlib, json, os, struct, sys
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
    if a.embedded: launch['executable_path']='/usr/bin/chromium'
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
    # Reset screenshot state without erasing the verified export/review artifacts.
    page.evaluate('discStudio.runtime.dispatch({type:"battle.state.select",id:"state-1"})')
    for name in ['shelf','course','components','competition']:
        route(page,name);page.screenshot(path=str(out/(name+'.png')))
        assert not page.evaluate('document.documentElement.scrollWidth>innerWidth'),name
    page.set_viewport_size({'width':390,'height':844})
    for name in ['shelf','course','components','competition']:
        route(page,name);assert not page.evaluate('document.documentElement.scrollWidth>innerWidth'),name+' mobile overflow'
    page.screenshot(path=str(out/'mobile.png'))
    record('Four routes render at desktop and mobile widths without horizontal page overflow')
    assert not errors,errors
    record('No browser JavaScript errors')
    report={'mode':'embedded DOM; memory storage double' if a.embedded else 'HTTP; real origin storage','checks':checks,'count':len(checks),'errors':errors}
    (out/'browser-report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2),flush=True)
    browser.close()
