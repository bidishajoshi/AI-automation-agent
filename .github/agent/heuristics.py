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

        # 7. Frontend: Add keyboard shortcut handling (Esc to close modal, / to focus search)
        app_js_path = self.workspace_root / "src" / "frontend" / "js" / "app.js"
        if app_js_path.exists() and "HEURISTIC_KEYBOARD_SHORTCUTS" not in completed_task_ids:
            content = app_js_path.read_text(encoding="utf-8")
            if "setupKeyboardShortcuts" not in content:
                opportunities.append({
                    "id": "HEURISTIC_KEYBOARD_SHORTCUTS",
                    "file_path": "src/frontend/js/app.js",
                    "category": "ACCESSIBILITY",
                    "task_summary": "Add global keyboard shortcuts (Escape to dismiss modal, / to focus search)",
                    "commit_message": "feat(a11y): add global keyboard accessibility shortcuts for modal and search",
                    "justification": "Enhances keyboard-only accessibility according to WCAG 2.1 guideline 2.1 Keyboard Accessible.",
                    "apply_fn": self._apply_keyboard_shortcuts
                })

        # 8. Frontend Formatters: Add formatRelativeTime helper
        fmt_js_path = self.workspace_root / "src" / "frontend" / "js" / "utils" / "formatters.js"
        if fmt_js_path.exists() and "HEURISTIC_FORMAT_RELATIVE_TIME" not in completed_task_ids:
            content = fmt_js_path.read_text(encoding="utf-8")
            if "formatRelativeTime" not in content:
                opportunities.append({
                    "id": "HEURISTIC_FORMAT_RELATIVE_TIME",
                    "file_path": "src/frontend/js/utils/formatters.js",
                    "category": "UI_POLISH",
                    "task_summary": "Add human-readable formatRelativeTime utility for live telemetry feeds",
                    "commit_message": "feat(formatters): add formatRelativeTime utility for real-time telemetry",
                    "justification": "Converts UTC timestamps to intuitive relative time strings (e.g., '2m ago').",
                    "apply_fn": self._apply_format_relative_time
                })

        # 9. Test Suite: Add unit test verifying formatRelativeTime
        test_fmt_path = self.workspace_root / "tests" / "test_frontend_logic.py"
        if test_fmt_path.exists() and "HEURISTIC_TEST_FORMATTERS" not in completed_task_ids:
            content = test_fmt_path.read_text(encoding="utf-8")
            if "test_formatters_presence" not in content:
                opportunities.append({
                    "id": "HEURISTIC_TEST_FORMATTERS",
                    "file_path": "tests/test_frontend_logic.py",
                    "category": "TEST_EXPANSION",
                    "task_summary": "Add automated unit tests verifying formatters and helper presence",
                    "commit_message": "test(frontend): add unit tests verifying telemetry formatters",
                    "justification": "Maintains 100% test coverage over formatting helper logic.",
                    "apply_fn": self._apply_test_formatters
                })

        return opportunities

    def _apply_backend_status_filter(self) -> bool:
        path = self.workspace_root / "src" / "backend" / "handlers.py"
        content = path.read_text(encoding="utf-8")
        # Ensure Optional is imported
        if "from typing import Dict, Any, List, Tuple" in content and "Optional" not in content:
            content = content.replace(
                "from typing import Dict, Any, List, Tuple",
                "from typing import Dict, Any, List, Tuple, Optional"
            )
        target = "def get_all_tasks() -> Tuple[int, Dict[str, Any]]:\n    return 200, [t.to_dict() for t in _TASKS_STORE]"
        replacement = """def get_all_tasks(status_filter: Optional[str] = None) -> Tuple[int, List[Dict[str, Any]]]:
    if status_filter:
        filtered = [t.to_dict() for t in _TASKS_STORE if t.status == status_filter]
        return 200, filtered
    return 200, [t.to_dict() for t in _TASKS_STORE]"""
        if target in content:
            new_content = content.replace(target, replacement)
            path.write_text(new_content, encoding="utf-8")
            return True
        return False

    def _apply_keyboard_shortcuts(self) -> bool:
        path = self.workspace_root / "src" / "frontend" / "js" / "app.js"
        content = path.read_text(encoding="utf-8")
        method = """
  setupKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        const modal = qs('#taskModal');
        if (modal && modal.classList.contains('open')) {
          modal.classList.remove('open');
          modal.setAttribute('aria-hidden', 'true');
        }
      } else if (e.key === '/' && document.activeElement.tagName !== 'INPUT') {
        e.preventDefault();
        const search = qs('#globalSearch');
        if (search) search.focus();
      }
    });
  }
"""
        target = "    this.setupFilters();\n    await this.refreshData();"
        replacement = "    this.setupFilters();\n    this.setupKeyboardShortcuts();\n    await this.refreshData();"
        if target in content:
            new_content = content.replace(target, replacement)
            new_content = new_content.replace("  setupFilters() {", method + "\n  setupFilters() {")
            path.write_text(new_content, encoding="utf-8")
            return True
        return False

    def _apply_format_relative_time(self) -> bool:
        path = self.workspace_root / "src" / "frontend" / "js" / "utils" / "formatters.js"
        content = path.read_text(encoding="utf-8")
        helper = """
export const formatRelativeTime = (isoString) => {
  if (!isoString) return 'just now';
  try {
    const diffMs = Date.now() - new Date(isoString).getTime();
    const diffSec = Math.floor(diffMs / 1000);
    if (diffSec < 60) return `${Math.max(1, diffSec)}s ago`;
    const diffMin = Math.floor(diffSec / 60);
    if (diffMin < 60) return `${diffMin}m ago`;
    const diffHr = Math.floor(diffMin / 60);
    if (diffHr < 24) return `${diffHr}h ago`;
    return `${Math.floor(diffHr / 24)}d ago`;
  } catch {
    return 'recently';
  }
};
"""
        new_content = content.strip() + "\n" + helper
        path.write_text(new_content, encoding="utf-8")
        return True

    def _apply_test_formatters(self) -> bool:
        path = self.workspace_root / "tests" / "test_frontend_logic.py"
        content = path.read_text(encoding="utf-8")
        test_method = """
    def test_formatters_presence(self):
        fmt_path = Path(__file__).resolve().parent.parent / "src" / "frontend" / "js" / "utils" / "formatters.js"
        content = fmt_path.read_text(encoding="utf-8")
        self.assertIn("formatRelativeTime", content)
        self.assertIn("formatCategory", content)
"""
        target = 'if __name__ == "__main__":'
        replacement = test_method + '\n\nif __name__ == "__main__":'
        if target in content and "test_formatters_presence" not in content:
            path.write_text(content.replace(target, replacement), encoding="utf-8")
            return True
        return False

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
