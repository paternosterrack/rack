# rack

Official **Paternoster Rack** marketplace repository.

## Layout

- `.pater/marketplace.json` — marketplace catalog (Claude-style flow, agent-agnostic schema)
- `plugins/*/.pater/plugin.json` — plugin manifests
- `plugins/*/skills/*/SKILL.md` — example skills

## Philosophy

- Marketplace first, plugin install second
- Multi-source ready (git/local/url)
- Namespaced plugin model
- Curated hooks and subagents per plugin

Consumed by the `pater` CLI.
