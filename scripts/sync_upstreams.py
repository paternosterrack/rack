#!/usr/bin/env python3
"""
Sync upstream marketplaces into rack/.pater/marketplace.json with dedupe.
Priority: claude-plugins-official > claude-code > skills
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UPSTREAMS = [
    ("official", ROOT / "_upstreams/claude-plugins-official/.claude-plugin/marketplace.json"),
    ("claude-code", ROOT / "_upstreams/claude-code/.claude-plugin/marketplace.json"),
    ("skills", ROOT / "_upstreams/skills/.claude-plugin/marketplace.json"),
]

seen = set()
plugins = []
for label, p in UPSTREAMS:
    if not p.exists():
        continue
    data = json.loads(p.read_text())
    for pl in data.get("plugins", []):
        name = pl.get("name")
        if not name or name in seen:
            continue
        seen.add(name)
        plugins.append(pl)

out = {
    "name": "paternoster-rack",
    "owner": {"name": "Paternoster Rack"},
    "metadata": {
        "description": "Unified curated marketplace (deduplicated)",
        "sync_priority": ["claude-plugins-official", "claude-code", "skills"],
    },
    "plugins": plugins,
}

out_path = ROOT / ".pater/marketplace.json"
out_path.parent.mkdir(parents=True, exist_ok=True)
out_path.write_text(json.dumps(out, indent=2) + "\n")
print(f"wrote {out_path} with {len(plugins)} plugins")
