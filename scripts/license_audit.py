#!/usr/bin/env python3
"""Audit marketplace plugin licenses and emit a machine-readable report."""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

PERMISSIVE_IDS = {
    "MIT",
    "APACHE-2.0",
    "BSD-2-CLAUSE",
    "BSD-3-CLAUSE",
    "ISC",
    "UNLICENSE",
    "CC0-1.0",
}

COPYLEFT_IDS = {
    "GPL-2.0",
    "GPL-3.0",
    "AGPL-3.0",
    "LGPL-2.1",
    "LGPL-3.0",
    "MPL-2.0",
}

ALIAS_TO_SPDX = {
    "MIT": "MIT",
    "APACHE2": "APACHE-2.0",
    "APACHE-2": "APACHE-2.0",
    "APACHE-2.0": "APACHE-2.0",
    "APACHELICENSE2.0": "APACHE-2.0",
    "BSD2": "BSD-2-CLAUSE",
    "BSD-2": "BSD-2-CLAUSE",
    "BSD-2-CLAUSE": "BSD-2-CLAUSE",
    "BSD2CLAUSE": "BSD-2-CLAUSE",
    "BSD3": "BSD-3-CLAUSE",
    "BSD-3": "BSD-3-CLAUSE",
    "BSD-3-CLAUSE": "BSD-3-CLAUSE",
    "BSD3CLAUSE": "BSD-3-CLAUSE",
    "ISC": "ISC",
    "UNLICENSE": "UNLICENSE",
    "CC0": "CC0-1.0",
    "CC0-1.0": "CC0-1.0",
    "GPL2": "GPL-2.0",
    "GPL-2": "GPL-2.0",
    "GPL-2.0": "GPL-2.0",
    "GPL3": "GPL-3.0",
    "GPL-3": "GPL-3.0",
    "GPL-3.0": "GPL-3.0",
    "AGPL3": "AGPL-3.0",
    "AGPL-3": "AGPL-3.0",
    "AGPL-3.0": "AGPL-3.0",
    "LGPL2.1": "LGPL-2.1",
    "LGPL-2.1": "LGPL-2.1",
    "LGPL3": "LGPL-3.0",
    "LGPL-3": "LGPL-3.0",
    "LGPL-3.0": "LGPL-3.0",
    "MPL2": "MPL-2.0",
    "MPL-2": "MPL-2.0",
    "MPL-2.0": "MPL-2.0",
}

LICENSE_TEXT_PATTERNS: List[Tuple[str, Tuple[str, ...]]] = [
    ("MIT", ("permission is hereby granted, free of charge, to any person obtaining a copy",)),
    ("APACHE-2.0", ("apache license", "version 2.0")),
    (
        "BSD-3-CLAUSE",
        (
            "redistribution and use in source and binary forms, with or without modification",
            "neither the name",
        ),
    ),
    (
        "BSD-2-CLAUSE",
        (
            "redistribution and use in source and binary forms, with or without modification",
            "this list of conditions and the following disclaimer",
        ),
    ),
    ("ISC", ("permission to use, copy, modify, and/or distribute this software", "without fee")),
    ("UNLICENSE", ("this is free and unencumbered software released into the public domain",)),
    ("CC0-1.0", ("creative commons zero", "cc0 1.0 universal")),
    ("AGPL-3.0", ("gnu affero general public license", "version 3")),
    ("LGPL-3.0", ("gnu lesser general public license", "version 3")),
    ("LGPL-2.1", ("gnu lesser general public license", "version 2.1")),
    ("GPL-3.0", ("gnu general public license", "version 3")),
    ("GPL-2.0", ("gnu general public license", "version 2")),
    ("MPL-2.0", ("mozilla public license", "version 2.0")),
]


