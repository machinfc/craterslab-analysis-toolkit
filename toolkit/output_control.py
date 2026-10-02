from __future__ import annotations

from pathlib import Path


def build_analysis_output_path(
    output_dir: Path,
    dataset: str,
    label: str,
    filename: str | None = None,
    start: int | None = None,
    end: int | None = None,
    prefix: str | None = None,
) -> Path:
    if filename is not None:
        stem = Path(filename).stem
        return output_dir / f"{stem}_{label}.csv"

    if start is not None and end is not None:
        range_part = f"_{start}_{end}"
    else:
        range_part = ""

    prefix_part = f"_{prefix}" if prefix and prefix != dataset else ""
    return output_dir / f"{dataset}{prefix_part}_{label}{range_part}.csv"



def next_available_path(path: Path) -> Path:
    candidate = path
    index = 1
    while candidate.exists():
        candidate = path.with_name(f"{path.stem}_{index}{path.suffix}")
        index += 1
    return candidate



def resolve_output_path(path: Path, overwrite: bool = False, prompt_user: bool = True) -> Path:
    if not path.exists() or overwrite:
        return path

    if prompt_user:
        answer = input(f"Output file already exists: {path}\nOverwrite it? [y/N]: ").strip().lower()
        if answer in {"y", "yes", "s", "si", "sí"}:
            return path

    new_path = next_available_path(path)
    print(f"Using a new output path instead of overwriting: {new_path}")
    return new_path
