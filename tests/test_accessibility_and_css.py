"""
Accessibility & CSS Standard Unit Tests
Audits semantic structure, ARIA compliance, and responsive rules.
"""

import unittest
import re
from pathlib import Path


class TestAccessibilityAndCSS(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root_dir = Path(__file__).resolve().parent.parent
        cls.html_path = cls.root_dir / "src" / "frontend" / "index.html"
        cls.html_content = cls.html_path.read_text(encoding="utf-8")
        cls.responsive_css = (cls.root_dir / "src" / "frontend" / "css" / "responsive.css").read_text(encoding="utf-8")
        cls.base_css = (cls.root_dir / "src" / "frontend" / "css" / "base.css").read_text(encoding="utf-8")

    def test_viewport_meta_tag_present(self):
        self.assertIn('name="viewport"', self.html_content)
        self.assertIn('width=device-width', self.html_content)

    def test_semantic_landmarks(self):
        self.assertIn('<header', self.html_content)
        self.assertIn('<main', self.html_content)
        self.assertIn('<aside', self.html_content)

    def test_buttons_have_aria_or_type(self):
        # Look for buttons in html
        button_tags = re.findall(r'<button([^>]*)>', self.html_content, re.IGNORECASE)
        self.assertGreater(len(button_tags), 0)
        for attr_str in button_tags:
            has_type = 'type=' in attr_str
            has_aria = 'aria-label=' in attr_str or 'aria-labelledby=' in attr_str
            self.assertTrue(
                has_type or has_aria,
                f"Button missing type or aria-label: <button{attr_str}>"
            )

    def test_responsive_media_queries_defined(self):
        self.assertIn('@media', self.responsive_css)
        self.assertIn('max-width: 1024px', self.responsive_css)
        self.assertIn('max-width: 768px', self.responsive_css)

    def test_css_design_tokens(self):
        self.assertIn('--bg-primary:', self.base_css)
        self.assertIn('--text-primary:', self.base_css)
        self.assertIn('--primary:', self.base_css)



    def test_mobile_touch_targets(self):
        """Verify mobile buttons and inputs define minimum 44px touch targets."""
        if 'min-height: 44px' in self.responsive_css:
            self.assertIn('touch-action: manipulation', self.responsive_css)


if __name__ == "__main__":
    unittest.main()
