# rack

Official **Paternoster Rack** marketplace repository.

## Current state

- Unified marketplace catalog in `.pater/marketplace.json`
- Aggregated from:
  - `anthropics/claude-plugins-official`
  - `anthropics/claude-code`
  - `anthropics/skills`
- Deduplicated by plugin name (priority order below)
- Signed marketplace artifact: `.pater/marketplace.sig`
- Official pubkey reference: `.pater/trusted-pubkey.hex`

## Deduplication priority

1. `claude-plugins-official`
2. `claude-code`
3. `skills`

## Safety model

- Plugins with unclear license provenance are marked:
  - `distribution: external-reference-only`
  - `license_status: unknown`
- `pater` policy can block these by default and allow explicit overrides.

## Scripts

```bash
# rebuild/merge upstream catalogs (from local upstream snapshots)
python3 scripts/sync_upstreams.py

# mark unknown-license plugins as external-reference-only
python3 scripts/mark_unknown_external.py

# license gate audit (non-zero exit if unknown/proprietary remain)
python3 scripts/license_audit.py

# sign marketplace after updates
scripts/sign_marketplace.sh /path/to/marketplace_signing_key.pem
```

## Release flow (minimal)

1. Sync/update marketplace
2. Run license audit
3. Review unknown/proprietary results
4. Sign `.pater/marketplace.json`
5. Commit + push marketplace + signature
