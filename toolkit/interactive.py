from __future__ import annotations

from pathlib import Path
from typing import Iterable

from toolkit.paths import DATASET_INFO, normalize_dataset_name


def safe_input(prompt: str) -> str:
    try:
        return input(prompt)
    except KeyboardInterrupt:
        print("\nCancelled by user.")
        raise SystemExit(130)
    except EOFError:
        print("\nInput closed. Exiting.")
        raise SystemExit(1)


def ask_text(prompt: str, default: str | None = None, allow_empty: bool = False) -> str:
    while True:
        suffix = f" [{default}]" if default is not None else ""
        value = safe_input(f"{prompt}{suffix}: ").strip()
        if value:
            return value
        if default is not None:
            return default
        if allow_empty:
            return ""
        print("Please enter a value.")


def ask_int(prompt: str, default: int | None = None) -> int:
    while True:
        raw = ask_text(prompt, str(default) if default is not None else None)
        try:
            return int(raw)
        except ValueError:
            print("Please enter an integer.")


def ask_float(prompt: str, default: float | None = None) -> float:
    while True:
        raw = ask_text(prompt, str(default) if default is not None else None)
        try:
            return float(raw)
        except ValueError:
            print("Please enter a number.")


def ask_yes_no(prompt: str, default: bool = False) -> bool:
    default_label = "Y/n" if default else "y/N"
    while True:
        value = safe_input(f"{prompt} [{default_label}]: ").strip().lower()
        if not value:
            return default
        if value in {"y", "yes", "s", "si", "sí"}:
            return True
        if value in {"n", "no"}:
            return False
        print("Please answer yes or no.")


def ask_choice(prompt: str, options: dict[str, str], default: str | None = None) -> str:
    keys = list(options)
    print(f"\n{prompt}")
    for index, key in enumerate(keys, start=1):
        marker = " (default)" if default == key else ""
        print(f"  {index}. {options[key]}{marker}")

    while True:
        raw = safe_input("Option: ").strip().lower()
        if not raw and default is not None:
            return default
        if raw.isdigit():
            idx = int(raw) - 1
            if 0 <= idx < len(keys):
                return keys[idx]
        if raw in options:
            return raw
        print("Please choose one of the listed options.")


def ask_dataset(default: str = "fluized") -> str:
    options = {
        key: f"{info['label']} ({info['file_type']})"
        for key, info in DATASET_INFO.items()
        if key in {"fluized", "compacted", "quickmap"}
    }
    selected = ask_choice("Dataset", options, default=normalize_dataset_name(default))
    return normalize_dataset_name(selected)


def ask_range(default_start: int, default_end: int) -> tuple[int, int]:
    start = ask_int("Start index", default_start)
    end = ask_int("End index", default_end)
    return start, end


def ask_bbox(
    default: tuple[int, int, int, int] | None = None
) -> tuple[int, int, int, int]:
    default_text = ",".join(map(str, default)) if default is not None else None
    while True:
        raw = ask_text("Manual crop (x,y,w,h)", default_text)
        try:
            parts = [int(part.strip()) for part in raw.split(",")]
            if len(parts) != 4:
                raise ValueError
            return tuple(parts)  # type: ignore[return-value]
        except ValueError:
            print("Use four integers separated by commas, for example: 10,50,100,100")


def ask_point(prompt: str, default: tuple[int, int] | None = None) -> tuple[int, int]:
    default_text = ",".join(map(str, default)) if default is not None else None
    while True:
        raw = ask_text(prompt, default_text)
        try:
            parts = [int(part.strip()) for part in raw.split(",")]
            if len(parts) != 2:
                raise ValueError
            return tuple(parts)  # type: ignore[return-value]
        except ValueError:
            print("Use two integers separated by commas, for example: 107,146")


def ask_optional_point(prompt: str) -> tuple[int, int] | None:
    raw = ask_text(f"{prompt} (leave empty to skip)", allow_empty=True)
    if not raw:
        return None
    try:
        parts = [int(part.strip()) for part in raw.split(",")]
        if len(parts) != 2:
            raise ValueError
        return tuple(parts)  # type: ignore[return-value]
    except ValueError:
        print("Invalid point. Skipping manual point.")
        return None


def ask_file_mode(default: str = "all") -> str:
    return ask_choice(
        "What do you want to process",
        {
            "all": "All files",
            "single": "One file",
            "range": "A numeric range",
        },
        default=default,
    )


def ask_plot_mode(default: str = "none") -> str:
    return ask_choice(
        "Visualization",
        {
            "none": "No plots",
            "2d": "2D only",
            "3d": "3D only",
            "both": "2D and 3D",
        },
        default=default,
    )


def ask_visualizer_mode(default: str = "all") -> str:
    return ask_choice(
        "What do you want to show",
        {
            "2d": "2D only",
            "3d": "3D only",
            "profile": "Profile only",
            "2d_profile": "2D and profile",
            "3d_profile": "3D and profile",
            "all": "2D, profile, and 3D",
        },
        default=default,
    )


def plot_flags_from_mode(plot_mode: str) -> tuple[bool, bool]:
    normalized = plot_mode.lower()
    return normalized in {"2d", "both"}, normalized in {"3d", "both"}


def visualization_flags_from_mode(mode: str) -> tuple[bool, bool, bool]:
    normalized = mode.lower()
    show_2d = normalized in {"2d", "2d_profile", "all"}
    show_3d = normalized in {"3d", "3d_profile", "all"}
    show_profile = normalized in {"profile", "2d_profile", "3d_profile", "all"}
    return show_2d, show_profile, show_3d


def choose_filename_from_directory(directory: Path, extensions: Iterable[str]) -> str:
    allowed = {ext.lower() for ext in extensions}
    candidates = sorted(
        path.name
        for path in directory.iterdir()
        if path.is_file() and path.suffix.lower() in allowed
    )
    if not candidates:
        raise FileNotFoundError(f"No matching files found in {directory}")

    options = {str(index): name for index, name in enumerate(candidates, start=1)}
    print("\nAvailable files:")
    for index, name in options.items():
        print(f"  {index}. {name}")

    while True:
        raw = safe_input("File number or exact name: ").strip()
        if raw in options:
            return options[raw]
        if raw in candidates:
            return raw
        print("Please choose one of the listed files.")
