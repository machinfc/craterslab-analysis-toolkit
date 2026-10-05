from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable, Sequence

DEFAULT_OBS_VAL = -1
META_COLUMNS = ["filename", "type"]


def build_observable_row(
    filename: str,
    surface,
    observables: Sequence[str],
    default_value: float = DEFAULT_OBS_VAL,
) -> list[object]:
    row: list[object] = [filename, str(surface.type)]
    for observable in observables:
        if observable in surface.observables:
            row.append(surface.observables[observable].value)
        else:
            row.append(default_value)
    return row


def write_observables_csv(
    path: Path | str,
    observables: Sequence[str],
    rows: Iterable[Sequence[object]],
) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(META_COLUMNS + list(observables))
        writer.writerows(rows)

    return output_path


def write_profile_csv(path: Path | str, profile) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Distance (s)", "Height (h)"])
        writer.writerows(zip(profile.s, profile.h))

    return output_path
