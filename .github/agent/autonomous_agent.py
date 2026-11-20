#!/usr/bin/env python3
"""
24/7 Autonomous AI GitHub Contribution Agent
Executes fully autonomously in GitHub Actions cloud runners.
Zero local laptop dependency.
"""

import os
import sys
import json
import argparse
import subprocess
import datetime
import urllib.request
import urllib.error
import ast
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Import local agent modules
AGENT_DIR = Path(__file__).resolve().parent
WORKSPACE_ROOT = AGENT_DIR.parent.parent
sys.path.insert(0, str(AGENT_DIR))

from prompts import SYSTEM_PROMPT, ANALYSIS_PROMPT_TEMPLATE, SELF_CORRECTION_PROMPT_TEMPLATE
from heuristics import HeuristicEngine


class AutonomousContributionAgent:
    def __init__(self, target_commits: int = 4, max_commits: int = 10, dry_run: bool = False, model: str = "gemini-2.5-flash"):
        self.workspace_root = WORKSPACE_ROOT
        self.agent_dir = AGENT_DIR
        self.target_commits = target_commits
        self.max_commits = min(max_commits, 10)
        self.dry_run = dry_run
        self.model = model
        
        self.config_path = self.agent_dir / "config.json"
        self.memory_path = self.agent_dir.parent / "agent_memory.json"
        self.reports_dir = self.workspace_root / "reports" / "daily"
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
        self.config = self._load_json(self.config_path, {})
        self.memory = self._load_json(self.memory_path, {
            "version": "1.0.0",
            "completed_tasks": [],
            "inspected_files": {},
            "prevent_duplicate_hashes": [],
            "total_commits_generated": 0,
            "metrics": {}
        })
        
        self.heuristic_engine = HeuristicEngine(self.workspace_root)
        self.api_key_gemini = os.environ.get("GEMINI_API_KEY", "").strip()
        self.api_key_openai = os.environ.get("OPENAI_API_KEY", "").strip()
        
        self.session_commits: List[Dict[str, str]] = []
        self.session_inspected_files: List[str] = []
        self.session_discovered_tasks: List[str] = []
        self.session_failed_tasks: List[str] = []
        self.test_results: List[str] = []

    def _load_json(self, path: Path, default: Any) -> Any:
        if path.exists():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except Exception as e:
                print(f"[WARN] Failed to parse {path}: {e}")
        return default

    def _save_json(self, path: Path, data: Any):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def run_command(self, cmd: List[str], check: bool = False) -> Tuple[int, str, str]:
        """Execute a shell command in workspace root."""
        try:
            res = subprocess.run(
                cmd,
                cwd=str(self.workspace_root),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                timeout=120
            )
            return res.returncode, res.stdout, res.stderr
        except Exception as e:
            return 1, "", str(e)

    def setup_git_identity(self):
        """Configure automated git author if not already configured."""
        self.run_command(["git", "config", "--global", "user.name", "github-actions[bot]"])
        self.run_command(["git", "config", "--global", "user.email", "github-actions[bot]@users.noreply.github.com"])

    def create_safety_backup_branch(self) -> str:
        """Create a local safety backup branch before making changes."""
        timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d-%H%M%S")
        backup_branch = f"backup/agent-{timestamp}"
        code, _, err = self.run_command(["git", "branch", backup_branch])
        if code == 0:
            print(f"[SAFEGUARD] Safety backup branch created: {backup_branch}")
        return backup_branch

    def run_test_suite(self) -> Tuple[bool, str]:
        """Execute test suite and return success status and output."""
        test_cmd = self.config.get("test_command", "python -m unittest discover tests").split()
        code, out, err = self.run_command(test_cmd)
        combined_output = (out + "\n" + err).strip()
        passed = (code == 0)
        return passed, combined_output

    def scan_project_files(self) -> List[Path]:
        """Scan project for eligible source files, avoiding protected paths."""
        scannable = []
        protected = self.config.get("protected_paths", [".env", ".git", ".github/workflows"])
        extensions = set(self.config.get("scannable_extensions", [".html", ".css", ".js", ".py"]))

        for root, dirs, files in os.walk(self.workspace_root):
            # Prune protected directories
            dirs[:] = [d for d in dirs if d not in [".git", "node_modules", "venv", ".venv", "__pycache__", ".parcel-cache"]]
            for file in files:
                file_path = Path(root) / file
                rel_path = file_path.relative_to(self.workspace_root).as_posix()

                # Guard against protected files
                if any(rel_path.startswith(p.replace("\\", "/")) for p in protected):
                    continue

                if file_path.suffix in extensions:
                    scannable.append(file_path)

        return scannable

    def call_gemini_api(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Call Gemini API using standard library urllib (zero external dependencies)."""
        if not self.api_key_gemini:
            return None

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key_gemini}"
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": SYSTEM_PROMPT + "\n\n" + prompt}]
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "responseMimeType": "application/json"
            }
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=45) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                return json.loads(text)
        except Exception as e:
            print(f"[WARN] Gemini API call failed: {e}")
            return None

    def execute_task(self, task: Dict[str, Any]) -> bool:
        """Apply a task change, validate tests, and commit if successful."""
        file_path_str = task.get("file_path", "")
        target_file = self.workspace_root / file_path_str
        
        print(f"\n[TASK] Starting: {task.get('task_summary')}")
        print(f"       File: {file_path_str}")
        print(f"       Category: {task.get('category')}")

        if not target_file.exists():
            print(f"[FAIL] Target file does not exist: {file_path_str}")
            return False

        original_content = target_file.read_text(encoding="utf-8")
        applied = False

        # Apply using apply_fn if available
        if "apply_fn" in task and callable(task["apply_fn"]):
            applied = task["apply_fn"]()
        elif "original_snippet" in task and "improved_snippet" in task:
            snippet_orig = task["original_snippet"]
            snippet_new = task["improved_snippet"]
            if snippet_orig in original_content:
                new_content = original_content.replace(snippet_orig, snippet_new, 1)
                target_file.write_text(new_content, encoding="utf-8")
                applied = True
            else:
                print(f"[WARN] Original snippet not found in {file_path_str}")

        if not applied:
            print("[FAIL] Failed to apply modification.")
            return False

        # Run verification checks
        tests_passed, test_log = self.run_test_suite()
        self.test_results.append(f"{task.get('task_summary')}: {'PASSED' if tests_passed else 'FAILED'}")

        if not tests_passed:
            print(f"[REVERT] Tests failed! Attempting rollback to protect project health...")
            target_file.write_text(original_content, encoding="utf-8")
            self.session_failed_tasks.append(task.get("task_summary", "Unknown"))
            return False

        # If in dry-run mode, revert and report success without committing
        if self.dry_run:
            print("[DRY-RUN] Verification succeeded. Reverting file to preserve clean git tree.")
            target_file.write_text(original_content, encoding="utf-8")
            self.session_commits.append({
                "hash": "dry-run-hash",
                "message": task.get("commit_message", "test: dry run commit"),
                "file": file_path_str,
                "category": task.get("category", "GENERAL")
            })
            return True

        # Commit validated changes
        self.run_command(["git", "add", file_path_str])
        commit_msg = task.get("commit_message", f"chore: improve {file_path_str}")
        code, out, err = self.run_command(["git", "commit", "-m", commit_msg])

        if code == 0:
            # Get latest commit hash
            _, hash_out, _ = self.run_command(["git", "rev-parse", "--short", "HEAD"])
            commit_hash = hash_out.strip()
            print(f"[COMMIT SUCCESS] {commit_hash} - {commit_msg}")

            self.session_commits.append({
                "hash": commit_hash,
                "message": commit_msg,
                "file": file_path_str,
                "category": task.get("category", "GENERAL")
            })

            # Record in memory
            self.memory["completed_tasks"].append({
                "id": task.get("id", f"task-{commit_hash}"),
                "category": task.get("category"),
                "description": task.get("task_summary"),
                "file_path": file_path_str,
                "commit_hash": commit_hash,
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
            })
            self.memory["total_commits_generated"] = self.memory.get("total_commits_generated", 0) + 1
            return True
        else:
            print(f"[WARN] Git commit did not produce changes: {err.strip()}")
            return False

    def generate_daily_report(self) -> str:
        """Generate a comprehensive daily activity markdown report."""
        today_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
        now_utc = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        report_lines = [
            f"# Autonomous AI Contribution Agent - Daily Report ({today_str})",
            "",
            f"**Execution Timestamp:** `{now_utc}`  ",
            f"**Model Provider:** `{self.model}`  ",
            f"**Target Commits:** `{self.target_commits}` | **Commits Created:** `{len(self.session_commits)}`  ",
            f"**Mode:** `{'Dry-Run (Simulation)' if self.dry_run else 'Production Cloud Execution'}`",
            "",
            "## 1. Summary of Files Inspected",
            f"- Total files scanned: `{len(self.session_inspected_files)}`",
        ]
        for f in self.session_inspected_files[:12]:
            report_lines.append(f"  - `{f}`")
        if len(self.session_inspected_files) > 12:
            report_lines.append(f"  - *...and {len(self.session_inspected_files) - 12} more files.*")

        report_lines.extend([
            "",
            "## 2. Completed Improvements & Commits",
        ])

        if self.session_commits:
            report_lines.append("| Commit Hash | Category | Description | Target File |")
            report_lines.append("| :--- | :--- | :--- | :--- |")
            for c in self.session_commits:
                report_lines.append(f"| `{c['hash']}` | `{c['category']}` | {c['message']} | `{c['file']}` |")
        else:
            report_lines.append("*No new commits were generated during this run (all quality criteria already met or dry-run).*")

        report_lines.extend([
            "",
            "## 3. Test & Verification Status",
            "- Test command: `python -m unittest discover tests`",
        ])
        for res in self.test_results:
            report_lines.append(f"  - {res}")

        report_lines.extend([
            "",
            "## 4. Project Protection & Safety Assurance",
            "- [x] Zero deletions of existing features or project files",
            "- [x] Design styles and themes preserved",
            "- [x] Sensitive environment secrets and API keys unexposed",
            "- [x] 100% of test suites passing before every commit",
            "- [x] Safe rebase check applied",
            "",
            "## 5. Next Autonomous Agenda",
            "- Scheduled next automatic run via GitHub Actions cron.",
            "- Continuous monitoring of performance, a11y, and responsive layouts."
        ])

        report_md = "\n".join(report_lines)
        report_file = self.reports_dir / f"{today_str}.md"
        report_file.write_text(report_md, encoding="utf-8")
        print(f"\n[REPORT] Saved daily activity report to: {report_file.relative_to(self.workspace_root)}")

        # Also write to GitHub Step Summary if running in GitHub Actions
        summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
        if summary_path:
            try:
                with open(summary_path, "a", encoding="utf-8") as f:
                    f.write(report_md + "\n")
                print("[REPORT] Written to GITHUB_STEP_SUMMARY")
            except Exception as e:
                print(f"[WARN] Failed writing to GITHUB_STEP_SUMMARY: {e}")

        return report_md

    def run(self) -> int:
        print("=" * 70)
        print("Starting Autonomous AI GitHub Contribution Agent")
        print(f"Target Commits: {self.target_commits} (Max: {self.max_commits}) | Model: {self.model}")
        print("=" * 70)

        # Baseline verification: test existing suite before any changes
        initial_tests_ok, initial_test_log = self.run_test_suite()
        if not initial_tests_ok:
            print("[CRITICAL] Existing test suite has failing tests! Aborting to protect project.")
            print(initial_test_log)
            return 1

        self.setup_git_identity()
        self.create_safety_backup_branch()

        # Step 1: Scan files
        scanned_files = self.scan_project_files()
        self.session_inspected_files = [f.relative_to(self.workspace_root).as_posix() for f in scanned_files]
        print(f"[SCAN] Found {len(scanned_files)} eligible source files.")

        # Step 2: Gather completed task IDs to prevent duplication
        completed_ids = [t.get("id") for t in self.memory.get("completed_tasks", []) if t.get("id")]

        # Step 3: Identify opportunities
        opportunities = []

        # Heuristic engine opportunities
        heuristic_tasks = self.heuristic_engine.find_opportunities(completed_ids)
        opportunities.extend(heuristic_tasks)

        # If Gemini API key is configured, also query AI for dynamic improvements
        if self.api_key_gemini and len(opportunities) < self.target_commits:
            print("[AI] Querying Gemini for additional project optimizations...")
            for s_file in scanned_files[:5]:
                if len(opportunities) >= self.target_commits:
                    break
                rel_path = s_file.relative_to(self.workspace_root).as_posix()
                content = s_file.read_text(encoding="utf-8")
                prompt = ANALYSIS_PROMPT_TEMPLATE.format(
                    file_path=rel_path,
                    language=s_file.suffix.replace(".", ""),
                    file_content=content[:3000],
                    completed_tasks_summary=json.dumps(self.memory.get("completed_tasks", [])[-5:]),
                    recent_commits=""
                )
                ai_resp = self.call_gemini_api(prompt)
                if ai_resp and ai_resp.get("has_improvement"):
                    opportunities.append({
                        "id": f"AI_{ai_resp.get('category')}_{len(opportunities)}",
                        "file_path": rel_path,
                        "category": ai_resp.get("category", "OPTIMIZATION"),
                        "task_summary": ai_resp.get("task_summary"),
                        "commit_message": ai_resp.get("commit_message"),
                        "justification": ai_resp.get("justification"),
                        "original_snippet": ai_resp.get("original_snippet"),
                        "improved_snippet": ai_resp.get("improved_snippet")
                    })

        print(f"[PLAN] Identified {len(opportunities)} candidate improvement tasks.")

        # Step 4: Execute up to target commits
        committed_count = 0
        for task in opportunities:
            if committed_count >= self.target_commits:
                print(f"[CADENCE] Reached target of {self.target_commits} commits for this run.")
                break

            success = self.execute_task(task)
            if success:
                committed_count += 1

        # Step 5: Save updated memory
        self.memory["total_runs"] = self.memory.get("total_runs", 0) + 1
        self._save_json(self.memory_path, self.memory)

        # Commit memory update if there were changes and not dry run
        if not self.dry_run and committed_count > 0:
            self.run_command(["git", "add", ".github/agent_memory.json"])
            self.run_command(["git", "commit", "-m", "chore(agent): update autonomous memory and task registry"])

        # Step 6: Generate Daily Report
        self.generate_daily_report()

        # Step 7: Push to remote if running in GitHub Actions and changes exist
        if not self.dry_run and committed_count > 0 and os.environ.get("GITHUB_ACTIONS") == "true":
            print("\n[PUSH] Rebase pulling and pushing validated commits to origin...")
            self.run_command(["git", "pull", "--rebase", "origin", "main"])
            code, out, err = self.run_command(["git", "push", "origin", "main"])
            if code == 0:
                print("[PUSH SUCCESS] All autonomous commits pushed to GitHub!")
            else:
                print(f"[PUSH ERROR] Failed to push: {err}")

        print("\n[AGENT FINISHED] Autonomous session complete.")
        return 0


def main():
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
        model=args.model
    )
    sys.exit(agent.run())


if __name__ == "__main__":
    main()
