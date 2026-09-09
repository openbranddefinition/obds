"""Read-only integrity audit. Run from any working directory."""
from pathlib import Path
import hashlib, json
W = Path(__file__).resolve().parents[1]
def inventory(root):
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob('*')) if p.is_file()}
def verify(root, record):
    expected = json.loads(record.read_text())
    actual = inventory(root)
    assert actual == expected, {'root':str(root), 'missing':sorted(expected.keys()-actual.keys()),
        'extra':sorted(actual.keys()-expected.keys()),
        'changed':[k for k in expected.keys() & actual.keys() if expected[k] != actual[k]]}
    print('VERIFIED', root, len(actual), 'files')
verify(W.parent/'_autonomous_interop_run', W/'reports/original-evidence-inventory.json')
verify(W/'evidence', W/'reports/evidence-inventory.json')
for record in sorted((W/'reports').glob('candidate-v*-inventory.json')):
    verify(W/'proposal'/record.name.removesuffix('-inventory.json'), record)
