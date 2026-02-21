# rack

Unified **Paternoster Rack** marketplace, aligned with Claude plugin marketplace structure and aggregated from:

- `anthropics/claude-plugins-official`
- `anthropics/skills`
- `anthropics/claude-code`

## What this repo contains

- `.pater/marketplace.json` — deduplicated unified catalog
- `plugins/*` — migrated plugin payloads (local where available)

## Deduplication policy

If the same plugin name exists in multiple upstream sources, Rack keeps a single entry with this priority:

1. `claude-plugins-official`
2. `claude-code`
3. `skills`

This avoids duplicate plugin IDs while preserving broad coverage.
