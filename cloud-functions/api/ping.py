"""Minimal standard-library health check for EdgeOne Python runtime.

This file uses ONLY the Python standard library — no third-party imports.
If this endpoint works but /api/health does not, the issue is with our
FastAPI dependency chain.  If this ALSO returns 404, EdgeOne is not
processing Python cloud functions at all.
"""

import json
from http.server import BaseHTTPRequestHandler


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps({
            "status": "ok",
            "msg": "EdgeOne Python cloud function is working",
        }).encode("utf-8"))

    def do_POST(self):
        """Echo back whatever was posted — useful for debugging."""
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length else b""
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps({
            "method": "POST",
            "body": body.decode("utf-8", errors="replace"),
            "headers": dict(self.headers),
        }, ensure_ascii=False).encode("utf-8"))
