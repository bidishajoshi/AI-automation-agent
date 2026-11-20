"""
DevPulse Backend Data Models
"""

from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any


@dataclass
class TaskModel:
    id: str
    title: str
    category: str
    priority: str
    status: str = "TODO"
    target_file: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "category": self.category,
            "priority": self.priority,
            "status": self.status,
            "targetFile": self.target_file,
            "createdAt": self.created_at,
            "updatedAt": self.updated_at
        }


@dataclass
class SystemMetrics:
    health: int = 100
    commits: int = 4
    target: int = 4
    a11y_score: int = 98
    latency_ms: int = 18

    def to_dict(self) -> Dict[str, Any]:
        return {
            "health": self.health,
            "commits": self.commits,
            "target": self.target,
            "a11yScore": self.a11y_score,
            "latencyMs": self.latency_ms
        }
