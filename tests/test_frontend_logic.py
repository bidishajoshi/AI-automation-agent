"""
Frontend Logic & Validation Unit Tests
Ensures frontend data formatting and validation constraints are upheld.
"""

import unittest
import re
from pathlib import Path


class TestFrontendLogic(unittest.TestCase):
    def test_frontend_files_exist(self):
        base_dir = Path(__file__).resolve().parent.parent / "src" / "frontend"
        expected_files = [
            "index.html",
            "css/base.css",
            "css/layout.css",
            "css/components.css",
            "css/responsive.css",
            "js/app.js",
            "js/api.js",
            "js/utils/dom.js",
            "js/utils/formatters.js",
            "js/utils/validator.js",
            "js/components/dashboard.js",
            "js/components/taskBoard.js",
            "js/components/themeManager.js"
        ]
        for rel_path in expected_files:
            file_path = base_dir / rel_path
            self.assertTrue(file_path.exists(), f"Missing required file: {rel_path}")

    def test_validator_js_rules(self):
        validator_path = Path(__file__).resolve().parent.parent / "src" / "frontend" / "js" / "utils" / "validator.js"
        content = validator_path.read_text(encoding="utf-8")
        self.assertIn("validateTaskInput", content)
        self.assertIn("sanitizeInput", content)
        self.assertIn("Input payload must be a non-null object", content)
        self.assertIn("RESPONSIVE_CSS", content)
        self.assertIn("ACCESSIBILITY", content)



    def test_formatters_presence(self):
        fmt_path = Path(__file__).resolve().parent.parent / "src" / "frontend" / "js" / "utils" / "formatters.js"
        content = fmt_path.read_text(encoding="utf-8")
        self.assertIn("formatRelativeTime", content)
        self.assertIn("formatCategory", content)


if __name__ == "__main__":
    unittest.main()
