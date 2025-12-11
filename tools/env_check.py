import importlib, sys
import importlib.util as importlib_util
print('Python', sys.version)

def check(pkg):
    # Support environments where importlib.util may not be available at top-level
    try:
        spec = importlib_util.find_spec(pkg)
    except Exception:
        spec = importlib.find_spec(pkg)
    return spec is not None

pkgs = ['selenium','webdriver_manager','ultralytics','torch']
for p in pkgs:
    print(p, 'installed' if check(p) else 'missing')

# webdriver-manager import check
try:
    from webdriver_manager.chrome import ChromeDriverManager
    print('webdriver-manager import: OK')
except Exception as e:
    print('webdriver-manager import failed:', e)

# selenium import/version
try:
    import selenium
    print('selenium version:', getattr(selenium, '__version__', 'unknown'))
except Exception as e:
    print('selenium import failed:', e)

# ultralytics import/version
try:
    import ultralytics
    print('ultralytics version:', getattr(ultralytics, '__version__', 'unknown'))
except Exception as e:
    print('ultralytics import failed:', e)

# torch import/version
try:
    import torch
    print('torch version:', torch.__version__, 'cuda_available=', torch.cuda.is_available())
except Exception as e:
    print('torch import failed:', e)

# Attempt to install chromedriver via webdriver-manager if available
try:
    from webdriver_manager.chrome import ChromeDriverManager
    print('Attempting to download chromedriver (may take a few seconds)...')
    path = ChromeDriverManager().install()
    print('ChromeDriver installed at', path)
except Exception as e:
    print('ChromeDriver installation failed or skipped:', e)

# Attempt to instantiate YOLO model if possible (this may download weights)
try:
    from importlib import util
    if util.find_spec('ultralytics') and util.find_spec('torch'):
        from ultralytics import YOLO
        print('Attempting to load YOLO model yolov8n.pt (may download weights)...')
        model = YOLO('yolov8n.pt')
        print('YOLO model object created:', type(model))
    else:
        print('Skipping YOLO model load: ultralytics or torch missing')
except Exception as e:
    print('YOLO model load failed:', e)
