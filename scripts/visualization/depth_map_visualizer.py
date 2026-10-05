from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from craterslab.craters import Surface
from craterslab.ellipse import EllipticalModel
from craterslab.sensors import DepthMap, SensorResolution

from toolkit.batch_review import (
    add_batch_item,
    ask_problematic_action,
    new_batch_stats,
    print_batch_summary,
)
from toolkit.error_handling import (
    append_error_log,
    ask_error_action,
    format_exception_text,
    print_processing_error,
)
from toolkit.interactive import (
    ask_choice,
    ask_dataset,
    ask_file_mode,
    ask_float,
    ask_int,
    ask_range,
    ask_text,
    ask_visualizer_mode,
    choose_filename_from_directory,
    visualization_flags_from_mode,
)
from toolkit.paths import get_dataset_dir, get_dataset_info, normalize_dataset_name
from toolkit.session_summary import (
    append_session_entry,
    append_session_note,
    ensure_session_summary_path,
)
from toolkit.visualization_helpers import show_review_figures

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Visualize crater files in 2D, 3D, and/or profile mode."
    )
    parser.add_argument("--dataset", default="fluized")
    parser.add_argument("--mode", choices=["all", "single", "range"], default="range")
    parser.add_argument("--prefix", default=None)
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--end", type=int, default=51)
    parser.add_argument("--filename", default=None)
    parser.add_argument("--ellipse-points", type=int, default=20)
    parser.add_argument("--crop-mode", choices=["auto", "none"], default="auto")
    parser.add_argument("--show-2d", action="store_true")
    parser.add_argument("--show-profile", action="store_true")
    parser.add_argument("--show-3d", action="store_true")
    parser.add_argument("--skip-missing", action="store_true")
    parser.add_argument("--xres", type=float, default=None)
    parser.add_argument("--yres", type=float, default=None)
    parser.add_argument("--zres", type=float, default=None)
    parser.add_argument("--scale", default=None)
    parser.add_argument(
        "--z-shift",
        type=float,
        default=0.0,
        help="Vertical offset used to adjust the LROC/QuickMap zero reference for lunar geodesy.",
    )
    return parser.parse_args(argv)


def iter_indices(start: int, end: int):
    step = 1 if end >= start else -1
    return range(start, end + step, step)


def build_interactive_args() -> argparse.Namespace:
    dataset = ask_dataset(default="fluized")
    dataset_info = get_dataset_info(dataset)
    mode = ask_file_mode(default="all")

    filename = None
    prefix = dataset_info["default_prefix"]
    start, end = 1, (51 if dataset != "quickmap" else 2)
    if mode == "single":
        filename = choose_filename_from_directory(
            get_dataset_dir(dataset), [f".{dataset_info['file_type']}"]
        )
    elif mode == "range":
        prefix = ask_text("File prefix", prefix)
        start, end = ask_range(start, end)
    else:
        prefix = ask_text("File prefix used to match all files", prefix)

    visualizer_mode = ask_visualizer_mode(default="all")
    show_2d, show_profile, show_3d = visualization_flags_from_mode(visualizer_mode)

    xres = yres = zres = None
    scale = None
    z_shift = 0.0
    if dataset == "quickmap":
        resolution = dataset_info["default_resolution"]
        xres = ask_float("X resolution", resolution["xres"])
        yres = ask_float("Y resolution", resolution["yres"])
        zres = ask_float("Z resolution", resolution["zres"])
        scale = ask_text("Scale units", resolution["scale"])
        z_shift = ask_float(
            "Z shift (lunar geodesy vertical offset used to align the LROC/QuickMap zero level)",
            0.0,
        )

    return argparse.Namespace(
        dataset=dataset,
        mode=mode,
        prefix=prefix,
        start=start,
        end=end,
        filename=filename,
        ellipse_points=ask_int("Ellipse points", 20),
        crop_mode=ask_choice(
            "Crop mode", {"auto": "Automatic crop", "none": "No crop"}, default="auto"
        ),
        show_2d=show_2d,
        show_profile=show_profile,
        show_3d=show_3d,
        skip_missing=False,
        xres=xres,
        yres=yres,
        zres=zres,
        scale=scale,
        z_shift=z_shift,
        interactive=True,
    )


