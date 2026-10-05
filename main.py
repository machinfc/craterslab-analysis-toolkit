from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from toolkit.interactive import ask_choice, ask_yes_no

PROJECT_ROOT = Path(__file__).resolve().parent

TOOLS = {
    "analyze": {
        "label": "Analyze crater data",
        "script": PROJECT_ROOT / "scripts" / "analysis" / "data_analyzer.py",
    },
    "visualize": {
        "label": "Review crater data visually",
        "script": PROJECT_ROOT
        / "scripts"
        / "visualization"
        / "depth_map_visualizer.py",
    },
    "fix": {
        "label": "Fix crater geometry / classification",
        "script": PROJECT_ROOT / "scripts" / "fixes" / "ellipse_fixer.py",
    },
    "fetch": {
        "label": "Capture a depth map from Kinect or Femto Bolt",
        "script": PROJECT_ROOT / "scripts" / "acquisition" / "depth_map_fetcher.py",
    },
    "diagnose": {
        "label": "Check environment compatibility",
        "script": PROJECT_ROOT / "scripts" / "diagnostics" / "check_craterslab_env.py",
    },
    "train": {
        "label": "Train classifier",
        "script": PROJECT_ROOT / "scripts" / "training" / "train_classifier_2_0.py",
    },
    "slopes": {
        "label": "Calculate slopes",
        "script": PROJECT_ROOT / "scripts" / "analysis" / "slope_calculator.py",
    },
}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Central launcher for the Craterslab Analysis Toolkit."
    )
    parser.add_argument(
        "tool",
        nargs="?",
        choices=[*TOOLS, "menu"],
        default="menu",
        help="Tool to launch directly. Leave empty to open the menu.",
    )
    parser.add_argument(
        "tool_args",
        nargs=argparse.REMAINDER,
        help="Extra arguments forwarded to the tool.",
    )
    return parser.parse_args(argv)


def launch_tool(tool_key: str, extra_args: list[str] | None = None) -> int:
    tool = TOOLS[tool_key]
    command = [sys.executable, str(tool["script"]), *(extra_args or [])]
    print(f"\nRunning: {tool['label']}")
    print(f"Command: {' '.join(command)}")
    return subprocess.run(command, check=False).returncode


def interactive_menu() -> None:
    print("=" * 72)
    print("CRATERSLAB ANALYSIS TOOLKIT")
    print("Choose a workflow.")
    print("=" * 72)

    while True:
        selection = ask_choice(
            "Main menu",
            {key: tool["label"] for key, tool in TOOLS.items()} | {"exit": "Exit"},
            default="analyze",
        )
        if selection == "exit":
            print("Exiting launcher.")
            return

        return_code = launch_tool(selection)
        print(f"Tool finished with exit code: {return_code}")
        if not ask_yes_no("Return to main menu", default=True):
            return


def main() -> None:
    args = parse_args()
    if args.tool == "menu":
        interactive_menu()
        return

    tool_args = list(args.tool_args)
    if tool_args and tool_args[0] == "--":
        tool_args = tool_args[1:]
    raise SystemExit(launch_tool(args.tool, tool_args))


if __name__ == "__main__":
    main()
