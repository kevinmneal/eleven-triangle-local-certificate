"""Check public release identities; this is not a mathematical proof checker."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
manifest = json.loads((ROOT / 'RELEASE_MANIFEST.json').read_text())
for name, expected in manifest['sha256'].items():
    path = (ROOT / name).resolve()
    if not path.is_relative_to(ROOT) or not path.is_file():
        raise RuntimeError('Missing or unsafe release path: ' + name)
    if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
        raise RuntimeError('Release file changed: ' + name)
print('PASS: public release identities (' + str(len(manifest['sha256'])) + ' files)')
