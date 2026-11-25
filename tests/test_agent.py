"""
Unit Tests for Autonomous Contribution Agent Safeguards & Helpers
"""

import sys
import unittest
from pathlib import Path

AGENT_DIR = Path(__file__).resolve().parent.parent / ".github" / "agent"
sys.path.insert(0, str(AGENT_DIR))

from autonomous_agent import AutonomousContributionAgent


class TestAutonomousAgent(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.agent = AutonomousContributionAgent(dry_run=True)

    def test_protected_paths_blocked(self):
        blocked = [
            ".env",
            ".env.production",
            ".git/HEAD",
            ".github/workflows/autonomous-dev-agent.yml",
            ".github/agent_memory.json",
            "reports/daily/2026-11-25.md",
            "../outside.py",
        ]
        for path in blocked:
            self.assertTrue(self.agent.is_protected_path(path), f"Expected protected path: {path}")

        self.assertFalse(self.agent.is_protected_path("src/frontend/index.html"))
        self.assertFalse(self.agent.is_protected_path("src/backend/handlers.py"))

    def test_meaningful_change_filter(self):
        self.assertFalse(self.agent.is_meaningful_change("const x = 1;", ""))
        self.assertFalse(self.agent.is_meaningful_change("const x = 1;", "const x = 1;"))
        self.assertFalse(self.agent.is_meaningful_change("const x = 1;", "const   x =  1;\n"))
        self.assertTrue(self.agent.is_meaningful_change("const x = 1;", "const x = 2;"))

    def test_parse_json_response_strips_fences(self):
        fenced = '```json\n{"has_improvement": true, "category": "BUG_FIX"}\n```'
        parsed = self.agent._parse_json_response(fenced)
        self.assertIsNotNone(parsed)
        self.assertTrue(parsed["has_improvement"])
        self.assertEqual(parsed["category"], "BUG_FIX")

    def test_validate_syntax_python_and_json(self):
        ok_py, _ = self.agent.validate_syntax(Path("sample.py"), "def add(a, b):\n    return a + b\n")
        self.assertTrue(ok_py)

        bad_py, err_py = self.agent.validate_syntax(Path("sample.py"), "def broken(:\n    pass\n")
        self.assertFalse(bad_py)
        self.assertIn("Python syntax error", err_py)

        bad_json, err_json = self.agent.validate_syntax(Path("sample.json"), "{invalid json}")
        self.assertFalse(bad_json)
        self.assertIn("JSON syntax error", err_json)

    def test_scan_project_files_excludes_protected_and_reports(self):
        files = [f.relative_to(self.agent.workspace_root).as_posix() for f in self.agent.scan_project_files()]
        self.assertGreater(len(files), 5)
        for rel in files:
            self.assertFalse(rel.startswith("reports/"), f"Reports should be excluded: {rel}")
            self.assertFalse(rel.startswith(".github/workflows/"), f"Workflows should be excluded: {rel}")


if __name__ == "__main__":
    unittest.main()