def load_marketplace(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def normalize_license(raw: Optional[str]) -> Optional[str]:
    if not raw:
        return None
    token = raw.strip().upper()
    if token in PERMISSIVE_IDS or token in COPYLEFT_IDS:
        return token
    compact = re.sub(r"[^A-Z0-9.+-]", "", token)
    if compact in ALIAS_TO_SPDX:
        return ALIAS_TO_SPDX[compact]

    phrase_map = [
        (r"\bMIT\b", "MIT"),
        (r"APACHE.*2(\.0)?", "APACHE-2.0"),
        (r"BSD.*3", "BSD-3-CLAUSE"),
        (r"BSD.*2", "BSD-2-CLAUSE"),
        (r"\bISC\b", "ISC"),
        (r"UNLICENSE", "UNLICENSE"),
        (r"CC0", "CC0-1.0"),
        (r"AGPL.*3", "AGPL-3.0"),
        (r"LGPL.*2\.1", "LGPL-2.1"),
        (r"LGPL.*3", "LGPL-3.0"),
        (r"\bGPL.*3", "GPL-3.0"),
        (r"\bGPL.*2", "GPL-2.0"),
        (r"MPL.*2", "MPL-2.0"),
    ]
    for pattern, spdx in phrase_map:
        if re.search(pattern, token):
            return spdx
    return None


def classify(spdx_id: Optional[str]) -> str:
    if not spdx_id:
        return "proprietary/unknown"
    if spdx_id in PERMISSIVE_IDS:
        return "permissive"
    if spdx_id in COPYLEFT_IDS:
        return "copyleft"
    return "proprietary/unknown"


def maybe_url(value: str) -> bool:
    parsed = urllib.parse.urlparse(value)
    return bool(parsed.scheme and parsed.netloc) or value.startswith("git@github.com:")


def detect_source_type(source: Any) -> str:
    if isinstance(source, str):
        return "url" if maybe_url(source) else "local path"
    if isinstance(source, dict):
        return "object source"
    return "unknown"


def detect_from_license_text(text: str) -> Optional[str]:
    hay = text.lower()
    for spdx_id, needles in LICENSE_TEXT_PATTERNS:
        if all(needle in hay for needle in needles):
            return spdx_id
    return None


def find_license_file(plugin_dir: Path) -> Tuple[Optional[Path], List[str]]:
    notes: List[str] = []
    for name in ("LICENSE", "LICENSE.md", "COPYING"):
        path = plugin_dir / name
        if path.is_file():
            notes.append(f"found {name}")
            return path, notes
    notes.append("no LICENSE/LICENSE.md/COPYING file found")
    return None, notes


def extract_manifest_license(manifest: Any) -> Optional[str]:
    if isinstance(manifest, dict):
        for key, value in manifest.items():
            lowered = str(key).lower()
            if lowered in {"license", "licence", "license_id", "spdx", "spdx_id"} and isinstance(value, str):
                return value
            nested = extract_manifest_license(value)
            if nested:
                return nested
    elif isinstance(manifest, list):
        for item in manifest:
            nested = extract_manifest_license(item)
            if nested:
                return nested
    return None


def parse_github_repo_from_url(url: str) -> Optional[Tuple[str, str]]:
    if url.startswith("git@github.com:"):
        repo = url.split(":", 1)[1].strip()
        if repo.endswith(".git"):
            repo = repo[:-4]
        parts = [p for p in repo.split("/") if p]
        if len(parts) >= 2:
            return parts[0], parts[1]
        return None

    parsed = urllib.parse.urlparse(url)
    host = parsed.netloc.lower()
    parts = [p for p in parsed.path.split("/") if p]

    if host == "github.com" and len(parts) >= 2:
        owner, repo = parts[0], parts[1]
        if repo.endswith(".git"):
            repo = repo[:-4]
        return owner, repo

    if host == "raw.githubusercontent.com" and len(parts) >= 2:
        return parts[0], parts[1]

    return None


def parse_github_repo(source: Any) -> Optional[Tuple[str, str]]:
    if isinstance(source, str):
        return parse_github_repo_from_url(source)

    if not isinstance(source, dict):
        return None

    repo_field = source.get("repo")
    if isinstance(repo_field, str):
        repo_field = repo_field.strip()
        if "/" in repo_field and not repo_field.startswith("http"):
            bits = [p for p in repo_field.split("/") if p]
            if len(bits) >= 2:
                return bits[0], bits[1]
        parsed = parse_github_repo_from_url(repo_field)
        if parsed:
            return parsed

    url_field = source.get("url")
    if isinstance(url_field, str):
        parsed = parse_github_repo_from_url(url_field)
        if parsed:
            return parsed

    source_kind = str(source.get("source", "")).lower()
    if source_kind == "github" and isinstance(repo_field, str) and "/" in repo_field:
        bits = [p for p in repo_field.split("/") if p]
        if len(bits) >= 2:
            return bits[0], bits[1]

    return None


def github_api_json(url: str) -> Dict[str, Any]:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "rack-license-audit",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=15) as resp:
        raw = resp.read().decode("utf-8")
    return json.loads(raw)


def detect_remote_github_license(owner: str, repo: str) -> Tuple[Optional[str], Optional[str], str, str]:
    api_url = f"https://api.github.com/repos/{owner}/{repo}/license"
    try:
        data = github_api_json(api_url)
    except urllib.error.HTTPError as err:
        return None, None, "low", f"GitHub API error {err.code} for {owner}/{repo}"
    except urllib.error.URLError as err:
        return None, None, "low", f"GitHub API unreachable for {owner}/{repo}: {err.reason}"
    except (TimeoutError, json.JSONDecodeError) as err:
        return None, None, "low", f"GitHub API parse/timeout error for {owner}/{repo}: {err}"

    license_obj = data.get("license") if isinstance(data, dict) else None
    if not isinstance(license_obj, dict):
        return None, None, "low", f"No license metadata returned for {owner}/{repo}"

    raw_id = license_obj.get("spdx_id")
    raw_name = license_obj.get("name")
    normalized = normalize_license(raw_id if isinstance(raw_id, str) else None)
    if not normalized and isinstance(raw_name, str):
        normalized = normalize_license(raw_name)

    confidence = "high" if normalized else "medium"
    return normalized, raw_name if isinstance(raw_name, str) else None, confidence, f"resolved via GitHub API for {owner}/{repo}"


