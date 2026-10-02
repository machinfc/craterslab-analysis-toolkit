from __future__ import annotations

from datetime import datetime
from pathlib import Path
import traceback

from toolkit.interactive import ask_choice
from toolkit.paths import OUTPUT_DIR, ensure_directory

ERROR_LOG_DIR = ensure_directory(OUTPUT_DIR / "error_logs")
DEFAULT_ERROR_LOG = ERROR_LOG_DIR / "error_history.txt"


def format_exception_text(exception: Exception) -> str:
    return "".join(traceback.format_exception(type(exception), exception, exception.__traceback__))



def print_processing_error(workflow: str, filename: str, exception: Exception) -> None:
    print("\n" + "!" * 80)
    print(f"Error in {workflow}")
    print(f"File: {filename}")
    print(f"Type: {type(exception).__name__}")
    print(f"Message: {exception}")
    print("!" * 80)



def append_error_log(
    *,
    workflow: str,
    dataset: str,
    filename: str,
    exception: Exception,
    log_path: str | Path = DEFAULT_ERROR_LOG,
) -> Path:
    path = Path(log_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().isoformat(timespec="seconds")
    trace = format_exception_text(exception)

    lines = [
        "=" * 80,
        f"Timestamp: {timestamp}",
        f"Workflow: {workflow}",
        f"Dataset: {dataset}",
        f"Filename: {filename}",
        f"Exception: {type(exception).__name__}",
        f"Message: {exception}",
        "Traceback:",
        trace,
        "",
    ]
    with path.open("a", encoding="utf-8") as logfile:
        logfile.write("\n".join(lines) + "\n")
    return path



def ask_error_action(
    *,
    allow_fix: bool = False,
    allow_edit: bool = False,
    allow_skip: bool = True,
    allow_stop: bool = True,
    default: str = "retry",
) -> str:
    options = {"retry": "Retry this file", "details": "Show full traceback"}
    if allow_edit:
        options["edit"] = "Edit parameters and retry"
    if allow_fix:
        options["fix"] = "Open the fixer for this file"
    if allow_skip:
        options["skip"] = "Skip this file and continue"
    if allow_stop:
        options["stop"] = "Stop the current batch"
    return ask_choice("How do you want to handle this error", options, default=default)
