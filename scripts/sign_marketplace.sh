#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   scripts/sign_marketplace.sh /path/to/marketplace_signing_key.pem

KEY_PATH="${1:-}"
if [[ -z "$KEY_PATH" ]]; then
  echo "Usage: $0 /path/to/ed25519-private-key.pem" >&2
  exit 1
fi

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

openssl pkeyutl -sign -inkey "$KEY_PATH" -rawin -in .pater/marketplace.json -out .pater/marketplace.sig.bin
python3 - <<'PY'
from pathlib import Path
sig=Path('.pater/marketplace.sig.bin').read_bytes()
Path('.pater/marketplace.sig').write_text(sig.hex()+'\n')
print('wrote .pater/marketplace.sig')
PY
rm -f .pater/marketplace.sig.bin