def adjust_visualizer_args(args: argparse.Namespace) -> None:
    args.ellipse_points = ask_int("Ellipse points", args.ellipse_points)
    args.crop_mode = ask_choice(
        "Crop mode",
        {"auto": "Automatic crop", "none": "No crop"},
        default=args.crop_mode,
    )
    mode = ask_visualizer_mode(
        default=(
            "all"
            if args.show_2d and args.show_profile and args.show_3d
            else (
                "2d"
                if args.show_2d and not args.show_profile and not args.show_3d
                else (
                    "3d"
                    if args.show_3d and not args.show_2d and not args.show_profile
                    else (
                        "profile"
                        if args.show_profile and not args.show_2d and not args.show_3d
                        else (
                            "2d_profile"
                            if args.show_2d and args.show_profile and not args.show_3d
                            else "3d_profile"
                        )
                    )
                )
            )
        )
    )
    args.show_2d, args.show_profile, args.show_3d = visualization_flags_from_mode(mode)
    if normalize_dataset_name(args.dataset) == "quickmap":
        args.z_shift = ask_float(
            "Z shift (lunar geodesy vertical offset used to align the LROC/QuickMap zero level)",
            args.z_shift,
        )


def build_resolution(args: argparse.Namespace) -> SensorResolution | None:
    if normalize_dataset_name(args.dataset) != "quickmap":
        return None
    defaults = get_dataset_info(args.dataset)["default_resolution"]
    return SensorResolution(
        args.xres if args.xres is not None else defaults["xres"],
        args.yres if args.yres is not None else defaults["yres"],
        args.zres if args.zres is not None else defaults["zres"],
        args.scale if args.scale is not None else defaults["scale"],
    )


def collect_file_paths(args: argparse.Namespace) -> list[Path]:
    dataset_info = get_dataset_info(args.dataset)
    dataset_dir = get_dataset_dir(args.dataset)
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


def load_depth_map(
    file_path: Path, args: argparse.Namespace, resolution: SensorResolution | None
) -> DepthMap:
    dataset = normalize_dataset_name(args.dataset)
    if dataset == "quickmap":
        if resolution is None:
            raise ValueError("QuickMap visualization requires valid resolution values")
        print(
            "Using z_shift to correct the lunar geodetic zero reference in the imported LROC/QuickMap data."
        )
        depth_map = DepthMap.from_xyz_file(
            file_path.name,
            data_folder=str(file_path.parent),
            resolution=resolution,
            z_shift=args.z_shift,
        )
    else:
        depth_map = DepthMap.load(file_path)
    if args.crop_mode == "auto":
        depth_map.auto_crop()
    return depth_map


def print_scientific_summary(filename: str, surface: Surface, profile) -> None:
    print("\n" + "=" * 72)
    print(f"Scientific review summary for: {filename}")
    print("=" * 72)
    print(f"Classified surface type: {surface.type}")
    try:
        m1, m2 = profile.slopes()
        print(f"Profile slopes: m1={m1}, m2={m2}")
    except Exception:  # noqa: BLE001
        print("Profile slopes: unavailable")
    print("Observables:")
    if not surface.observables:
        print("  No observables available.")
        return
    for observable_name, observable in surface.observables.items():
        print(f"  {observable_name}: {observable.value}")


def launch_corresponding_fixer(dataset: str, filename: str) -> None:
    script = PROJECT_ROOT / "scripts" / "fixes" / "ellipse_fixer.py"
    command = [
        sys.executable,
        str(script),
        "--interactive",
        "--dataset",
        normalize_dataset_name(dataset),
        "--mode",
        "single",
        "--filename",
        filename,
    ]
    print(f"Opening fixer: {' '.join(command)}")
    subprocess.run(command, check=False)


def ask_post_visualization_action(single_mode: bool = False) -> str:
    options = {
        "repeat": "Repeat visualization for this file",
        "fix": "Open the corresponding fixer",
        "exit": "Exit visualizer",
    }
    if not single_mode:
        options = {"continue": "Continue to the next file", **options}
    return ask_choice(
        "Next step", options, default="continue" if not single_mode else "repeat"
    )


