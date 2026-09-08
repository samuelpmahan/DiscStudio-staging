"""Verify a DiscStudio consumer against retained artwork through its real HTTP API."""
import argparse
import hashlib
import importlib.metadata
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import urllib.request

parser = argparse.ArgumentParser()
parser.add_argument('--consumer', type=Path, required=True)
parser.add_argument('--art-library', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
scaling = args.art_library / 'component-scaling'
recipes = {r['id']: r for r in json.loads((scaling / 'recipes.json').read_text())['recipes']}
manifest = json.loads((scaling / 'corrected/manifest.json').read_text())
results = []
with tempfile.TemporaryDirectory() as data:
    with tempfile.TemporaryFile(mode='w+') as log:
        server = subprocess.Popen([sys.executable, str(args.consumer / 'app.py'), '--root', data, '--port', '0'], stdout=subprocess.PIPE, stderr=log, text=True)
        try:
            line = server.stdout.readline().strip()
            if not line.startswith('READY http://'):
                log.seek(0)
                raise RuntimeError('Server failed: ' + line + log.read())
            url = line.removeprefix('READY ').rstrip('/')
            for artifact in manifest['renders']:
                recipe = recipes[artifact['recipeId']]
                payload = {'family': recipe['family'], 'seed': recipe['seed'], 'base': recipe['palette']['base'], 'accent': recipe['palette']['accent'], 'label': recipe['label'], 'targetPx': artifact['targetPx'], 'version': 'components-v2'}
                request = urllib.request.Request(url + '/api/art', data=json.dumps(payload).encode(), headers={'Content-Type': 'application/json'})
                with urllib.request.urlopen(request, timeout=10) as response:
                    result = json.load(response)
                retained = (scaling / artifact['path']).read_bytes()
                digest = hashlib.sha256(retained).hexdigest()
                assert digest == artifact['sha256'], artifact['path']
                assert result['svg'].encode() == retained, artifact['path']
                assert result['receipt']['outputSha256'] == digest
                evidence = result['receipt']['compositionEvidence']
                assert evidence['pyto']['version'] == importlib.metadata.version('pyto-lab')
                composition = evidence['composition']
                assert composition['adapterSourceSha256'] == hashlib.sha256((args.consumer / 'app.py').read_bytes()).hexdigest()
                invocation = composition['ticks'][0]['calculations'][0]
                assert invocation['calculation'] == 'fn.discArt.render'
                assert invocation['inputs'] == {'value': 'px:px.disc.art.request'}
                assert invocation['into'] == 'px.disc.art.svg'
                for name, recorded in evidence['pyto']['moduleSourceSha256'].items():
                    source = Path(importlib.util.find_spec(name).origin)
                    assert hashlib.sha256(source.read_bytes()).hexdigest() == recorded, name
                results.append({'recipeId': artifact['recipeId'], 'targetPx': artifact['targetPx'], 'identicalSvg': True, 'outputSha256': digest, 'compositionEvidence': evidence})
            assert not list(Path(data).rglob('*.json'))
            assert not (Path(data) / 'data/events.jsonl').exists()
        finally:
            server.terminate()
            server.wait(timeout=10)
report = {'consumer': str(args.consumer), 'installedPyto': importlib.util.find_spec('pyto').origin, 'renders': results, 'renderingDidNotWriteUserData': True}
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(json.dumps(report, indent=2) + '\n')
print(f'{len(results)}/{len(manifest["renders"])} retained SVGs identical through installed pyto; source receipts verified; no render data writes.')
