"""
Backend API Unit Tests
"""

import unittest
from src.backend.models import TaskModel, SystemMetrics
from src.backend.handlers import get_all_tasks, create_task, get_system_metrics, get_commit_history


class TestBackendApi(unittest.TestCase):
    def test_get_all_tasks(self):
        status, tasks = get_all_tasks()
        self.assertEqual(status, 200)
        self.assertIsInstance(tasks, list)
        self.assertGreaterEqual(len(tasks), 1)
        self.assertIn("title", tasks[0])

    def test_get_all_tasks_with_status_filter(self):
        status, done_tasks = get_all_tasks(status_filter="DONE")
        self.assertEqual(status, 200)
        self.assertIsInstance(done_tasks, list)
        for task in done_tasks:
            self.assertEqual(task["status"], "DONE")

    def test_create_task_success(self):
        payload = {
            "title": "Add test coverage for responsive navigation",
            "category": "RESPONSIVE_CSS",
            "priority": "HIGH"
        }
        status, data = create_task(payload)
        self.assertEqual(status, 201)
        self.assertEqual(data["title"], payload["title"])
        self.assertEqual(data["status"], "TODO")

    def test_create_task_validation_failure(self):
        # Title too short
        payload = {"title": "abc"}
        status, data = create_task(payload)
        self.assertEqual(status, 400)
        self.assertIn("error", data)

    def test_get_system_metrics(self):
        status, metrics = get_system_metrics()
        self.assertEqual(status, 200)
        self.assertIn("health", metrics)
        self.assertEqual(metrics["health"], 100)

    def test_get_commit_history(self):
        status, history = get_commit_history()
        self.assertEqual(status, 200)
        self.assertIsInstance(history, list)
        self.assertGreaterEqual(len(history), 1)
        self.assertIn("commitHash", history[0])


if __name__ == "__main__":
    unittest.main()
