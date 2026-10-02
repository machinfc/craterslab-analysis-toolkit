from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TARGET = PROJECT_ROOT / "scripts" / "fixes" / "ellipse_fixer.py"


def main() -> None:
    print("[INFO] lroc_fixer.py is kept as a compatibility wrapper.")
    print("[INFO] Please use scripts/fixes/ellipse_fixer.py for the unified fixer workflow.")
    command = [sys.executable, str(TARGET)]
    if len(sys.argv) > 1:
        command.extend(["--dataset", "quickmap", *sys.argv[1:]])
    raise SystemExit(subprocess.run(command, check=False).returncode)


if __name__ == "__main__":
    main()
