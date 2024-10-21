import sys
import importlib
from pathlib import Path

root = Path(__file__).parent
sys.path.append(str(root))

# Loop through all files in the directory
for p in root.rglob("*.py"):
    if p != root / "__init__.py":
        p = str(p.relative_to(root))
        print(p)
        module_name = p[:-3].replace("/", ".")  # Remove the .py extension
        m = importlib.import_module(f"{module_name}", package=__name__)
        globals().update(vars(m))
