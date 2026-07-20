import os
import sys

# Get absolute path of backend directory
backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Under Vercel environment, /var/task is the root.
# To make 'backend' importable as a package and ensure relative imports work correctly,
# we create a symlink /tmp/backend pointing to the backend root directory.
if os.environ.get("VERCEL") == "1":
    tmp_backend = "/tmp/backend"
    if not os.path.exists(tmp_backend):
        try:
            os.symlink(backend_root, tmp_backend)
        except Exception as e:
            # Fallback if symlink fails
            print(f"Symlink failed: {e}")
            
    # Add /tmp to sys.path so 'backend' package is importable
    if "/tmp" not in sys.path:
        sys.path.insert(0, "/tmp")
else:
    # Local environment fallback
    parent_dir = os.path.dirname(backend_root)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)

# Import the application from backend package
from backend.main import app
