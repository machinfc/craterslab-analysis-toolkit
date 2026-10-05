from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TARGET = PROJECT_ROOT / "scripts" / "analysis" / "data_analyzer.py"


def main() -> None:
    print("[INFO] lroc_analyzer.py is kept as a compatibility wrapper.")
    print(
        "[INFO] Please use scripts/analysis/data_analyzer.py for the unified analyzer workflow."
    )
    command = [sys.executable, str(TARGET)]
    if len(sys.argv) > 1:
        command.extend(["--dataset", "quickmap", *sys.argv[1:]])
    raise SystemExit(subprocess.run(command, check=False).returncode)


if __name__ == "__main__":
    main()