def resolve_local_license(plugin_dir: Path) -> Tuple[Optional[str], Optional[str], str, List[str]]:
    notes: List[str] = []

    license_file, file_notes = find_license_file(plugin_dir)
    notes.extend(file_notes)

    if license_file:
        try:
            text = license_file.read_text(encoding="utf-8", errors="ignore")
        except OSError as err:
            notes.append(f"failed reading {license_file.name}: {err}")
        else:
            detected = detect_from_license_text(text)
            if detected:
                notes.append(f"license recognized from {license_file.name}")
                return detected, detected, "high", notes
            notes.append(f"unable to recognize license text in {license_file.name}")

    manifest_path = plugin_dir / ".claude-plugin" / "plugin.json"
    if manifest_path.is_file():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as err:
            notes.append(f"failed parsing plugin manifest: {err}")
        else:
            manifest_license = extract_manifest_license(manifest)
            if manifest_license:
                normalized = normalize_license(manifest_license)
                if normalized:
                    notes.append("license resolved from plugin manifest")
                    return normalized, manifest_license, "medium", notes
                notes.append(f"manifest license present but unmapped: {manifest_license}")
    else:
        notes.append("plugin manifest not found at .claude-plugin/plugin.json")

    return None, None, "low", notes


def audit_plugin(plugin: Dict[str, Any], repo_root: Path) -> Dict[str, Any]:
    name = str(plugin.get("name", "<unnamed>"))
    source = plugin.get("source")
    source_type = detect_source_type(source)

    license_id: Optional[str] = None
    license_name: Optional[str] = None
    confidence = "low"
    notes: List[str] = []

    if source_type == "local path" and isinstance(source, str):
        plugin_dir = (repo_root / source).resolve()
        if plugin_dir.exists() and plugin_dir.is_dir():
            license_id, license_name, confidence, notes = resolve_local_license(plugin_dir)
        else:
            notes.append(f"local path does not exist: {source}")
    else:
        repo = parse_github_repo(source)
        if repo:
            owner, repository = repo
            license_id, license_name, confidence, note = detect_remote_github_license(owner, repository)
            notes.append(note)
        else:
            notes.append("source not resolvable to GitHub repository metadata")

    classification = classify(license_id)

    return {
        "name": name,
        "source": source,
        "source_type": source_type,
        "license_id": license_id,
        "license_name": license_name,
        "classification": classification,
        "confidence": confidence,
        "notes": notes,
    }


def print_summary(report: Iterable[Dict[str, Any]]) -> Dict[str, int]:
    counts = {
        "permissive": 0,
        "copyleft": 0,
        "proprietary/unknown": 0,
    }
    total = 0
    for item in report:
        total += 1
        cls = str(item.get("classification", "proprietary/unknown"))
        if cls not in counts:
            cls = "proprietary/unknown"
        counts[cls] += 1

    print("License Audit Summary")
    print("---------------------")
    print(f"{'classification':<22}{'count':>6}")
    print(f"{'permissive':<22}{counts['permissive']:>6}")
    print(f"{'copyleft':<22}{counts['copyleft']:>6}")
    print(f"{'proprietary/unknown':<22}{counts['proprietary/unknown']:>6}")
    print(f"{'total':<22}{total:>6}")

    return counts


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    marketplace_path = repo_root / ".pater" / "marketplace.json"
    report_path = repo_root / ".pater" / "license-audit.json"

    try:
        marketplace = load_marketplace(marketplace_path)
    except (OSError, json.JSONDecodeError) as err:
        print(f"Failed to read marketplace file at {marketplace_path}: {err}", file=sys.stderr)
        return 2

    plugins = marketplace.get("plugins")
    if not isinstance(plugins, list):
        print("Invalid marketplace format: 'plugins' must be an array", file=sys.stderr)
        return 2

    report = [audit_plugin(plugin, repo_root) for plugin in plugins if isinstance(plugin, dict)]

    report_payload = {
        "marketplace": str(marketplace_path),
        "generated_by": "scripts/license_audit.py",
        "plugins": report,
    }
    report_path.write_text(json.dumps(report_payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    counts = print_summary(report)
    print(f"Detailed report written to: {report_path}")

    return 1 if counts["proprietary/unknown"] > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
