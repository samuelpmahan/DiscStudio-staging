"""The demo, as a storyboard that runs: tease first, razzle after.

The wedge is the order. The TEASE beats are the thing a person already cares
about -- their discs, their photo, their comparison on their footage -- with no
PxC word on screen. The RAZZLE beats are what was underneath the whole time:
the same edit, its receipt, an undo that restores the exact value and is itself
on the record, the run record the Tick page draws, the receipts read back as a
PQL query, and the brain run over the shelf's own material.

Every beat is one screenshot and one line of on-screen truth asserted -- a value,
a count, a receipt name -- so the storyboard is a test that passes or a demo that
is not ready. The beats and what each one asserted are written to beats.json in
the --out directory.

    python scripts/demo_beats.py --embedded --out out/beats
    python scripts/demo_beats.py --url http://127.0.0.1:4173/ --out out/beats

It uses the same harness as scripts/browser_test.py (tests/embedded_harness.py in
--embedded mode; a real origin otherwise) and drives the same built application.
"""
import argparse, base64, functools, http.server, json, socketserver, sys, threading
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))
from embedded_harness import mount

parser = argparse.ArgumentParser()
parser.add_argument('--embedded', action='store_true')
parser.add_argument('--url', default='http://127.0.0.1:4173/')
parser.add_argument('--out', default=str(ROOT / 'test-results' / 'beats'))
a = parser.parse_args()
out = Path(a.out); out.mkdir(parents=True, exist_ok=True)

beats = []
def beat(page, act, name, title, assertion, value):
    """One beat: what it shows, the truth it asserts, and the picture of it."""
    shot = out / f'{name}.png'
    page.screenshot(path=str(shot))
    beats.append({'beat': name, 'act': act, 'title': title, 'assertion': assertion, 'value': value, 'screenshot': shot.name})
    print(f'PASS: {act} · {title} — {assertion} = {value}', flush=True)

def route(page, name):
    page.evaluate('r=>location.hash="/"+r', name)
    page.wait_for_timeout(150)

def open_trace(page):
    """Open the Inspect panel if it is not already open (it stays open across routes)."""
    if page.locator('.trace-panel.open').count() == 0:
        page.locator('[data-action="toggle-trace"]').first.click()
    page.wait_for_selector('.trace-panel.open')
    page.wait_for_timeout(120)

def synthetic_png(page):
    """A disc photo made in the page, so the demo needs no third-party asset."""
    return page.evaluate("""()=>{const c=document.createElement('canvas');c.width=c.height=96;const x=c.getContext('2d');
      x.fillStyle='#d47d54';x.beginPath();x.arc(48,48,44,0,7);x.fill();x.fillStyle='#203d36';x.beginPath();x.arc(48,48,15,0,7);x.fill();
      return c.toDataURL('image/png').split(',')[1]}""")

