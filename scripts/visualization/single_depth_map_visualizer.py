from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TARGET = PROJECT_ROOT / "scripts" / "visualization" / "depth_map_visualizer.py"


def main() -> None:
    print("[INFO] single_depth_map_visualizer.py is kept as a compatibility wrapper.")
    print("[INFO] Please use scripts/visualization/depth_map_visualizer.py for the unified visual review workflow.")
    command = [sys.executable, str(TARGET)]
    if len(sys.argv) > 1:
        command.extend(["--mode", "single", *sys.argv[1:]])
    raise SystemExit(subprocess.run(command, check=False).returncode)


if __name__ == "__main__":
    main()
