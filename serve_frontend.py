"""
Simple HTTP Server to serve the BharatVision HTML frontend
Run this to access the professional government website at http://localhost:8001
"""

import http.server
import socketserver
from pathlib import Path
import webbrowser
import threading
import time
import os

PORT = 8001
PUBLIC_DIR = Path(__file__).parent / "frontend" / "public"

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def translate_path(self, path):
        """Serve files from the public directory"""
        if path == "/":
            path = "/index.html"
        return str(PUBLIC_DIR / path.lstrip("/"))
    
    def end_headers(self):
        """Add CORS headers"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

def open_browser():
    """Open browser after server starts"""
    time.sleep(1)
    webbrowser.open(f"http://localhost:{PORT}")
    print(f"\n✓ Browser opened at http://localhost:{PORT}")

if __name__ == "__main__":
    os.chdir(PUBLIC_DIR.parent)  # Change to frontend directory
    
    print("\n" + "="*70)
    print(" "*15 + "BharatVision HTML Frontend Server")
    print("="*70)
    print(f"\n📁 Serving from: {PUBLIC_DIR}")
    print(f"🌐 Access at:    http://localhost:{PORT}")
    print("\nMake sure the FastAPI backend is running at http://localhost:8000")
    print("\nPress Ctrl+C to stop the server\n")
    print("="*70 + "\n")
    
    # Start browser opener thread
    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()
    
    # Start HTTP server
    try:
        with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n✓ Server stopped.")
