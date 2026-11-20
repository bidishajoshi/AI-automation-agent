"""
DevPulse Standalone HTTP Server
Serves static frontend files and exposes JSON REST endpoints.
Uses standard Python library (http.server) for zero external dependencies.
"""

import json
import os
import sys
from http.server import SimpleHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

from src.backend.handlers import get_all_tasks, create_task, get_system_metrics

PORT = int(os.environ.get("PORT", 8000))
FRONTEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend"))


class DevPulseHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=FRONTEND_DIR, **kwargs)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/tasks":
            status, data = get_all_tasks()
            self._send_json(status, data)
        elif parsed.path == "/api/metrics":
            status, data = get_system_metrics()
            self._send_json(status, data)
        elif parsed.path == "/api/health":
            self._send_json(200, {"status": "healthy", "service": "DevPulse Backend"})
        else:
            # Fall back to serving static frontend
            super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/tasks":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            try:
                payload = json.loads(body.decode("utf-8"))
            except Exception:
                self._send_json(400, {"error": "Invalid JSON body"})
                return

            status, data = create_task(payload)
            self._send_json(status, data)
        else:
            self._send_json(404, {"error": "Endpoint not found"})

    def _send_json(self, status: int, data: any):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))


def run(port=PORT):
    server = HTTPServer(("0.0.0.0", port), DevPulseHandler)
    print(f"DevPulse running at http://localhost:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
        server.server_close()


if __name__ == "__main__":
    run()
