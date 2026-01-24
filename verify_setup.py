import sys
import os

print(f"Python: {sys.version}")

try:
    import PySide6
    print("PySide6 imported successfully")
except ImportError as e:
    print(f"Failed to import PySide6: {e}")

try:
    import cjio
    print(f"cjio imported successfully (v{cjio.__version__})")
except ImportError as e:
    print(f"Failed to import cjio: {e}")

try:
    import trimesh
    print("trimesh imported successfully")
except ImportError as e:
    print(f"Failed to import trimesh: {e}")

# Check local app import
try:
    sys.path.append(os.getcwd())
    from app.processor import CityGMLProcessor
    proc = CityGMLProcessor()
    print("CityGMLProcessor instantiated successfully")
except ImportError as e:
    print(f"Failed to import app.processor: {e}")
except Exception as e:
    print(f"Failed to instantiate CityGMLProcessor: {e}")

print("Verification Complete")
