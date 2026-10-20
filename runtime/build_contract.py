#!/usr/bin/env python3
"""Verify that both frozen contracts and the v2 source snapshot are unchanged."""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEXT = ROOT / 'MARKER_INVENTORY.md'
CONTRACTS = Path(__file__).resolve().parent / 'contracts'
V1 = CONTRACTS / 'made-well-discovery-v1.json'
OUTPUT = CONTRACTS / 'made-well-discovery-v2.json'
# The historical v1 file is preserved byte-for-byte, including its misleading revision field.
V1_SHA256 = 'b38651dbd1dde232efec3e47d95d61ef8cc505924f44cd9c26b10692b5f5c689'
V2_SHA256 = 'bde0219dff85ec98e1ddc7142ec9bd5c840ee422d90958d32c69e782526e8d25'
GROUPS = {
    'A': 'Declare run', 'N': 'Live conversation specialization', 'B': 'Look before adding',
    'C': 'Ground', 'D': 'Classify input', 'E': 'Choose pass mode', 'F': 'Apply lenses',
    'L': 'Cross-artifact synthesis', 'H': 'The One Thing', 'I': 'PRD compression',
    'J': 'Route findings', 'K': 'Name things and questions', 'M': 'Reflect, review and rack',
}
SOURCE = ROOT / 'MARKER_INVENTORY.md'
SOURCES = [
    Path.home() / 'projects/infinity/arc/AGENTS.md',
    Path.home() / 'projects/infinity/arc/.madewell/skills/discovery.md',
    Path.home() / 'projects/infinity/arc/.madewell/ground/PROTOCOL.md',
    Path.home() / 'projects/infinity/arc/.madewell/ground/PICTURE.md',
    Path.home() / 'projects/infinity/arc/.madewell/ground/ROOTS.md',
]

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    if not V1.is_file() or sha(V1) != V1_SHA256:
        raise SystemExit('Frozen v1 missing or changed; refusing to verify v2.')
    if not OUTPUT.is_file() or sha(OUTPUT) != V2_SHA256:
        raise SystemExit('Frozen v2 missing or changed; refusing to regenerate it.')
    text = TEXT.read_text()
    rows = re.findall(r'^- `([A-N]\d{2})` ([^\n]+)', text, re.M)
    assert len(rows) == 72, f'expected 72 fixed markers, got {len(rows)}'
    assert len({key for key, _ in rows}) == len(rows), 'duplicate marker ID'
    mapping = dict(rows)
    assert set(k[0] for k in mapping) == set(GROUPS)
    markers = []
    for group, stage in GROUPS.items():
        for marker_id, description in rows:
            if marker_id.startswith(group):
                markers.append({'id': marker_id, 'stage': group, 'requirement': description})
    doc = {
        'schema': 'pipeline-contract/v2', 'id': 'made-well/discovery', 'version': 2,
        'name': 'Made Well / Discovery',
        'source_provenance': 'Local file-byte SHA256 snapshot; no Git revision claim (some files are ignored).',
        'source_hashes': {str(p): sha(p) for p in [SOURCE, *SOURCES]},
        'progress': {'denominator': len(markers), 'weights': 'equal', 'settled': ['satisfied', 'satisfied_by_rule']},
        'stages': [{'id': key, 'name': value} for key, value in GROUPS.items()],
        'markers': markers,
        'policy': {
            'operator_unavailable': 'Only after draft and request: publish with linked open question, never as confirmed.',
            'paired_artifact': 'L during analysis before routing; six F lenses considered in synthesis.',
            'blind': 'No rack, prior analysis, built material or answer-key context. Log what was withheld.',
            'one_thing': 'Draft at H01; H02 settles only when written to one authorized destination after review.',
            'ground': 'Present four-section picture; no disk write unless specifically requested.',
            'corpus': 'Record stable pointers; no transcript bodies in ledger or stock.'
        },
        'gates': {
            'publish': [m['id'] for m in markers if m['id'] not in ('M07','M08','M09','M10')],
            'deep_comb_fanout': ['E01', 'E02', 'E04'],
        },
    }
    encoded = json.dumps(doc, indent=2) + '\n'
    if OUTPUT.read_text() != encoded:
        raise SystemExit('Refusing to change frozen v2. Create a new contract version/path for source or marker edits.')
    print(f'{OUTPUT}: {len(markers)} markers sha256={sha(OUTPUT)}')

if __name__ == '__main__': main()
