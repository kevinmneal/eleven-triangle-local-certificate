"""Verify portable artifact identity and replay its exact local theorem."""
import hashlib,json,subprocess,sys
from pathlib import Path
root=Path(__file__).resolve().parent
manifest=json.loads((root/'PACKET_MANIFEST.json').read_text())
for name,digest in manifest['sha256'].items():
    path=(root/name).resolve()
    if not path.is_relative_to(root) or not path.is_file():
        raise RuntimeError('Missing or unsafe packet path: '+name)
    if hashlib.sha256(path.read_bytes()).hexdigest()!=digest:
        raise RuntimeError('Hash mismatch: '+name)
run=subprocess.run([sys.executable,'-B','-S','-O',str(root/'check_source_local.py'),str(root/'certificates/source_local_v2.json.gz')],check=True,capture_output=True,text=True)
fresh=json.loads(run.stdout)
saved=json.loads((root/'verification/source_local_radius_1e_minus_7_verdict.json').read_text())
if fresh!=saved:
    raise RuntimeError('Fresh local-proof verdict differs from saved verdict')
if (fresh['pair_nonoverlap_checks'],fresh['wall_inequalities'],fresh['complete_local_branch_count'])!=(55,165,256):
    raise RuntimeError('Incomplete target or branch coverage')
print(json.dumps(dict(status='PASS: frozen packet and exact strict local minimum',files=len(manifest['sha256']),certificate_sha256=fresh['certificate_sha256'],side_interval=fresh['unit_side_container_side_interval'],neighborhood=fresh['local_pose_and_radius_infinity_neighborhood'],growth_lower=fresh['radius_growth_lower'],scope=fresh['scope']),indent=2))
