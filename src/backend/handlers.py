"""
DevPulse Backend Route Handlers & Business Logic
"""

import json
from typing import Dict, Any, List, Tuple
from src.backend.models import TaskModel, SystemMetrics

# In-memory storage with initial bootstrap records
_TASKS_STORE: List[TaskModel] = [
    TaskModel(
        id="task-101",
        title="Enhance responsive typography and mobile breakpoint layout",
        category="RESPONSIVE_CSS",
        priority="HIGH",
        status="DONE",
        target_file="src/frontend/css/responsive.css"
    ),
    TaskModel(
        id="task-102",
        title="Audit and insert missing aria-labels on interactive icon buttons",
        category="ACCESSIBILITY",
        priority="HIGH",
        status="DONE",
        target_file="src/frontend/index.html"
    ),
    TaskModel(
        id="task-103",
        title="Add try-catch timeout guards for API calls with offline fallback",
        category="ERROR_HANDLING",
        priority="MEDIUM",
        status="IN_PROGRESS",
        target_file="src/frontend/js/api.js"
    ),
    TaskModel(
        id="task-104",
        title="Optimize DOM updates and event delegation in task board",
        category="OPTIMIZATION",
        priority="LOW",
        status="TODO",
        target_file="src/frontend/js/components/taskBoard.js"
    )
]

_METRICS_STORE = SystemMetrics()


def get_all_tasks() -> Tuple[int, Dict[str, Any]]:
    return 200, [t.to_dict() for t in _TASKS_STORE]


def create_task(payload: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
    title = payload.get("title", "").strip()
    if not title or len(title) < 5:
        return 400, {"error": "Task title must be at least 5 characters long"}

    category = payload.get("category", "RESPONSIVE_CSS")
    priority = payload.get("priority", "MEDIUM")
    target_file = payload.get("targetFile")

    new_task = TaskModel(
        id=f"task-{len(_TASKS_STORE) + 101}",
        title=title,
        category=category,
        priority=priority,
        status="TODO",
        target_file=target_file
    )
    _TASKS_STORE.append(new_task)
    return 201, new_task.to_dict()


def get_system_metrics() -> Tuple[int, Dict[str, Any]]:
    return 200, _METRICS_STORE.to_dict()