def visualize_file(
    file_path: Path,
    args: argparse.Namespace,
    resolution: SensorResolution | None,
    stats: dict[str, list[str]],
) -> bool:
    while True:
        try:
            if not file_path.exists():
                raise FileNotFoundError(f"Input file not found: {file_path}")

            depth_map = load_depth_map(file_path, args, resolution)
            ellipse_model = EllipticalModel(depth_map, args.ellipse_points)
            profile = ellipse_model.max_profile()
            surface = Surface(depth_map)

            print(f"Processing {file_path.name}")
            append_session_entry(
                workflow="visualizer",
                dataset=normalize_dataset_name(args.dataset),
                category="reviewed",
                value=file_path.name,
            )
            add_batch_item(stats, "reviewed", file_path.name)
            print_scientific_summary(file_path.name, surface, profile)

            slopes_drawn = show_review_figures(
                depth_map=depth_map,
                profile=profile,
                ellipse_model=ellipse_model,
                surface=surface,
                show_2d=args.show_2d,
                show_profile=args.show_profile,
                show_3d=args.show_3d,
                preview_scale=(1, 1, 4),
            )
            if args.show_profile and not slopes_drawn:
                print("[WARN] Profile slopes could not be drawn for this file.")

            action = ask_post_visualization_action(
                single_mode=(args.mode == "single" or args.filename is not None)
            )
            if action == "repeat":
                continue
            if action == "fix":
                launch_corresponding_fixer(args.dataset, file_path.name)
                continue
            if action == "exit":
                return False
            return True

        except FileNotFoundError as exception:
            if args.skip_missing and not getattr(args, "interactive", False):
                print(f"[WARN] {exception}")
                return True
            print_processing_error("visualizer", file_path.name, exception)
            log_path = append_error_log(
                workflow="visualizer",
                dataset=normalize_dataset_name(args.dataset),
                filename=file_path.name,
                exception=exception,
            )
            print(f"Logged error details to: {log_path}")
            append_session_entry(
                workflow="visualizer",
                dataset=normalize_dataset_name(args.dataset),
                category="failed",
                value=file_path.name,
            )
            add_batch_item(stats, "failed", file_path.name)
            add_batch_item(stats, "problematic", file_path.name)
            if not getattr(args, "interactive", False):
                raise
            while True:
                action = ask_error_action(
                    allow_fix=False,
                    allow_edit=False,
                    allow_skip=True,
                    allow_stop=True,
                    default="skip",
                )
                if action == "details":
                    print(format_exception_text(exception))
                    continue
                if action == "retry":
                    break
                if action == "skip":
                    return True
                return False

        except Exception as exception:  # noqa: BLE001
            print_processing_error("visualizer", file_path.name, exception)
            log_path = append_error_log(
                workflow="visualizer",
                dataset=normalize_dataset_name(args.dataset),
                filename=file_path.name,
                exception=exception,
            )
            print(f"Logged error details to: {log_path}")
            append_session_entry(
                workflow="visualizer",
                dataset=normalize_dataset_name(args.dataset),
                category="failed",
                value=file_path.name,
            )
            add_batch_item(stats, "failed", file_path.name)
            add_batch_item(stats, "problematic", file_path.name)
            if not getattr(args, "interactive", False):
                raise
            while True:
                action = ask_error_action(
                    allow_fix=True,
                    allow_edit=True,
                    allow_skip=True,
                    allow_stop=True,
                    default="retry",
                )
                if action == "details":
                    print(format_exception_text(exception))
                    continue
                if action == "edit":
                    adjust_visualizer_args(args)
                    break
                if action == "fix":
                    launch_corresponding_fixer(args.dataset, file_path.name)
                    continue
                if action == "retry":
                    break
                if action == "skip":
                    return True
                return False


def reopen_problematic_visualizations(
    args: argparse.Namespace,
    problematic_files: list[str],
    resolution: SensorResolution | None,
) -> None:
    if not problematic_files:
        return
    if ask_problematic_action() != "reopen":
        return
    for filename in problematic_files:
        file_path = get_dataset_dir(args.dataset) / filename
        if file_path.exists():
            visualize_file(
                file_path,
                args,
                resolution,
                {"reviewed": [], "failed": [], "problematic": []},
            )


def main() -> None:
    args = parse_args() if len(sys.argv) > 1 else build_interactive_args()
    session_path = ensure_session_summary_path()
    append_session_note(
        "visualizer",
        f"Started visual review (mode={args.mode})",
        dataset=normalize_dataset_name(args.dataset),
    )
    print(f"Session summary: {session_path}")
    if not (args.show_2d or args.show_profile or args.show_3d):
        args.show_2d = args.show_profile = args.show_3d = True

    resolution = build_resolution(args)
    stats = new_batch_stats()
    for file_path in collect_file_paths(args):
        should_continue = visualize_file(file_path, args, resolution, stats)
        if not should_continue:
            break
    print_batch_summary("visualizer", stats)
    if getattr(args, "interactive", False):
        reopen_problematic_visualizations(
            args, stats.get("problematic", []), resolution
        )


if __name__ == "__main__":
    main()
