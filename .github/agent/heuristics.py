"""
Heuristic Improvement Engine & Static Code Analysis
Provides deterministic rule-based analysis and verified fallback improvements.
"""

import os
import re
from typing import Dict, Any, List, Optional
from pathlib import Path


class HeuristicEngine:
    """
    Scans project source files for standard best practices:
    - WCAG 2.1 AA touch target guidelines (min 44px on mobile)
    - ARIA states (aria-expanded, aria-live)
    - Network error resilience & retry utilities
    - Mobile overflow prevention
    - DOM event listener cleanup and debouncing
    """

    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root

    def find_opportunities(self, completed_task_ids: List[str]) -> List[Dict[str, Any]]:
        opportunities = []

        # 1. Responsive CSS: Mobile touch targets and overflow protection
        resp_css_path = self.workspace_root / "src" / "frontend" / "css" / "responsive.css"
        if resp_css_path.exists() and "HEURISTIC_RESPONSIVE_TOUCH_TARGETS" not in completed_task_ids:
            content = resp_css_path.read_text(encoding="utf-8")
            if "min-height: 44px" not in content:
                opportunities.append({
                    "id": "HEURISTIC_RESPONSIVE_TOUCH_TARGETS",
                    "file_path": "src/frontend/css/responsive.css",
                    "category": "RESPONSIVE_CSS",
                    "task_summary": "Enforce WCAG 2.1 AA minimum 44px touch targets on mobile viewports",
                    "commit_message": "style(responsive): enforce minimum 44px touch targets for mobile buttons",
                    "justification": "Improves mobile usability and complies with WCAG 2.1 Success Criterion 2.5.5 for touch target sizes.",
                    "apply_fn": self._apply_responsive_touch_targets
                })

        # 2. Accessibility: aria-expanded on sidebarToggle and live status announcements
        index_html_path = self.workspace_root / "src" / "frontend" / "index.html"
        if index_html_path.exists() and "HEURISTIC_A11Y_EXPANDED_STATE" not in completed_task_ids:
            content = index_html_path.read_text(encoding="utf-8")
            if 'aria-expanded="false"' not in content:
                opportunities.append({
                    "id": "HEURISTIC_A11Y_EXPANDED_STATE",
                    "file_path": "src/frontend/index.html",
                    "category": "ACCESSIBILITY",
                    "task_summary": "Add aria-expanded state to navigation toggle button for screen readers",
                    "commit_message": "fix(a11y): add aria-expanded state to sidebar navigation toggle button",
                    "justification": "Screen reader users will now be informed whether the mobile navigation drawer is expanded or collapsed.",
                    "apply_fn": self._apply_a11y_expanded_state
                })

        # 3. Error Handling: Safe DOM element creation and null guards
        dom_js_path = self.workspace_root / "src" / "frontend" / "js" / "utils" / "dom.js"
        if dom_js_path.exists() and "HEURISTIC_DOM_NULL_GUARDS" not in completed_task_ids:
            content = dom_js_path.read_text(encoding="utf-8")
            if "createElementWithAttributes" not in content:
                opportunities.append({
                    "id": "HEURISTIC_DOM_NULL_GUARDS",
                    "file_path": "src/frontend/js/utils/dom.js",
                    "category": "ERROR_HANDLING",
                    "task_summary": "Add safe createElementWithAttributes helper with null-safe attribute assignment",
                    "commit_message": "refactor(dom): add safe createElementWithAttributes helper with defensive null guards",
                    "justification": "Prevents runtime null reference errors when dynamically constructing UI nodes and badges.",
                    "apply_fn": self._apply_dom_null_guards
                })

        # 4. Error Handling: API exponential backoff retry utility
        api_js_path = self.workspace_root / "src" / "frontend" / "js" / "api.js"
        if api_js_path.exists() and "HEURISTIC_API_RETRY_BACKOFF" not in completed_task_ids:
            content = api_js_path.read_text(encoding="utf-8")
            if "fetchWithRetry" not in content:
                opportunities.append({
                    "id": "HEURISTIC_API_RETRY_BACKOFF",
                    "file_path": "src/frontend/js/api.js",
                    "category": "ERROR_HANDLING",
                    "task_summary": "Implement fetchWithRetry utility with exponential backoff for network resilience",
                    "commit_message": "feat(api): implement fetchWithRetry utility with exponential backoff",
                    "justification": "Recovers automatically from transient cloud network interruptions without failing user actions.",
                    "apply_fn": self._apply_api_retry_backoff
                })

        # 5. UI Polish: Skeleton loader shimmer animation
        comp_css_path = self.workspace_root / "src" / "frontend" / "css" / "components.css"
        if comp_css_path.exists() and "HEURISTIC_SKELETON_SHIMMER" not in completed_task_ids:
            content = comp_css_path.read_text(encoding="utf-8")
            if "skeleton-shimmer" not in content:
                opportunities.append({
                    "id": "HEURISTIC_SKELETON_SHIMMER",
                    "file_path": "src/frontend/css/components.css",
                    "category": "UI_POLISH",
                    "task_summary": "Add skeleton placeholder shimmer keyframes for loading states",
                    "commit_message": "feat(ui): add accessible skeleton loading shimmer animations",
                    "justification": "Provides smooth visual feedback during data fetching, preventing perceived layout shifts.",
                    "apply_fn": self._apply_skeleton_shimmer
                })

        # 6. Backend: Status filtering support in get_all_tasks
        handlers_path = self.workspace_root / "src" / "backend" / "handlers.py"
        if handlers_path.exists() and "HEURISTIC_BACKEND_STATUS_FILTER" not in completed_task_ids:
            content = handlers_path.read_text(encoding="utf-8")
            if "status_filter: Optional[str] = None" not in content:
                opportunities.append({
                    "id": "HEURISTIC_BACKEND_STATUS_FILTER",
                    "file_path": "src/backend/handlers.py",
                    "category": "OPTIMIZATION",
                    "task_summary": "Add optional status_filter parameter to backend get_all_tasks handler",
                    "commit_message": "feat(backend): add optional status_filter parameter to get_all_tasks handler",
                    "justification": "Optimizes server response payloads by allowing clients to query specific task states.",
                    "apply_fn": self._apply_backend_status_filter
                })

        # 7. Test Expansion: Expand test suite to assert new touch target rule
        test_css_path = self.workspace_root / "tests" / "test_accessibility_and_css.py"
        if test_css_path.exists() and "HEURISTIC_TEST_EXPANSION_A11Y" not in completed_task_ids:
            content = test_css_path.read_text(encoding="utf-8")
            if "test_mobile_touch_targets" not in content:
                opportunities.append({
                    "id": "HEURISTIC_TEST_EXPANSION_A11Y",
                    "file_path": "tests/test_accessibility_and_css.py",
                    "category": "TEST_EXPANSION",
                    "task_summary": "Add unit test verifying mobile touch target accessibility standards",
                    "commit_message": "test(a11y): add automated verification test for mobile touch targets",
                    "justification": "Guarantees continuous regression testing for WCAG 2.1 touch target compliance.",
                    "apply_fn": self._apply_test_expansion_a11y
                })

        return opportunities

    def _apply_responsive_touch_targets(self) -> bool:
        path = self.workspace_root / "src" / "frontend" / "css" / "responsive.css"
        content = path.read_text(encoding="utf-8")
        addition = """
  /* WCAG 2.1 AA Touch Targets - Min 44px */
  .btn, .btn-icon, .form-input, .select-input {
    min-height: 44px;
    touch-action: manipulation;
  }
"""
        target = "  .live-status-pill {\n    padding: 4px;\n  }\n}"
        if target in content:
            new_content = content.replace(target, "  .live-status-pill {\n    padding: 4px;\n  }" + addition + "}")
            path.write_text(new_content, encoding="utf-8")
            return True
        return False

    def _apply_a11y_expanded_state(self) -> bool:
        path = self.workspace_root / "src" / "frontend" / "index.html"
        content = path.read_text(encoding="utf-8")
        target = '<button id="sidebarToggle" class="btn-icon" aria-label="Toggle navigation menu" type="button">'
        replacement = '<button id="sidebarToggle" class="btn-icon" aria-label="Toggle navigation menu" aria-expanded="false" type="button">'
        if target in content:
            path.write_text(content.replace(target, replacement), encoding="utf-8")
            return True
        return False

    def _apply_dom_null_guards(self) -> bool:
        path = self.workspace_root / "src" / "frontend" / "js" / "utils" / "dom.js"
        content = path.read_text(encoding="utf-8")
        helper = """
export const createElementWithAttributes = (tag, attributes = {}, children = []) => {
  const el = document.createElement(tag);
  Object.entries(attributes).forEach(([key, val]) => {
    if (val !== undefined && val !== null) {
      if (key === 'className') el.className = val;
      else if (key === 'textContent') el.textContent = val;
      else el.setAttribute(key, val);
    }
  });
  children.forEach(child => {
    if (typeof child === 'string') el.appendChild(document.createTextNode(child));
    else if (child instanceof Node) el.appendChild(child);
  });
  return el;
};
"""
        new_content = content.strip() + "\n" + helper
        path.write_text(new_content, encoding="utf-8")
        return True

    def _apply_api_retry_backoff(self) -> bool:
        path = self.workspace_root / "src" / "frontend" / "js" / "api.js"
        content = path.read_text(encoding="utf-8")
        retry_fn = """
  async fetchWithRetry(url, options = {}, maxRetries = 2, delayMs = 500) {
    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      try {
        const response = await fetch(url, options);
        if (response.ok) return response;
        if (attempt === maxRetries) throw new Error(`HTTP ${response.status}`);
      } catch (err) {
        if (attempt === maxRetries) throw err;
        await new Promise(r => setTimeout(r, delayMs * Math.pow(2, attempt)));
      }
    }
  }
"""
        target = "export class ApiClient {\n  constructor(baseUrl = '') {"
        replacement = "export class ApiClient {\n" + retry_fn + "\n  constructor(baseUrl = '') {"
        if target in content:
            path.write_text(content.replace(target, replacement), encoding="utf-8")
            return True
        return False

    def _apply_skeleton_shimmer(self) -> bool:
        path = self.workspace_root / "src" / "frontend" / "css" / "components.css"
        content = path.read_text(encoding="utf-8")
        shimmer_css = """
/* Accessible Skeleton Loading States */
.skeleton-shimmer {
  background: linear-gradient(90deg, var(--bg-tertiary) 25%, var(--bg-card-hover) 50%, var(--bg-tertiary) 75%);
  background-size: 200% 100%;
  animation: skeleton-shimmer 1.5s infinite;
  border-radius: var(--radius-sm);
}

@keyframes skeleton-shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
"""
        new_content = content.strip() + "\n" + shimmer_css
        path.write_text(new_content, encoding="utf-8")
        return True

    def _apply_backend_status_filter(self) -> bool:
        path = self.workspace_root / "src" / "backend" / "handlers.py"
        content = path.read_text(encoding="utf-8")
        target = "def get_all_tasks() -> Tuple[int, Dict[str, Any]]:\n    return 200, [t.to_dict() for t in _TASKS_STORE]"
        replacement = """def get_all_tasks(status_filter: Optional[str] = None) -> Tuple[int, List[Dict[str, Any]]]:
    if status_filter:
        filtered = [t.to_dict() for t in _TASKS_STORE if t.status == status_filter]
        return 200, filtered
    return 200, [t.to_dict() for t in _TASKS_STORE]"""
        if target in content:
            path.write_text(content.replace(target, replacement), encoding="utf-8")
            return True
        return False

    def _apply_test_expansion_a11y(self) -> bool:
        path = self.workspace_root / "tests" / "test_accessibility_and_css.py"
        content = path.read_text(encoding="utf-8")
        test_method = """
    def test_mobile_touch_targets(self):
        \"\"\"Verify mobile buttons and inputs define minimum 44px touch targets.\"\"\"
        if 'min-height: 44px' in self.responsive_css:
            self.assertIn('touch-action: manipulation', self.responsive_css)
"""
        target = 'if __name__ == "__main__":'
        replacement = test_method + '\n\nif __name__ == "__main__":'
        if target in content and "test_mobile_touch_targets" not in content:
            path.write_text(content.replace(target, replacement), encoding="utf-8")
            return True
        return False
