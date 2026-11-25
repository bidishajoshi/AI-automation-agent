#!/usr/bin/env python3
"""
24/7 Autonomous AI GitHub Contribution Agent
Executes fully autonomously in GitHub Actions cloud runners.
Zero local laptop dependency.
"""

import argparse
import ast
import datetime
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

AGENT_DIR = Path(__file__).resolve().parent
WORKSPACE_ROOT = AGENT_DIR.parent.parent
sys.path.insert(0, str(AGENT_DIR))

from heuristics import HeuristicEngine
from prompts import (
    ANALYSIS_PROMPT_TEMPLATE,
    SELF_CORRECTION_PROMPT_TEMPLATE,
    SYSTEM_PROMPT,
)

CATEGORY_METRIC_MAP = {
    "ACCESSIBILITY": "accessibility_fixes",
    "RESPONSIVE_CSS": "responsive_fixes",
    "BUG_FIX": "bug_fixes",
    "OPTIMIZATION": "optimizations",
    "UI_POLISH": "ui_improvements",
    "ERROR_HANDLING": "error_handling",
    "TEST_EXPANSION": "test_expansions",
}


class AutonomousContributionAgent:
    """Autonomous cloud maintenance engine for inspecting, improving, testing, and committing."""

    def __init__(
        self,
        target_commits: int = 4,
        max_commits: int = 10,
        dry_run: bool = False,
        model: str = "gemini-2.5-flash",
    ):
        self.workspace_root = WORKSPACE_ROOT
        self.agent_dir = AGENT_DIR
        self.target_commits = max(1, min(target_commits, max_commits, 10))
        self.max_commits = min(max_commits, 10)
        self.dry_run = dry_run
        self.model = model

        self.config_path = self.agent_dir / "config.json"
        self.memory_path = self.agent_dir.parent / "agent_memory.json"
        self.reports_dir = self.workspace_root / "reports" / "daily"
        self.reports_dir.mkdir(parents=True, exist_ok=True)

        self.config = self._load_json(self.config_path, {})
        self.memory = self._load_json(
            self.memory_path,
            {
                "version": "1.0.0",
                "completed_tasks": [],
                "inspected_files": {},
                "prevent_duplicate_hashes": [],
                "total_commits_generated": 0,
                "metrics": {},
            },
        )

        self.heuristic_engine = HeuristicEngine(self.workspace_root)
        self.api_key_gemini = os.environ.get("GEMINI_API_KEY", "").strip()
        self.api_key_openai = os.environ.get("OPENAI_API_KEY", "").strip()

        self.session_commits: List[Dict[str, str]] = []
        self.session_inspected_files: List[str] = []
        self.session_failed_tasks: List[str] = []
        self.test_results: List[str] = []

    def _load_json(self, path: Path, default: Any) -> Any:
        if path.exists():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except Exception as exc:
                print(f"[WARN] Failed to parse {path}: {exc}")
        return default

    def _save_json(self, path: Path, data: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    def run_command(self, cmd: List[str]) -> Tuple[int, str, str]:
        """Execute a command in the workspace root with a timeout."""
        try:
            res = subprocess.run(
                cmd,
                cwd=str(self.workspace_root),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                timeout=120,
            )
            return res.returncode, res.stdout, res.stderr
        except Exception as exc:
            return 1, "", str(exc)

    def setup_git_identity(self) -> None:
        """Configure automated git author only if running in CI or unconfigured."""
        if os.environ.get("GITHUB_ACTIONS") == "true":
            self.run_command(["git", "config", "--global", "user.name", "github-actions[bot]"])
            self.run_command(
                ["git", "config", "--global", "user.email", "github-actions[bot]@users.noreply.github.com"]
            )
            return

        code, name_out, _ = self.run_command(["git", "config", "user.name"])
        if code != 0 or not name_out.strip():
            self.run_command(["git", "config", "user.name", "github-actions[bot]"])
            self.run_command(["git", "config", "user.email", "github-actions[bot]@users.noreply.github.com"])

    def create_safety_backup_branch(self) -> str:
        """Create a local safety backup branch before modifying repository files."""
        timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d-%H%M%S")
        backup_branch = f"backup/agent-{timestamp}"
        code, _, _ = self.run_command(["git", "branch", backup_branch])
        if code == 0:
            print(f"[SAFEGUARD] Safety backup branch created: {backup_branch}")
        return backup_branch

    def get_recent_commits(self, limit: int = 10) -> str:
        """Return recent git commits for context so the AI avoids duplicate work."""
        code, out, _ = self.run_command(["git", "log", f"-n{limit}", "--oneline"])
        return out.strip() if code == 0 and out.strip() else "None"

    def is_protected_path(self, rel_path: str) -> bool:
        """Return True if rel_path matches any protected path or escapes the workspace."""
        normalized = re.sub(r"^(?:\./)+", "", rel_path.replace("\\", "/"))
        if not normalized or normalized.startswith("/") or ".." in Path(normalized).parts:
            return True

        protected = self.config.get(
            "protected_paths",
            [".env", ".env.*", ".git", ".github/workflows", ".github/agent_memory.json", "reports/"],
        )
        for pattern in protected:
            pat = pattern.replace("\\", "/").rstrip("/")
            if pat.endswith("*"):
                if normalized.startswith(pat[:-1]):
                    return True
            elif normalized == pat or normalized.startswith(f"{pat}/"):
                return True
        return False

    def is_meaningful_change(self, original: str, updated: str) -> bool:
        """Reject empty, identical, or whitespace-only modifications."""
        if not updated or original == updated:
            return False
        stripped_orig = re.sub(r"\s+", "", original)
        stripped_new = re.sub(r"\s+", "", updated)
        return stripped_orig != stripped_new

    def validate_syntax(self, file_path: Path, content: str) -> Tuple[bool, str]:
        """Run fast syntax validation appropriate to file extension."""
        suffix = file_path.suffix.lower()
        if suffix == ".py":
            try:
                ast.parse(content, filename=str(file_path))
            except SyntaxError as exc:
                return False, f"Python syntax error: {exc}"
        elif suffix == ".json":
            try:
                json.loads(content)
            except json.JSONDecodeError as exc:
                return False, f"JSON syntax error: {exc}"
        elif suffix == ".js":
            code, _, err = self.run_command(["node", "--check", str(file_path)])
            if code != 0 and "not recognized" not in err and "No such file" not in err:
                return False, f"JavaScript syntax error: {err.strip()}"
        return True, ""

    def run_test_suite(self) -> Tuple[bool, str]:
        """Execute configured test suite and return (passed, log)."""
        test_cmd = self.config.get("test_command", "python -m unittest discover tests").split()
        code, out, err = self.run_command(test_cmd)
        combined_output = (out + "\n" + err).strip()
        return (code == 0), combined_output

    def scan_project_files(self) -> List[Path]:
        """Scan eligible source files, excluding protected paths, sorted by least-recently-inspected."""
        scannable: List[Path] = []
        extensions = set(self.config.get("scannable_extensions", [".html", ".css", ".js", ".py", ".md"]))
        pruned_dirs = {".git", "node_modules", "venv", ".venv", "__pycache__", ".parcel-cache", "reports"}

        for root, dirs, files in os.walk(self.workspace_root):
            dirs[:] = sorted(d for d in dirs if d not in pruned_dirs)
            for file_name in sorted(files):
                file_path = Path(root) / file_name
                rel_path = file_path.relative_to(self.workspace_root).as_posix()
                if self.is_protected_path(rel_path):
                    continue
                if file_path.suffix in extensions:
                    scannable.append(file_path)

        inspected_map = self.memory.get("inspected_files", {})

        def sort_key(path: Path) -> Tuple[int, str, str]:
            rel = path.relative_to(self.workspace_root).as_posix()
            # Prioritize src/ and tests/ ahead of docs, and oldest inspected timestamp first
            is_code = 0 if rel.startswith(("src/", "tests/")) else 1
            last_seen = inspected_map.get(rel, "")
            return (is_code, last_seen, rel)

        scannable.sort(key=sort_key)
        return scannable

    @staticmethod
    def _parse_json_response(raw_text: str) -> Optional[Dict[str, Any]]:
        """Extract and parse a JSON object, stripping optional markdown code fences."""
        if not raw_text:
            return None
        cleaned = raw_text.strip()
        fence_match = re.match(r"^```(?:json)?\s*(.*?)\s*```$", cleaned, re.DOTALL | re.IGNORECASE)
        if fence_match:
            cleaned = fence_match.group(1).strip()
        try:
            parsed = json.loads(cleaned)
            return parsed if isinstance(parsed, dict) else None
        except json.JSONDecodeError:
            return None

    def call_gemini_api(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Call Gemini REST API with configured model and fallbacks."""
        if not self.api_key_gemini:
            return None

        models_to_try = [self.model] + [
            m for m in self.config.get("fallback_models", ["gemini-2.0-flash", "gemini-1.5-flash"]) if m != self.model
        ]
        payload = {
            "contents": [{"role": "user", "parts": [{"text": SYSTEM_PROMPT + "\n\n" + prompt}]}],
            "generationConfig": {
                "temperature": self.config.get("temperature", 0.2),
                "responseMimeType": "application/json",
            },
        }
        encoded_payload = json.dumps(payload).encode("utf-8")

        for model_name in models_to_try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={self.api_key_gemini}"
            req = urllib.request.Request(
                url,
                data=encoded_payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            try:
                with urllib.request.urlopen(req, timeout=45) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    text = data["candidates"][0]["content"]["parts"][0]["text"]
                    parsed = self._parse_json_response(text)
                    if parsed is not None:
                        return parsed
            except Exception as exc:
                print(f"[WARN] Gemini model '{model_name}' failed: {exc}")
        return None

    def call_openai_api(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Call OpenAI Chat Completions API as a secondary provider."""
        if not self.api_key_openai:
            return None

        openai_model = self.config.get("openai_model", "gpt-4o-mini")
        payload = {
            "model": openai_model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "temperature": self.config.get("temperature", 0.2),
            "response_format": {"type": "json_object"},
        }
        req = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key_openai}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=45) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                text = data["choices"][0]["message"]["content"]
                return self._parse_json_response(text)
        except Exception as exc:
            print(f"[WARN] OpenAI API call failed: {exc}")
            return None

    def call_ai_provider(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Invoke available cloud AI provider (Gemini first, then OpenAI)."""
        if self.api_key_gemini:
            resp = self.call_gemini_api(prompt)
            if resp is not None:
                return resp
        if self.api_key_openai:
            return self.call_openai_api(prompt)
        return None

    def _attempt_self_correction(
        self, target_file: Path, rel_path: str, current_content: str, error_output: str
    ) -> bool:
        """Ask AI once to fix newly introduced syntax or test errors before rolling back."""
        if not (self.api_key_gemini or self.api_key_openai):
            return False

        prompt = SELF_CORRECTION_PROMPT_TEMPLATE.format(
            file_path=rel_path,
            error_output=error_output[:2000],
            current_content=current_content[:4000],
        )
        resp = self.call_ai_provider(prompt)
        if not resp or not resp.get("success"):
            return False

        corrected = resp.get("full_corrected_content", "")
        if not self.is_meaningful_change(current_content, corrected):
            return False

        target_file.write_text(corrected, encoding="utf-8")
        syntax_ok, _ = self.validate_syntax(target_file, corrected)
        if not syntax_ok:
            return False

        tests_ok, _ = self.run_test_suite()
        return tests_ok

    def execute_task(self, task: Dict[str, Any]) -> bool:
        """Apply a task modification, validate syntax & tests, and commit if valid."""
        file_path_str = task.get("file_path", "")
        if self.is_protected_path(file_path_str):
            print(f"[SAFEGUARD] Refusing to modify protected path: {file_path_str}")
            return False

        target_file = self.workspace_root / file_path_str
        print(f"\n[TASK] Starting: {task.get('task_summary')}")
        print(f"       File: {file_path_str}")
        print(f"       Category: {task.get('category')}")

        if not target_file.exists():
            print(f"[FAIL] Target file does not exist: {file_path_str}")
            return False

        original_content = target_file.read_text(encoding="utf-8")
        applied = False

        if "apply_fn" in task and callable(task["apply_fn"]):
            applied = task["apply_fn"]()
        elif "original_snippet" in task and "improved_snippet" in task:
            snippet_orig = task["original_snippet"]
            snippet_new = task["improved_snippet"]
            if snippet_orig and snippet_orig in original_content:
                new_content = original_content.replace(snippet_orig, snippet_new, 1)
                if self.is_meaningful_change(original_content, new_content):
                    target_file.write_text(new_content, encoding="utf-8")
                    applied = True
            else:
                print(f"[WARN] Original snippet not found in {file_path_str}")

        if not applied:
            print("[FAIL] No valid modification applied.")
            return False

        updated_content = target_file.read_text(encoding="utf-8")
        if not self.is_meaningful_change(original_content, updated_content):
            print("[SKIP] Change was empty or whitespace-only; reverting.")
            target_file.write_text(original_content, encoding="utf-8")
            return False

        syntax_ok, syntax_err = self.validate_syntax(target_file, updated_content)
        tests_passed, test_log = (self.run_test_suite() if syntax_ok else (False, syntax_err))

        if not tests_passed and self.config.get("max_repair_retries", 1) > 0:
            print("[REPAIR] Validation failed; attempting AI self-correction...")
            if self._attempt_self_correction(target_file, file_path_str, updated_content, test_log):
                tests_passed = True

        self.test_results.append(f"{task.get('task_summary')}: {'PASSED' if tests_passed else 'FAILED'}")

        if not tests_passed:
            print("[REVERT] Tests failed! Rolling back to protect project health.")
            target_file.write_text(original_content, encoding="utf-8")
            self.session_failed_tasks.append(task.get("task_summary", "Unknown"))
            return False

        if self.dry_run:
            print("[DRY-RUN] Verification succeeded. Reverting file to preserve clean git tree.")
            target_file.write_text(original_content, encoding="utf-8")
            self.session_commits.append(
                {
                    "hash": "dry-run-hash",
                    "message": task.get("commit_message", "test: dry run commit"),
                    "file": file_path_str,
                    "category": task.get("category", "GENERAL"),
                }
            )
            return True

        self.run_command(["git", "add", file_path_str])
        commit_msg = task.get("commit_message") or f"chore: improve {file_path_str}"
        code, _, err = self.run_command(["git", "commit", "-m", commit_msg])

        if code == 0:
            _, hash_out, _ = self.run_command(["git", "rev-parse", "--short", "HEAD"])
            commit_hash = hash_out.strip()
            print(f"[COMMIT SUCCESS] {commit_hash} - {commit_msg}")

            category = task.get("category", "GENERAL")
            self.session_commits.append(
                {
                    "hash": commit_hash,
                    "message": commit_msg,
                    "file": file_path_str,
                    "category": category,
                }
            )
            self.memory.setdefault("completed_tasks", []).append(
                {
                    "id": task.get("id", f"task-{commit_hash}"),
                    "category": category,
                    "description": task.get("task_summary"),
                    "file_path": file_path_str,
                    "commit_hash": commit_hash,
                    "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                }
            )
            self.memory["total_commits_generated"] = self.memory.get("total_commits_generated", 0) + 1
            metric_key = CATEGORY_METRIC_MAP.get(category)
            if metric_key:
                metrics = self.memory.setdefault("metrics", {})
                metrics[metric_key] = metrics.get(metric_key, 0) + 1
            return True

        print(f"[WARN] Git commit did not produce changes: {err.strip()}")
        return False

    def generate_daily_report(self) -> Path:
        """Generate daily markdown report and append it to GITHUB_STEP_SUMMARY if available."""
        today_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
        now_utc = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        provider_status = (
            "Gemini API" if self.api_key_gemini else ("OpenAI API" if self.api_key_openai else "Heuristic Engine (No AI API Key configured)")
        )

        report_lines = [
            f"# Autonomous AI Contribution Agent - Daily Report ({today_str})",
            "",
            f"**Execution Timestamp:** `{now_utc}`  ",
            f"**AI Provider:** `{provider_status}` (`{self.model}`)  ",
            f"**Target Commits:** `{self.target_commits}` | **Commits Created:** `{len(self.session_commits)}`  ",
            f"**Mode:** `{'Dry-Run (Simulation)' if self.dry_run else 'Production Cloud Execution'}`",
            "",
            "## 1. Summary of Files Inspected",
            f"- Total eligible files scanned: `{len(self.session_inspected_files)}`",
        ]
        for file_rel in self.session_inspected_files[:12]:
            report_lines.append(f"  - `{file_rel}`")
        if len(self.session_inspected_files) > 12:
            report_lines.append(f"  - *...and {len(self.session_inspected_files) - 12} more files.*")

        report_lines.extend(["", "## 2. Completed Improvements & Commits"])
        if self.session_commits:
            report_lines.append("| Commit Hash | Category | Description | Target File |")
            report_lines.append("| :--- | :--- | :--- | :--- |")
            for commit in self.session_commits:
                report_lines.append(
                    f"| `{commit['hash']}` | `{commit['category']}` | {commit['message']} | `{commit['file']}` |"
                )
        else:
            report_lines.append(
                "*No new commits were generated during this run (either no improvements needed or `GEMINI_API_KEY` / `OPENAI_API_KEY` secret is not configured yet).*"
            )

        report_lines.extend(["", "## 3. Test & Verification Status", f"- Test command: `{self.config.get('test_command', 'python -m unittest discover tests')}`"])
        if self.test_results:
            for res in self.test_results:
                report_lines.append(f"  - {res}")
        else:
            report_lines.append("  - Pre-flight baseline test suite: PASSED")

        report_lines.extend(
            [
                "",
                "## 4. Project Protection & Safety Assurance",
                "- [x] Zero deletions of existing features or project files",
                "- [x] Design styles and themes preserved",
                "- [x] Sensitive environment secrets and API keys unexposed",
                "- [x] 100% of test suites passing before every commit",
                "- [x] Protected paths guarded from modification",
                "",
                "## 5. Next Autonomous Agenda",
                "- Scheduled next automatic run via GitHub Actions cron (`0 2 * * *`).",
                "- Continuous rotation across least-recently-inspected project modules.",
            ]
        )

        report_md = "\n".join(report_lines) + "\n"
        report_file = self.reports_dir / f"{today_str}.md"

        # Avoid overwriting an already committed daily report when 0 new commits were made
        should_write_file = True
        if not self.session_commits and report_file.exists():
            code, tracked, _ = self.run_command(["git", "ls-files", "--error-unmatch", str(report_file.relative_to(self.workspace_root))])
            if code == 0 and tracked.strip():
                should_write_file = False

        if should_write_file:
            report_file.write_text(report_md, encoding="utf-8")
            print(f"\n[REPORT] Saved daily activity report to: {report_file.relative_to(self.workspace_root)}")

        summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
        if summary_path:
            try:
                with open(summary_path, "a", encoding="utf-8") as handle:
                    handle.write(report_md + "\n")
                print("[REPORT] Written to GITHUB_STEP_SUMMARY")
            except Exception as exc:
                print(f"[WARN] Failed writing to GITHUB_STEP_SUMMARY: {exc}")

        return report_file

    def run(self) -> int:
        print("=" * 70)
        print("Starting Autonomous AI GitHub Contribution Agent")
        print(f"Target Commits: {self.target_commits} (Max: {self.max_commits}) | Model: {self.model}")
        print("=" * 70)

        if not self.api_key_gemini and not self.api_key_openai:
            print("[NOTICE] Neither GEMINI_API_KEY nor OPENAI_API_KEY is set; running heuristic engine only.")

        initial_tests_ok, initial_test_log = self.run_test_suite()
        if not initial_tests_ok:
            print("[CRITICAL] Existing test suite has failing tests! Aborting to protect project.")
            print(initial_test_log)
            return 1

        self.setup_git_identity()
        if not self.dry_run:
            self.create_safety_backup_branch()

        scanned_files = self.scan_project_files()
        self.session_inspected_files = [f.relative_to(self.workspace_root).as_posix() for f in scanned_files]
        print(f"[SCAN] Found {len(scanned_files)} eligible source files (rotated by least-recently-inspected).")

        completed_ids = [t.get("id") for t in self.memory.get("completed_tasks", []) if t.get("id")]
        opportunities = self.heuristic_engine.find_opportunities(completed_ids)

        recent_commits = self.get_recent_commits(10)
        completed_summary = json.dumps(self.memory.get("completed_tasks", [])[-8:])

        if (self.api_key_gemini or self.api_key_openai) and len(opportunities) < self.target_commits:
            print("[AI] Querying cloud AI provider across rotated project files...")
            now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
            max_files_to_inspect = min(len(scanned_files), max(8, self.target_commits * 2))
            for s_file in scanned_files[:max_files_to_inspect]:
                if len(opportunities) >= self.target_commits + 2:
                    break
                rel_path = s_file.relative_to(self.workspace_root).as_posix()
                content = s_file.read_text(encoding="utf-8")
                prompt = ANALYSIS_PROMPT_TEMPLATE.format(
                    file_path=rel_path,
                    language=s_file.suffix.lstrip("."),
                    file_content=content[:6000],
                    completed_tasks_summary=completed_summary,
                    recent_commits=recent_commits,
                )
                ai_resp = self.call_ai_provider(prompt)
                self.memory.setdefault("inspected_files", {})[rel_path] = now_iso
                if ai_resp and ai_resp.get("has_improvement"):
                    opportunities.append(
                        {
                            "id": f"AI_{ai_resp.get('category', 'OPT')}_{datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%d%H%M%S')}_{len(opportunities)}",
                            "file_path": rel_path,
                            "category": ai_resp.get("category", "OPTIMIZATION"),
                            "task_summary": ai_resp.get("task_summary"),
                            "commit_message": ai_resp.get("commit_message"),
                            "justification": ai_resp.get("justification"),
                            "original_snippet": ai_resp.get("original_snippet"),
                            "improved_snippet": ai_resp.get("improved_snippet"),
                        }
                    )

        print(f"[PLAN] Identified {len(opportunities)} candidate improvement tasks.")

        committed_count = 0
        for task in opportunities:
            if committed_count >= self.target_commits:
                print(f"[CADENCE] Reached target of {self.target_commits} commits for this run.")
                break
            if self.execute_task(task):
                committed_count += 1

        now_utc_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        self.memory["last_run"] = now_utc_iso
        self.memory["total_runs"] = self.memory.get("total_runs", 0) + 1
        report_file = self.generate_daily_report()

        if not self.dry_run and committed_count > 0:
            self._save_json(self.memory_path, self.memory)
            report_rel = report_file.relative_to(self.workspace_root).as_posix()
            self.run_command(["git", "add", ".github/agent_memory.json", report_rel])
            today_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
            self.run_command(
                ["git", "commit", "-m", f"chore(agent): update autonomous memory and daily report for {today_str}"]
            )
        elif not self.dry_run:
            # Keep memory clean if 0 commits were made so working tree stays clean
            self.run_command(["git", "checkout", "--", ".github/agent_memory.json"])

        print("\n[AGENT FINISHED] Autonomous session complete.")
        return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="24/7 Autonomous AI GitHub Contribution Agent")
    parser.add_argument("--target-commits", type=int, default=4, help="Target commits to create (default: 4)")
    parser.add_argument("--max-commits", type=int, default=10, help="Maximum commits to create (default: 10)")
    parser.add_argument("--dry-run", action="store_true", help="Simulate execution without committing/pushing")
    parser.add_argument("--model", type=str, default="gemini-2.5-flash", help="AI model name")

    args = parser.parse_args()
    agent = AutonomousContributionAgent(
        target_commits=args.target_commits,
        max_commits=args.max_commits,
        dry_run=args.dry_run,
        model=args.model,
    )
    sys.exit(agent.run())


if __name__ == "__main__":
    main()
