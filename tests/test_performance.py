"""
Performance & File Integrity Unit Tests
"""

import unittest
import ast
from pathlib import Path


class TestPerformanceAndIntegrity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root_dir = Path(__file__).resolve().parent.parent

    def test_python_syntax_all_files(self):
        """Ensure all Python source files compile without syntax errors."""
        py_files = list(self.root_dir.glob("src/**/*.py")) + list(self.root_dir.glob("tests/**/*.py"))
        self.assertGreater(len(py_files), 0)
        for py_file in py_files:
            content = py_file.read_text(encoding="utf-8")
            try:
                ast.parse(content, filename=str(py_file))
            except SyntaxError as e:
                self.fail(f"Syntax error in {py_file}: {e}")

    def test_file_sizes_within_reasonable_bounds(self):
        """Ensure no runaway single file bloat (>500KB) in src/."""
        for file in self.root_dir.glob("src/**/*.*"):
            if file.is_file():
                size_kb = file.stat().st_size / 1024
                self.assertLess(size_kb, 500, f"File {file} exceeds 500KB limit ({size_kb:.2f} KB)")


if __name__ == "__main__":
    unittest.main()
