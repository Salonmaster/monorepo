import importlib
import os
import sys
from pathlib import Path

package_dir = Path(__file__).resolve().parent
os.chdir(package_dir)
package_str = str(package_dir)
if package_str not in sys.path:
    sys.path.insert(0, package_str)

__all__ = ["core", "enums", "helpers", "models", "commands"]


def __getattr__(name):
    if name in __all__:
        module = importlib.import_module(f".{name}", __name__)
        globals()[name] = module
        return module
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
