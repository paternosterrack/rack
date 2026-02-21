# rack

**Paternoster Rack** marketplace repository.

This repo contains the signed marketplace catalog consumed by `pater`.

## For Users

You usually do **not** use this repo directly.  
Use the `pater` CLI, which defaults to `paternosterrack/rack`.

## For Developers / Maintainers

## What is here

- `.pater/marketplace.json` — unified plugin catalog
- `.pater/marketplace.sig` — detached signature for catalog
- `.pater/trusted-pubkey.hex` — official public key reference

## Upstream aggregation priority

1. `anthropics/claude-plugins-official`
2. `anthropics/claude-code`
3. `anthropics/skills`

## Safety model

Unknown-license entries are marked as:
- `distribution: external-reference-only`
- `license_status: unknown`

`pater` policy can block these by default.

## Maintainer scripts

```bash
# sync upstream snapshots into marketplace
python3 scripts/sync_upstreams.py

# mark unknown-license entries as external-reference-only
python3 scripts/mark_unknown_external.py

# audit license status (non-zero if unknown/proprietary exist)
python3 scripts/license_audit.py

# sign marketplace.json
scripts/sign_marketplace.sh /path/to/marketplace_signing_key.pem
```

## Minimal release flow

1. Sync/update catalog
2. Run license audit
3. Apply safety marking
4. Sign marketplace
5. Commit + push
