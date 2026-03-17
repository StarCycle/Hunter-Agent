from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

from tests.support import workspace_temp_dir


class TestCli(unittest.TestCase):
    def test_help(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "hunter_agent.cli", "--help"],
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("hunter-agent", result.stdout)

    def test_init_upsert_find_and_export(self) -> None:
        with workspace_temp_dir() as tmp_path:
            db_path = tmp_path / "hunter.db"
            export_dir = tmp_path / "exports"
            env = os.environ.copy()
            env["HUNTER_DB_PATH"] = str(db_path)
            env["HUNTER_EXPORT_DIR"] = str(export_dir)

            init_result = subprocess.run(
                [sys.executable, "-m", "hunter_agent.cli", "init-db"],
                capture_output=True,
                text=True,
                env=env,
                check=False,
            )
            self.assertEqual(init_result.returncode, 0)
            self.assertTrue(db_path.exists())

            payload_path = tmp_path / "profile.json"
            payload_path.write_text(
                json.dumps(
                    {
                        "action": "upsert",
                        "profile": {
                            "name": "CLI Candidate",
                            "email": "cli@example.com",
                            "project_categories": ["other:cli flow"],
                        },
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            upsert_result = subprocess.run(
                [sys.executable, "-m", "hunter_agent.cli", "talent-upsert", "--json", str(payload_path)],
                capture_output=True,
                text=True,
                env=env,
                check=False,
            )
            self.assertEqual(upsert_result.returncode, 0)
            upsert_payload = json.loads(upsert_result.stdout)
            self.assertEqual(upsert_payload["action"], "upsert")

            find_result = subprocess.run(
                [sys.executable, "-m", "hunter_agent.cli", "talent-find", "--name", "CLI Candidate"],
                capture_output=True,
                text=True,
                env=env,
                check=False,
            )
            self.assertEqual(find_result.returncode, 0)
            find_payload = json.loads(find_result.stdout)
            self.assertEqual(len(find_payload["matches"]), 1)

            export_path = tmp_path / "talents.csv"
            export_result = subprocess.run(
                [sys.executable, "-m", "hunter_agent.cli", "export", "--out", str(export_path)],
                capture_output=True,
                text=True,
                env=env,
                check=False,
            )
            self.assertEqual(export_result.returncode, 0)
            export_payload = json.loads(export_result.stdout)
            self.assertEqual(export_payload["output"], str(export_path))
            self.assertTrue(export_path.exists())


if __name__ == "__main__":
    unittest.main()
