#!/usr/bin/env python3
"""
Launcher script for Legal Metrology OCR Pipeline Web Interface

This script provides a convenient way to launch the web interface from the project root.
It simply redirects to the proper web application startup script.
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """Launch the web interface from the project root"""
    
    # Get project root and web directory
    project_root = Path(__file__).parent
    web_dir = project_root / "web"
    
    # Check if web directory exists
    if not web_dir.exists():
        print("❌ Error: Web directory not found!")
        print(f"Expected location: {web_dir}")
        sys.exit(1)
    
    # Check if the web app script exists
    web_app_script = web_dir / "run_app.py"
    if not web_app_script.exists():
        print("❌ Error: Web application script not found!")
        print(f"Expected location: {web_app_script}")
        sys.exit(1)
    
    print("🚀 Launching Legal Metrology OCR Pipeline Web Interface...")
    print(f"📁 Redirecting to: {web_dir}")
    print("-" * 60)
    
    # Change to web directory and run the app
    try:
        os.chdir(web_dir)
        subprocess.run([sys.executable, "run_app.py"], check=True)
    except KeyboardInterrupt:
        print("\n👋 Web interface stopped.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error launching web interface: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()