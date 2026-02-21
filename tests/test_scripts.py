import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


class ScriptTests(unittest.TestCase):
    def test_mark_unknown_external_marks_plugins(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td) / "rack"
            repo.mkdir()
            (repo / "scripts").mkdir()
            (repo / ".pater").mkdir()

            shutil.copy2(
                Path(__file__).resolve().parents[1] / "scripts" / "mark_unknown_external.py",
                repo / "scripts" / "mark_unknown_external.py",
            )

            write_json(
                repo / ".pater" / "marketplace.json",
                {
                    "plugins": [
                        {"name": "a", "source": "./plugins/a"},
                        {"name": "b", "source": "./plugins/b"},
                    ]
                },
            )
            write_json(
                repo / ".pater" / "license-audit.json",
                {
                    "plugins": [
                        {"name": "a", "classification": "proprietary/unknown"},
                        {"name": "b", "classification": "permissive"},
                    ]
                },
            )

            subprocess.run(["python3", "scripts/mark_unknown_external.py"], cwd=repo, check=True)

            m = json.loads((repo / ".pater" / "marketplace.json").read_text())
            by_name = {p["name"]: p for p in m["plugins"]}
            self.assertEqual(by_name["a"]["distribution"], "external-reference-only")
            self.assertEqual(by_name["a"]["license_status"], "unknown")
            self.assertNotIn("distribution", by_name["b"])

    def test_sync_upstreams_deduplicates_by_priority(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td) / "rack"
            repo.mkdir()
            (repo / "scripts").mkdir()

            shutil.copy2(
                Path(__file__).resolve().parents[1] / "scripts" / "sync_upstreams.py",
                repo / "scripts" / "sync_upstreams.py",
            )

            base = repo / "_upstreams"
            write_json(
                base / "claude-plugins-official" / ".claude-plugin" / "marketplace.json",
                {
                    "plugins": [
                        {"name": "same", "source": "./official"},
                        {"name": "o", "source": "./o"},
                    ]
                },
            )
            write_json(
                base / "claude-code" / ".claude-plugin" / "marketplace.json",
                {
                    "plugins": [
                        {"name": "same", "source": "./code"},
                        {"name": "c", "source": "./c"},
                    ]
                },
            )
            write_json(
                base / "skills" / ".claude-plugin" / "marketplace.json",
                {
                    "plugins": [
                        {"name": "same", "source": "./skills"},
                        {"name": "s", "source": "./s"},
                    ]
                },
            )

            subprocess.run(["python3", "scripts/sync_upstreams.py"], cwd=repo, check=True)

            out = json.loads((repo / ".pater" / "marketplace.json").read_text())
            names = [p["name"] for p in out["plugins"]]
            self.assertEqual(names.count("same"), 1)
            same = next(p for p in out["plugins"] if p["name"] == "same")
            self.assertEqual(same["source"], "./official")

    def test_license_audit_reports_permissive_local_plugin(self):
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td) / "rack"
            repo.mkdir()
            (repo / "scripts").mkdir()

            shutil.copy2(
                Path(__file__).resolve().parents[1] / "scripts" / "license_audit.py",
                repo / "scripts" / "license_audit.py",
            )

            plugin_dir = repo / "plugins" / "demo"
            (plugin_dir / ".claude-plugin").mkdir(parents=True)
            (plugin_dir / "LICENSE").write_text(
                "MIT License\n\nPermission is hereby granted, free of charge, to any person obtaining a copy ",
                encoding="utf-8",
            )
            (plugin_dir / ".claude-plugin" / "plugin.json").write_text(
                json.dumps({"name": "demo", "version": "1.0.0"}), encoding="utf-8"
            )

            write_json(
                repo / ".pater" / "marketplace.json",
                {
                    "plugins": [
                        {"name": "demo", "source": "./plugins/demo"},
                    ]
                },
            )

            proc = subprocess.run(
                ["python3", "scripts/license_audit.py"],
                cwd=repo,
                text=True,
                capture_output=True,
            )
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

            report = json.loads((repo / ".pater" / "license-audit.json").read_text())
            self.assertEqual(report["plugins"][0]["classification"], "permissive")


if __name__ == "__main__":
    unittest.main()
