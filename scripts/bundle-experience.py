#!/usr/bin/env python3
"""Bundle this working Studio source, including uncommitted files, for a focused build.

Standard library only. Run again for a fresh snapshot; --verify checks an unpacked
baseline. Fixed source roots exclude Git/auth state, local drafts, installed
dependencies, generated images/builds and unrelated experiments' large evidence.
"""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
ROOTS = (
    'src', 'public', 'tests', 'scripts', 'docs', 'concept-b', 'experiments',
    'pyto/viewer', 'pyto/consumers/discstudio-card/port/painter',
    'evidence/card-render/attempt-02-lazy-signature',
    'evidence/card-render/baseline-941f354',
)
FILES = ('index.html', 'package.json', 'README.md', 'AGENTS.md', '.gitignore',
         'CLOUD-START.md', '.neat/items/DS-STUDIO-02.json')
SKIP_DIRS = {'__pycache__', 'node_modules', '.venv', '.git'}
SKIP_SUFFIXES = {'.pyc', '.pyo', '.DS_Store'}
PREFIX = 'discstudio-cloud'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def encoded(value):
    return (json.dumps(value, indent=2, sort_keys=True) + '\n').encode()


def inputs():
    paths = set()
    for name in ROOTS:
        directory = ROOT / name
        if not directory.is_dir() or directory.is_symlink():
            raise ValueError(f'Missing or symlinked input root: {name}')
        for path in directory.rglob('*'):
            relative = path.relative_to(ROOT)
            if any(part in SKIP_DIRS for part in relative.parts):
                continue
            if path.is_symlink():
                raise ValueError(f'Symlink is not a source snapshot: {relative}')
            if path.is_file() and path.suffix not in SKIP_SUFFIXES and path.name != '.DS_Store' and not path.name.startswith('.env'):
                paths.add(relative.as_posix())
    for name in FILES:
        if not (ROOT / name).is_file() or (ROOT / name).is_symlink():
            raise ValueError(f'Missing or symlinked input file: {name}')
        paths.add(name)
    for name in ('LICENSE', 'LICENSE.md', 'NOTICE'):
        if (ROOT / name).is_symlink():
            raise ValueError(f'Symlinked input file: {name}')
        if (ROOT / name).is_file():
            paths.add(name)
    return sorted(paths)


def git(*args):
    result = subprocess.run(['git', '-C', str(ROOT), *args], capture_output=True, text=True)
    return result.stdout.strip() if result.returncode == 0 else None


def verify(directory):
    directory = directory.resolve()
    manifest = json.loads((directory / 'bundle-manifest.json').read_text())
    if manifest.get('schemaVersion') != 1 or not manifest.get('files'):
        raise ValueError('Unknown or empty bundle manifest')
    failures = []
    for name, expected in manifest['files'].items():
        relative = PurePosixPath(name)
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError(f'Unsafe manifest path: {name}')
        path = directory / name
        if not path.resolve().is_relative_to(directory) or path.is_symlink():
            raise ValueError(f'Manifest path escapes the snapshot: {name}')
        if not path.is_file():
            failures.append(f'missing: {name}')
        else:
            data = path.read_bytes()
            if len(data) != expected['bytes'] or digest(data) != expected['sha256']:
                failures.append(f'changed: {name}')
    if failures:
        raise ValueError('\n'.join(failures))
    print(f"Verified {len(manifest['files'])} baseline files. Manifest SHA-256: "
          f"{digest((directory / 'bundle-manifest.json').read_bytes())}")


def bundle(output):
    names = inputs()
    payload = {name: (ROOT / name).read_bytes() for name in names}
    source = {
        'scope': 'Experience frame, then UDS photo/paint with three existing painters',
        'baseCommit': git('rev-parse', 'HEAD'),
        'branch': git('branch', '--show-current'),
        'workingTreeStatus': git('status', '--porcelain=v1'),
        'includesUncommittedSource': True,
        'roots': ROOTS,
        'rootFiles': FILES,
        'excluded': ['.git and credentials', 'node_modules and virtualenvs',
                     'dist and local test results', 'local browser drafts/photos',
                     'unrelated repos and the full Python runtime',
                     'historical evidence except the two required sealed test fixtures'],
        'notes': 'This is the actual local Studio source, not a latest-upstream assertion. '
                 'Source painter fixtures and required sealed test evidence are retained. '
                 'P&C uses the supplied JavaScript runtime; no Python pyto install is needed.',
    }
    if source['baseCommit'] is None and (ROOT / 'bundle-source.json').is_file():
        source['incomingSource'] = json.loads((ROOT / 'bundle-source.json').read_text())
    payload['bundle-source.json'] = encoded(source)
    manifest = {'schemaVersion': 1, 'files': {
        name: {'bytes': len(data), 'sha256': digest(data)}
        for name, data in sorted(payload.items())
    }}
    payload['bundle-manifest.json'] = encoded(manifest)
    # Detect source edits during capture; all archived bytes came from this read.
    if names != inputs() or any((ROOT / name).read_bytes() != payload[name] for name in names):
        raise ValueError('Source changed during capture; rerun for a consistent snapshot')
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix('.zip.tmp')
    try:
        with zipfile.ZipFile(temporary, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
            for name, data in sorted(payload.items()):
                info = zipfile.ZipInfo(f'{PREFIX}/{name}', date_time=(1980, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                archive.writestr(info, data)
        with zipfile.ZipFile(temporary) as archive:
            if archive.testzip() is not None:
                raise ValueError('Zip CRC verification failed')
            for name, data in payload.items():
                if archive.read(f'{PREFIX}/{name}') != data:
                    raise ValueError(f'Archive bytes differ: {name}')
        temporary.replace(output)
    finally:
        temporary.unlink(missing_ok=True)
    print(json.dumps({'zip': str(output), 'bytes': output.stat().st_size,
                      'files': len(payload), 'sha256': digest(output.read_bytes()),
                      'manifestSha256': digest(payload['bundle-manifest.json'])}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=ROOT.parent / 'cloud-bundles' / 'discstudio-uds-cloud.zip')
    parser.add_argument('--verify', type=Path, help='verify an unpacked baseline instead of bundling')
    arguments = parser.parse_args()
    try:
        verify(arguments.verify) if arguments.verify else bundle(arguments.out)
    except (ValueError, OSError, KeyError, zipfile.BadZipFile) as error:
        parser.exit(1, f'{error}\n')
