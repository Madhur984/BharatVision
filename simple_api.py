import uvicorn
import os
import sys

# Ensure backend directory is in python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

if __name__ == "__main__":
    # Import the new modular app
    # Note: uvicorn needs the import string format for reload to work, 
    # but for simple run we can pass the app object.
    from backend.app.main import app
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