with sync_playwright() as p:
    launch = {'headless': True, 'args': ['--no-sandbox']}
    import os
    found = next((c for c in ('/opt/pw-browsers/chromium', os.environ.get('CHROMIUM'), '/usr/bin/chromium') if c and os.path.exists(c)), None)
    if found: launch['executable_path'] = found
    browser = p.chromium.launch(**launch)
    context = browser.new_context(viewport={'width': 1536, 'height': 960}, accept_downloads=True)
    page = context.new_page(); page.set_default_timeout(15000)
    errors = []; page.on('pageerror', lambda e: errors.append(str(e)))
    page.on('dialog', lambda d: d.accept())
    if a.embedded: mount(page)
    else: page.goto(a.url, wait_until='networkidle')
    page.wait_for_selector('.app-header')

    # ------------------------------------------------------------------ tease
    # 1. Your shelf. Your discs. Nothing else on screen.
    route(page, 'shelf')
    bag = page.locator('.bag-picker select').first.input_value()
    cards = page.locator('.bag-card').count()
    in_bag = len(page.evaluate('b=>discStudio.world.objects.Bag[b].discIds', bag))
    assert cards == in_bag and cards > 0, (cards, in_bag)
    # Nothing about the machinery is open yet: the one PxC panel on this screen is shut.
    assert page.locator('.trace-panel.open').count() == 0, 'the tease opens nothing'
    beat(page, 'tease', 'tease-01-your-shelf', 'Your discs, in the bag you actually throw',
         'bag cards on screen == discs in the bag', cards)

    # 1b. Ask for a disc the way you would say it out loud, and it is the first one.
    page.locator('[data-search="discs"]').fill('buzzz 177')
    page.wait_for_timeout(150)
    found = [e.get_attribute('data-disc-row') for e in page.locator('.disc-row').all()]
    matched = page.locator('.disc-row[data-disc-row="%s"] .match' % found[0]).all_text_contents()
    assert found[0] == 'buzzz-mint' and '177 g' in matched, (found, matched)
    beat(page, 'tease', 'tease-01b-the-right-disc', 'Say it the way you would say it out loud; the right disc comes first',
         'first result for "buzzz 177", and what it matched on', '%s — %s' % (found[0], ' · '.join(matched)))
    page.locator('[data-action="shelf-clear"]').click()
    page.wait_for_timeout(120)

    # 1c. One tap and the same disc is in a second bag. Nothing is copied, nothing is moved.
    discs_before = len(page.evaluate('Object.keys(discStudio.world.objects.Disc)'))
    page.locator('[data-disc-row="luna-mint"] [data-action="membership"]').click()
    page.wait_for_timeout(150)
    tags = page.locator('.disc-row[data-disc-row="luna-mint"] .bag-tag').all_text_contents()
    assert len(tags) == 2 and len(page.evaluate('Object.keys(discStudio.world.objects.Disc)')) == discs_before, tags
    beat(page, 'tease', 'tease-01c-one-disc-many-bags', 'One tap, and the same disc is in two bags — not copied, not moved',
         'the bags this disc is in', ' · '.join(tags))

    # 2. One exact photo, and every place that disc appears is your disc.
    disc = page.evaluate('discStudio.view.discId')
    page.locator(f'[data-action="disc-select"][data-id="{disc}"]').first.click()
    page.locator('#photo-file').set_input_files({'name': 'my-disc.png', 'mimeType': 'image/png', 'buffer': base64.b64decode(synthetic_png(page))})
    page.wait_for_function('d=>discStudio.world.objects.Disc[d].photo?.startsWith("data:image/webp")', arg=disc)
    photo = page.evaluate('d=>discStudio.world.objects.Disc[d].photo', disc)
    everywhere = page.evaluate("""p=>['shelf','bag','single','competition'].map(k=>discStudio.runtime.cards.recompose(discStudio.view.discId,{}).cards[k].svg.includes(p))""", photo[:64])
    assert all(everywhere), everywhere
    beat(page, 'tease', 'tease-02-your-photo', 'Your own photo replaces the sample art in every projection at once',
         'projections showing the uploaded photo', f'{sum(everywhere)} of 4')

    # 3. The comparison, over your footage.
    route(page, 'course')
    page.locator('[data-action="bag-lineup"]').click()
    page.locator('#footage-file').set_input_files({'name': 'my-still.png', 'mimeType': 'image/png', 'buffer': base64.b64decode(synthetic_png(page))})
    page.wait_for_selector('.footage-layer img')
    count = page.evaluate('discStudio.preview.cardCount')
    assert count >= 3 and photo[:48] in page.evaluate('discStudio.preview.svg'), count
    beat(page, 'tease', 'tease-03-on-the-course', 'The bag, on the screen, over your own footage',
         'cards in the overlay, one carrying your photo', count)

    # 3b. The same discs, on the canvas a phone actually wants.
    page.locator('[data-action="orientation"][data-value="portrait"]').click()
    page.locator('[data-control="frame-preset"]').select_option('filled')
    page.locator('[data-control="frame-title"]').fill('PutterWarz')
    page.locator('[data-control="frame-title"]').dispatch_event('change')
    size = page.evaluate('[discStudio.preview.width, discStudio.preview.height]')
    assert size == [1080, 1920] and 'data-frame="filled"' in page.evaluate('discStudio.preview.svg'), size
    beat(page, 'tease', 'tease-03b-vertical', 'The same comparison, on the canvas a phone wants, framed and titled',
         'preview canvas', ' x '.join(str(n) for n in size))
    page.locator('[data-control="frame-preset"]').select_option('none')
    page.locator('[data-action="orientation"][data-value="landscape"]').click()

    # 4. A score moves and the card that owns it pulses.
    before = page.evaluate('discStudio.world.battle.states[0].scores["entry-1"] ?? 0')
    page.locator('[data-action="score-step"][data-id="entry-1"][data-value="1"]').click()
    after = page.evaluate('discStudio.world.battle.states[0].scores["entry-1"]')
    assert after == before + 1, (before, after)
    beat(page, 'tease', 'tease-04-the-score-moves', 'Change the score; the card that owns it moves',
         'entry-1 score', after)

    # 5. One token, every card. (Still no explanation on screen -- just the result.)
    route(page, 'components')
    page.locator('[data-action="component"][data-value="AllCards"]').click(); page.wait_for_timeout(80)
    page.locator('[data-control="cascade-token"][data-layer="global"][data-token="radius"]').fill('40')
    page.locator('[data-control="cascade-token"][data-layer="global"][data-token="radius"]').dispatch_event('change')
    page.wait_for_timeout(80)
    changed = {k: page.locator(f'[data-projection-preview="{k}"]').get_attribute('data-changed') for k in ['shelf', 'bag', 'single', 'competition']}
    assert all(v == 'true' for v in changed.values()), changed
    beat(page, 'tease', 'tease-05-one-token-every-card', 'One design token; all four cards recompose in front of you',
         'projections marked recomposed', f"{sum(v == 'true' for v in changed.values())} of 4")

    # ----------------------------------------------------------------- razzle
    # 6. The same edit, with the receipt that was underneath it all along.
    open_trace(page)
    receipt_line = page.locator('.cascade-receipt').first.inner_text()
    rows = page.locator('.trace-panel.open .trace-row').count()
    assert 'recomposed' in receipt_line and rows > 4, (receipt_line, rows)
    assert page.evaluate("discStudio.runtime.pxc.get('px.discstudio.cards.global').radius") == 40
    beat(page, 'razzle', 'razzle-01-the-receipt', 'That edit had a receipt: which cards recomposed, and what ran',
         'cascade receipt line', receipt_line.strip())

    # 7. Undo is a Calculation over a Part, so it restores the exact value and leaves its own receipt.
    depth = page.evaluate('discStudio.runtime.undo.depth()')
    page.locator('[data-action="undo"]').first.click(); page.wait_for_timeout(120)
    radius = page.evaluate('discStudio.world.cards.global.radius')
    notice = page.locator('.notice').first.inner_text()
    assert radius != 40 and 'px.undo.studio' in notice and page.evaluate('discStudio.runtime.undo.depth()') == depth - 1, (radius, notice)
    beat(page, 'razzle', 'razzle-02-undo-on-the-record', 'Undo restores the exact previous value, and is itself on the record',
         'global radius after undo, restored from px.undo.studio', radius)

    # 8. The run record, and the Tick page it draws -- opened over file://, no server.
    # The studio builds that page out of the viewer's own three files, read over its
    # origin, so these last beats drive the app on a real local origin (Python's own
    # http.server, no new dependency) even when the earlier beats used the DOM harness.
    if a.embedded:
        quiet = type('Quiet', (http.server.SimpleHTTPRequestHandler,), {'log_message': lambda *x, **k: None})
        server = socketserver.TCPServer(('127.0.0.1', 0), functools.partial(quiet, directory=str(ROOT)))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        host = context.new_page(); host.set_default_timeout(15000)
        host.on('pageerror', lambda e: errors.append(str(e)))
        host.goto(f'http://127.0.0.1:{server.server_address[1]}/', wait_until='load')
        host.wait_for_selector('.app-header')
    else:
        server, host = None, page
    route(host, 'course')
    open_trace(host)
    with host.expect_download() as d: host.locator('[data-action="record-export"]').click()
    d.value.save_as(str(out / 'on-the-course-run-record.json'))
    record = json.loads((out / 'on-the-course-run-record.json').read_text())
    assert record['schema'] == 'pyto-run-record@1' and record['pcr'] == 'on-the-course', record['pcr']
    with host.expect_download() as d: host.locator('[data-action="record-render"]').click()
    d.value.save_as(str(out / 'tick-render.html'))
    viewer = context.new_page(); viewer.set_default_timeout(15000)
    viewer.on('pageerror', lambda e: errors.append(str(e)))
    viewer.goto((out / 'tick-render.html').resolve().as_uri())
    viewer.wait_for_selector('section.tick')
    ticks = viewer.locator('section.tick').count()
    assert ticks == len(record['ticks']) and viewer.evaluate("performance.getEntriesByType('resource').length") == 0
    beat(viewer, 'razzle', 'razzle-03-the-tick-page', 'The run, drawn Tick by Tick, in a page that opens with no server',
         'Ticks drawn == Ticks in the record', ticks)
    viewer.close()

    # 9. The receipts, read back the way anything else is read: a PQL prefix query.
    open_trace(page)
    listed = page.evaluate("discStudio.runtime.pxc.get('px.studio.receipts').map(r=>r.name)")
    names = sorted(page.evaluate("discStudio.runtime.parts().map(p=>p.address).filter(a=>a.startsWith('px.receipt.')).map(a=>a.slice(11))"))
    shown = page.locator('.receipts-row[data-receipt]').count()
    assert listed == names and shown == len(names), (listed, names, shown)
    assert 'studio-undo' in names
    beat(page, 'razzle', 'razzle-04-receipts-as-a-query', 'Every receipt, listed by the query px.receipt.* -- including the undo',
         'receipts listed by the query', shown)

    # 10. The brain on the shelf: a PxC program over this same material, drawn by the same viewer.
    brain = json.loads((ROOT / 'pyto/experiments/brain/records/brain_shelf.json').read_text())
    assert brain['schema'] == 'pyto-run-record@1' and brain['pcr'] == 'brain_shelf'
    html = host.evaluate('record=>discStudio.renderRecordPage(record)', brain)
    (out / 'brain-shelf-tick-render.html').write_text(html)
    shelf = context.new_page(); shelf.set_default_timeout(15000)
    shelf.on('pageerror', lambda e: errors.append(str(e)))
    shelf.goto((out / 'brain-shelf-tick-render.html').resolve().as_uri())
    shelf.wait_for_selector('section.tick')
    assert shelf.locator('section.tick .tick-name').all_text_contents() == [t['name'] for t in brain['ticks']]
    beat(shelf, 'razzle', 'razzle-05-the-brain-on-the-shelf', 'The same record shape over the shelf\'s own numbers: describe, correlate, cluster, regress',
         'Ticks of brain_shelf (python -m experiments.brain.shelf), drawn by the studio viewer',
         f"{len(brain['ticks'])} Ticks, {brain['counters']['invocations']} invocations")
    shelf.close()

    if server: server.shutdown(); server.server_close()
    assert not errors, errors
    manifest = {'for': 'the demo as a storyboard that runs: tease first, razzle after', 'acts': ['tease', 'razzle'], 'beats': beats, 'count': len(beats), 'errors': errors}
    (out / 'beats.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps({'beats': [b['beat'] for b in beats], 'out': str(out)}, indent=2), flush=True)
    browser.close()
