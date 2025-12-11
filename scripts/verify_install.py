#!/usr/bin/env python3
"""Quick verification script to test critical imports after installing requirements."""
import importlib
import sys

packages = [
    ("torch", "torch"),
    ("cv2", "cv2"),
    ("pytesseract", "pytesseract"),
    ("numpy", "numpy"),
    # Surya OCR may be optional on some platforms. This check will tell
    # you whether Surya was installed successfully in the current env.
    ("surya", "surya"),
]

def try_import(name):
    try:
        mod = importlib.import_module(name)
        version = getattr(mod, "__version__", "(no __version__)")
        print(f"OK: {name} imported, version: {version}")
        return True
    except Exception as e:
        print(f"FAIL: importing {name}: {e}")
        return False

def main():
    print(f"Python: {sys.version.splitlines()[0]}")
    all_ok = True
    for pkg_name, import_name in packages:
        ok = try_import(import_name)
        all_ok = all_ok and ok

    if all_ok:
        print("All checks passed.")
        sys.exit(0)
    else:
        print("Some imports failed. See messages above.")
        sys.exit(2)

if __name__ == '__main__':
    main()
