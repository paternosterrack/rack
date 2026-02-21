# AGENTS.md

Essential rules for contributors and coding agents in this repository.

## Scope

This repo (`rack`) is the marketplace catalog + plugin payload source for `pater`.

## Required checks on every plugin add/update/remove

1. **Validate marketplace file**
   - Ensure `.pater/marketplace.json` is valid JSON and contains the plugin entry.
2. **Required plugin files exist (for local plugins)**
   - `plugins/<name>/.claude-plugin/plugin.json`
   - referenced assets/skills/hooks/agents paths must exist.
3. **Version bump discipline**
   - If plugin behavior/content/manifest changed, bump plugin `version` in marketplace entry and plugin manifest.
4. **Compatibility test with pater CLI (mandatory)**
   - Run from `pater` repo against this rack:
     - `pater --marketplace ../rack validate`
     - `pater --marketplace ../rack discover <plugin-name-or-keyword>`
     - `pater --marketplace ../rack show <plugin-name>@paternoster-rack`
     - `pater --marketplace ../rack install <plugin-name>@paternoster-rack`
5. **No duplicate plugin IDs**
   - Plugin `name` must be unique in `.pater/marketplace.json`.

## README policy

- Do **not** change root `README.md` unless explicitly requested by the user.
- Functional/plugin/catalog changes should be documented in commit messages and/or plugin metadata, not by default README rewrites.

## Keep it minimal

- Avoid large refactors when only catalog/plugin updates are requested.
- Preserve upstream compatibility conventions where possible.

## License Gate

- Plugin sync/update changes must run `pater rack license-audit --rack-dir ../rack` before merge.
- If adding/updating commands, add or update tests in `pater/tests/cli.rs` in the same change.
- CI checks must pass on every PR/push (`.github/workflows/tests.yml`).
