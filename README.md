# DevPulse - 24/7 Autonomous AI Contribution Agent & Cloud Operations

[![Autonomous AI Agent](https://github.com/actions/workflows/autonomous-dev-agent.yml/badge.svg)](https://github.com)
[![CI Tests](https://github.com/actions/workflows/ci.yml/badge.svg)](https://github.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![WCAG 2.1 AA](https://img.shields.io/badge/Accessibility-WCAG%202.1%20AA-success)](https://www.w3.org/WAI/WCAG21/quickref/)

**DevPulse** is a modern, responsive cloud operations and task matrix platform featuring a built-in **24/7 Autonomous AI GitHub Contribution Agent**.

The autonomous agent runs entirely in GitHub's cloud infrastructure via GitHub Actions. **It continues inspecting, optimizing, bug-fixing, and creating meaningful daily commits even when your laptop is turned OFF and Antigravity is closed.**

---

## 🌟 Key Architecture & Capabilities

```
                  +----------------------------------------------+
                  |         GitHub Actions Cloud Runner          |
                  |     (Runs 24/7 even with Laptop OFF)         |
                  +----------------------------------------------+
                                         |
                                (Scheduled Cron)
                                         v
                         +-------------------------------+
                         |   Autonomous Agent Engine     |
                         |  (.github/agent/agent.py)     |
                         +-------------------------------+
                                 |               |
             +-------------------+               +-------------------+
             v                                                       v
  +--------------------+                                   +--------------------+
  | Gemini 2.5/2.0 API |                                   | Heuristic Engine   |
  | (AI Code Analysis) |                                   | (WCAG & Fallbacks) |
  +--------------------+                                   +--------------------+
             |                                                       |
             +-------------------+               +-------------------+
                                 |               |
                                 v               v
                         +-------------------------------+
                         | Pre-Commit Test Suite Runner  |
                         | (All 13 Unit Tests Passing)   |
                         +-------------------------------+
                                         |
                       [Passes]          |          [Fails]
               +-------------------------+-------------------------+
               v                                                   v
    +----------------------+                             +--------------------+
    | Create Validated Git |                             | Immediate Rollback |
    |  Atomic Commit (1-4) |                             | (Project Safe)     |
    +----------------------+                             +--------------------+
               |
               v
    +----------------------+
    | Safe Git Push & Push |
    | Daily Activity Log   |
    +----------------------+
```

### 1. Cloud-Native & Autonomous
- **Zero local dependency**: Runs on GitHub Actions `ubuntu-latest` runners.
- **Daily schedule**: Triggered by cron (`0 2 * * *` at 02:00 UTC daily) or on-demand via `workflow_dispatch`.
- **Automatic rebase**: Automatically pulls latest changes before running to prevent merge conflicts.

### 2. Meaningful Daily Commit Target
- **Target**: 4 meaningful, verified commits per day (configurable up to 10).
- **Strict Anti-Spam Guarantee**: Zero fake commits, zero empty commits, zero whitespace-only commits.
- **Full Validation**: Every commit is verified against test suites, linters, and syntax checks before being staged.

### 3. Comprehensive Task Domains
The agent independently inspects and addresses:
- **Responsive Layout & CSS**: Mobile breakpoints, touch targets (min 44px), overflow prevention, layout flex/grid fixes.
- **Accessibility (a11y)**: Screen reader states (`aria-expanded`, `aria-label`, `aria-live`), semantic HTML, focus rings.
- **Error Handling**: Network timeout handling, exponential backoff retries, safe DOM element creation, defensive null checks.
- **UI & Component Polish**: Loading state shimmer animations, button hover/focus transitions, responsive modals.
- **Performance & Code Optimization**: DOM caching, search input debouncing, dead code cleanup.
- **Test Suite Expansion**: Automated regression tests for new features and accessibility rules.

### 4. Strict Project Safeguards
- **Protected directories**: Blacklists `.env*`, `.git/`, secrets, passwords, and workflow credentials.
- **Automatic rollback**: If an improvement fails tests, the agent immediately restores the original file.
- **Safety backup branch**: Creates a local `backup/agent-<timestamp>` branch before any code modification.
- **Non-destructive**: Never wipes existing designs, CSS themes, or business logic.

---

## 🚀 Quick Start Guide

### Step 1: Run the Application Locally
```bash
# Start the backend server & frontend (port 8000)
python src/backend/server.py

# Or run test suites
python -m unittest discover tests -v
```

### Step 2: Test the Autonomous Agent Locally (Dry Run)
```bash
# Run agent in dry-run mode (verifies analysis & tests without committing)
python .github/agent/autonomous_agent.py --dry-run
```

---

## ⚙️ How to Activate 24/7 Cloud Execution

For full instructions, read [SETUP_GUIDE.md](file:///c:/Users/VICTUS/Desktop/ai%20automation/SETUP_GUIDE.md).

1. Push this repository to GitHub.
2. In GitHub repository **Settings -> Secrets and variables -> Actions**, add:
   - `GEMINI_API_KEY`: Your free Gemini API key from [Google AI Studio](https://aistudio.google.com/).
3. In **Settings -> Actions -> General -> Workflow permissions**, enable:
   - **Read and write permissions**.
4. That's it! The agent will run every single day at 02:00 UTC and push 4 meaningful commits.
