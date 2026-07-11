from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def open_with_default_app(path: Path) -> bool:
    path = Path(path)
    try:
        if sys.platform == "win32":
            os.startfile(str(path))
        else:
            subprocess.run(["xdg-open", str(path)], check=False)
        return True
    except OSError:
        return False


def open_in_file_explorer(path: Path) -> bool:
    path = Path(path)
    target = path if path.is_dir() else path.parent
    try:
        if sys.platform == "win32":
            subprocess.run(["explorer", str(target)], check=False)
        else:
            subprocess.run(["xdg-open", str(target)], check=False)
        return True
    except OSError:
        return False
