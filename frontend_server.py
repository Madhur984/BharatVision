#!/usr/bin/env python3
"""Simple HTTP Server for serving the HTML frontend"""

from http.server import HTTPServer, SimpleHTTPRequestHandler
import os
import sys

PORT = 8080
SERVE_DIR = os.path.join(os.path.dirname(__file__), 'frontend', 'public')

class MyHTTPRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=SERVE_DIR, **kwargs)
    
    def end_headers(self):
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

if __name__ == '__main__':
    os.chdir(SERVE_DIR)
    server = HTTPServer(('0.0.0.0', PORT), MyHTTPRequestHandler)
    print(f"✅ Frontend Server running on http://localhost:{PORT}")
    print(f"   Serving from: {SERVE_DIR}")
    print("   Press Ctrl+C to stop")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n✋ Server stopped")
        server.server_close()
