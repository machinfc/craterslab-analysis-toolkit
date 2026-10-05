from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

from craterslab.ellipse import EllipticalModel
from craterslab.sensors import DepthMap

from toolkit.error_handling import (
    append_error_log,
    ask_error_action,
    format_exception_text,
    print_processing_error,
)
from toolkit.interactive import (
    ask_dataset,
    ask_file_mode,
    ask_int,
    ask_plot_mode,
    ask_range,
    ask_text,
    choose_filename_from_directory,
    plot_flags_from_mode,
)
from toolkit.output_control import build_analysis_output_path, resolve_output_path
from toolkit.paths import (
    OUTPUT_DIR,
    get_dataset_dir,
    get_dataset_info,
    normalize_dataset_name,
)
from toolkit.session_summary import (
    append_session_entry,
    append_session_note,
    ensure_session_summary_path,
)
from toolkit.visualization_helpers import show_review_figures

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Calculate slopes from automatically generated max profiles."
    )
    parser.add_argument(
        "--dataset", default="compacted", choices=["compacted", "fluized"]
    )
    parser.add_argument("--mode", choices=["all", "single", "range"], default="range")
    parser.add_argument("--prefix", default=None)
    parser.add_argument("--start", type=int, default=25)
    parser.add_argument("--end", type=int, default=49)
    parser.add_argument("--filename", default=None)
    parser.add_argument("--ellipse-points", type=int, default=20)
    parser.add_argument("--plot", action="store_true")
    parser.add_argument("--plot2d", action="store_true")
    parser.add_argument("--plot3d", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--skip-missing", action="store_true")
    parser.add_argument("--output", type=Path, default=None)
    return parser.parse_args(argv)


def iter_indices(start: int, end: int):
    step = 1 if end >= start else -1
    return range(start, end + step, step)


def build_interactive_args() -> argparse.Namespace:
    dataset = ask_dataset(default="compacted")
    mode = ask_file_mode(default="range")
    dataset_info = get_dataset_info(dataset)
    prefix = dataset_info["default_prefix"]
    filename = None
    start, end = (25, 49) if dataset == "compacted" else (1, 51)

    if mode == "single":
        filename = choose_filename_from_directory(
            get_dataset_dir(dataset), [f".{dataset_info['file_type']}"]
        )
    elif mode == "range":
        prefix = ask_text("File prefix", prefix)
        start, end = ask_range(start, end)
    else:
        prefix = ask_text("File prefix used to match all files", prefix)

    plot_mode = ask_plot_mode(default="none")
    plot2d, plot3d = plot_flags_from_mode(plot_mode)
    output = Path(
        ask_text(
            "Output CSV path",
            str(
                build_analysis_output_path(
                    OUTPUT_DIR,
                    normalize_dataset_name(dataset),
                    label="slopes",
                    filename=filename,
                    start=None if mode != "range" else start,
                    end=None if mode != "range" else end,
                    prefix=prefix,
                )
            ),
        )
    )

    return argparse.Namespace(
        dataset=dataset,
        mode=mode,
        prefix=prefix,
        start=start,
        end=end,
        filename=filename,
        ellipse_points=ask_int("Ellipse points", 20),
        plot=plot2d or plot3d,
        plot2d=plot2d,
        plot3d=plot3d,
        overwrite=False,
        skip_missing=False,
        output=output,
        interactive=True,
    )


def collect_file_paths(args: argparse.Namespace) -> list[Path]:
    dataset_dir = get_dataset_dir(args.dataset)
    dataset_info = get_dataset_info(args.dataset)
    suffix = f".{dataset_info['file_type']}"
    if args.mode == "single" or args.filename:
        if not args.filename:
            raise ValueError("Single mode requires a file name")
        return [dataset_dir / args.filename]
    prefix = args.prefix or dataset_info["default_prefix"]
    if args.mode == "all":
        return sorted(
            path for path in dataset_dir.glob(f"{prefix}_*{suffix}") if path.is_file()
        )
    return [
        dataset_dir / f"{prefix}_{index}{suffix}"
        for index in iter_indices(args.start, args.end)
    ]


def process_one_file(
    file_path: Path, args: argparse.Namespace
) -> tuple[list[object] | None, bool]:
    while True:
        try:
            if not file_path.exists():
                raise FileNotFoundError(f"Input file not found: {file_path}")

            depth_map = DepthMap.load(file_path)
            depth_map.auto_crop()
            ellipse_model = EllipticalModel(depth_map, args.ellipse_points)
            profile = ellipse_model.max_profile()
            m1, m2 = profile.slopes()
            print(f"Processed {file_path.name}: m1={m1}, m2={m2}")
            append_session_entry(
                workflow="slope calculator",
                dataset=normalize_dataset_name(args.dataset),
                category="analyzed",
                value=file_path.name,
            )

            if (
                getattr(args, "plot2d", False)
                or getattr(args, "plot3d", False)
                or args.plot
            ):
                show_review_figures(
                    depth_map=depth_map,
                    profile=profile,
                    ellipse_model=ellipse_model,
                    surface=None,
                    show_2d=getattr(args, "plot2d", False) or args.plot,
                    show_profile=True,
                    show_3d=getattr(args, "plot3d", False),
                    preview_scale=(1, 1, 4),
                )
            return [file_path.name, m1, m2], True

        except FileNotFoundError as exception:
            if args.skip_missing and not getattr(args, "interactive", False):
                print(f"[WARN] {exception}")
                return None, True
            print_processing_error("slope calculator", file_path.name, exception)
            log_path = append_error_log(
                workflow="slope calculator",
                dataset=normalize_dataset_name(args.dataset),
                filename=file_path.name,
                exception=exception,
            )
            print(f"Logged error details to: {log_path}")
            append_session_entry(
                workflow="slope calculator",
                dataset=normalize_dataset_name(args.dataset),
                category="failed",
                value=file_path.name,
            )
            if not getattr(args, "interactive", False):
                raise
            while True:
                action = ask_error_action(
                    allow_edit=False, allow_skip=True, allow_stop=True, default="skip"
                )
                if action == "details":
                    print(format_exception_text(exception))
                    continue
                if action == "retry":
                    break
                if action == "skip":
                    return None, True
                return None, False

        except Exception as exception:  # noqa: BLE001
            print_processing_error("slope calculator", file_path.name, exception)
            log_path = append_error_log(
                workflow="slope calculator",
                dataset=normalize_dataset_name(args.dataset),
                filename=file_path.name,
                exception=exception,
            )
            print(f"Logged error details to: {log_path}")
            append_session_entry(
                workflow="slope calculator",
                dataset=normalize_dataset_name(args.dataset),
                category="failed",
                value=file_path.name,
            )
            if not getattr(args, "interactive", False):
                raise
            while True:
                action = ask_error_action(
                    allow_edit=True, allow_skip=True, allow_stop=True, default="retry"
                )
                if action == "details":
                    print(format_exception_text(exception))
                    continue
                if action == "edit":
                    args.ellipse_points = ask_int("Ellipse points", args.ellipse_points)
                    plot_mode = ask_plot_mode(default="none")
                    args.plot2d, args.plot3d = plot_flags_from_mode(plot_mode)
                    args.plot = args.plot2d or args.plot3d
                    break
                if action == "retry":
                    break
                if action == "skip":
                    return None, True
                return None, False


def main() -> None:
    args = parse_args() if len(sys.argv) > 1 else build_interactive_args()
    session_path = ensure_session_summary_path()
    append_session_note(
        "slope calculator",
        f"Started slope run (mode={args.mode})",
        dataset=normalize_dataset_name(args.dataset),
    )
    print(f"Session summary: {session_path}")
    output_path = args.output or build_analysis_output_path(
        OUTPUT_DIR,
        normalize_dataset_name(args.dataset),
        label="slopes",
        filename=args.filename if args.mode == "single" else None,
        start=None if args.mode != "range" else args.start,
        end=None if args.mode != "range" else args.end,
        prefix=args.prefix,
    )
    output_path = resolve_output_path(
        output_path, overwrite=args.overwrite, prompt_user=True
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)

    rows: list[list[object]] = []
    for file_path in collect_file_paths(args):
        row, should_continue = process_one_file(file_path, args)
        if row is not None:
            rows.append(row)
        if not should_continue:
            break

    with output_path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Filename", "m1", "m2"])
        writer.writerows(rows)

    append_session_entry(
        workflow="slope calculator",
        dataset=normalize_dataset_name(args.dataset),
        category="output",
        value=str(output_path),
    )
    print(f"Saved slopes CSV to: {output_path}")


if __name__ == "__main__":
    main()
