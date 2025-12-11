#!/usr/bin/env python3
"""
Startup script for the Legal Metrology OCR Pipeline Web Interface

This script launches the Streamlit web application from the correct directory
with the proper Python path configuration.
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """Launch the Streamlit web application"""
    
    # Get the web directory (where this script is located)
    web_dir = Path(__file__).parent
    
    # Get the project root (parent of web directory)
    project_root = web_dir.parent
    
    # Change to the web directory
    os.chdir(web_dir)
    
    # Add project root to Python path
    env = os.environ.copy()
    if 'PYTHONPATH' in env:
        env['PYTHONPATH'] = f"{project_root}{os.pathsep}{env['PYTHONPATH']}"
    else:
        env['PYTHONPATH'] = str(project_root)
    
    print("🚀 Starting Legal Metrology OCR Pipeline Web Interface...")
    print(f"📁 Web Directory: {web_dir}")
    print(f"📁 Project Root: {project_root}")
    print(f"🐍 Python Path: {env.get('PYTHONPATH', 'Not set')}")
    print("-" * 60)
    
    # Launch Streamlit
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "streamlit_app.py",
            "--server.headless", "false",
            "--server.runOnSave", "true",
            "--browser.gatherUsageStats", "false"
        ], env=env, check=True)
    except KeyboardInterrupt:
        print("\n👋 Shutting down web interface...")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error launching Streamlit: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
