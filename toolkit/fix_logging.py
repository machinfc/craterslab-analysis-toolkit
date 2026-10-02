from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Mapping, Sequence

from toolkit.paths import OUTPUT_DIR, ensure_directory

LOG_DIR = ensure_directory(OUTPUT_DIR / "fix_logs")
DEFAULT_LOG_PATH = LOG_DIR / "fix_history.txt"


def _format_mapping(mapping: Mapping[str, object]) -> list[str]:
    lines: list[str] = []
    for key, value in mapping.items():
        lines.append(f"- {key}: {value}")
    return lines



def append_fix_log(
    *,
    script_name: str,
    dataset: str,
    filename: str,
    parameters: Mapping[str, object],
    observables: Mapping[str, object],
    output_path: str | Path,
    log_path: str | Path = DEFAULT_LOG_PATH,
    notes: Sequence[str] | None = None,
) -> Path:
    path = Path(log_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().isoformat(timespec="seconds")

    lines = [
        "=" * 80,
        f"Timestamp: {timestamp}",
        f"Script: {script_name}",
        f"Dataset: {dataset}",
        f"Filename: {filename}",
        f"CSV Output: {output_path}",
        "Parameters:",
        *_format_mapping(parameters),
        "Observables:",
        *_format_mapping(observables),
    ]
    if notes:
        lines.append("Notes:")
        lines.extend(f"- {note}" for note in notes)
    lines.append("")

    with path.open("a", encoding="utf-8") as logfile:
        logfile.write("\n".join(lines) + "\n")

    return path
