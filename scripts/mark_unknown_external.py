#!/usr/bin/env python3
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
marketplace = root / '.pater' / 'marketplace.json'
audit = root / '.pater' / 'license-audit.json'

m = json.loads(marketplace.read_text())
a = json.loads(audit.read_text())
unknown = {p['name'] for p in a.get('plugins', []) if p.get('classification') == 'proprietary/unknown'}

for p in m.get('plugins', []):
    if p.get('name') in unknown:
        p['distribution'] = 'external-reference-only'
        p['license_status'] = 'unknown'

marketplace.write_text(json.dumps(m, indent=2) + '\n')
print(f'marked {len(unknown)} plugins as external-reference-only')
