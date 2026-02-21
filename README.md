# rack

**Paternoster Rack** marketplace repository.

This repo contains the signed marketplace catalog consumed by `pater`.

## For Users

You usually do **not** use this repo directly.  
Use `pater` (defaults to `paternosterrack/rack`).

## For Maintainers

### Repository artifacts

- `.pater/marketplace.json` — unified plugin catalog
- `.pater/marketplace.sig` — detached signature
- `.pater/trusted-pubkey.hex` — official public key reference

### Upstream aggregation priority

1. `anthropics/claude-plugins-official`
2. `anthropics/claude-code`
3. `anthropics/skills`

### Safety model

Unknown-license entries are marked:
- `distribution: external-reference-only`
- `license_status: unknown`

`pater` policy can block these by default.

### Maintenance via `pater` (no Python scripts)

```bash
# run from pater repo (or anywhere with pater installed)
pater rack sync --rack-dir ../rack
pater rack license-audit --rack-dir ../rack
pater rack mark-unknown-external --rack-dir ../rack
pater rack sign --rack-dir ../rack --sign-key /path/to/marketplace_signing_key.pem

# or one-shot pipeline
pater rack prepare-release --rack-dir ../rack --sign-key /path/to/marketplace_signing_key.pem
```

### Minimal release flow

1. Sync/update catalog
2. Run license audit
3. Mark unknown-license entries external-only
4. Sign marketplace
5. Commit + push
