#!/usr/bin/env python
"""
Starter script for React.py + Flask backend
Launches both servers for the Legal Metrology OCR Pipeline
"""

import subprocess
import sys
import time
import os
from pathlib import Path

def start_flask_api():
    """Start Flask API server"""
    print("\n" + "="*60)
    print("Starting Flask API Server...")
    print("="*60)
    
    flask_script = Path(__file__).parent / "backend" / "flask_api.py"
    
    proc = subprocess.Popen(
        [sys.executable, str(flask_script)],
        cwd=Path(__file__).parent,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    return proc

def start_react_app():
    """Start React.py application"""
    print("\n" + "="*60)
    print("Starting React.py Application...")
    print("="*60)
    
    react_main = Path(__file__).parent / "react_app" / "main.py"
    
    proc = subprocess.Popen(
        [sys.executable, str(react_main)],
        cwd=Path(__file__).parent,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    return proc

if __name__ == "__main__":
    print("\n🚀 Legal Metrology OCR Pipeline - React.py Frontend")
    print("="*60)
    
    # Start both servers
    print("\n✓ Attempting to start services...")
    
    # Start Flask first
    flask_proc = start_flask_api()
    time.sleep(2)
    
    # Start React.py
    react_proc = start_react_app()
    time.sleep(2)
    
    print("\n" + "="*60)
    print("✓ Services started!")
    print("="*60)
    print("\n📡 Server URLs:")
    print("   • Flask API:  http://localhost:8080")
    print("   • React.py:   http://localhost:3000")
    print("\n💡 Press Ctrl+C to stop all services")
    print("="*60 + "\n")
    
    try:
        # Keep servers running
        flask_proc.wait()
        react_proc.wait()
    except KeyboardInterrupt:
        print("\n\n⛔ Shutting down...")
        flask_proc.terminate()
        react_proc.terminate()
        flask_proc.wait(timeout=5)
        react_proc.wait(timeout=5)
        print("✓ Shutdown complete\n")
