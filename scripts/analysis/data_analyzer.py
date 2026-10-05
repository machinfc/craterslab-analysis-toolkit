from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from craterslab.craters import Surface
from craterslab.ellipse import EllipticalModel
from craterslab.sensors import DepthMap, SensorResolution
from craterslab.visuals import plot_2D, plot_3D

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
from toolkit.exporters import build_observable_row, write_observables_csv
from toolkit.interactive import (
    ask_choice,
    ask_dataset,
    ask_file_mode,
    ask_float,
    ask_int,
    ask_plot_mode,
    ask_range,
    ask_text,
    ask_yes_no,
    choose_filename_from_directory,
    plot_flags_from_mode,
)
from toolkit.observable_plotting import interactive_observable_plotting
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

ALL_OBSERVABLES = [
    "D",
    "d_max",
    "d_exc",
    "mean_h_rim",
    "V_in",
    "V_ex",
    "V_exc",
    "V_cp",
    "H_cp",
    "epsilon",
]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Calculate crater observables from laboratory NPZ files or QuickMap XYZ files.",
    )
    parser.add_argument("--dataset", default="fluized")
    parser.add_argument("--mode", choices=["all", "single", "range"], default="range")
    parser.add_argument("--prefix", default=None)
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--end", type=int, default=51)
    parser.add_argument("--filename", default=None)
    parser.add_argument("--ellipse-points", type=int, default=20)
    parser.add_argument("--crop-mode", choices=["auto", "none"], default="auto")
    parser.add_argument("--plot2d", action="store_true")
    parser.add_argument("--plot3d", action="store_true")
    parser.add_argument("--plot-observables", action="store_true")
    parser.add_argument("--overwrite", action="store_true")
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
    parser.add_argument("--output", type=Path, default=None)
    return parser.parse_args(argv)


def iter_indices(start: int, end: int):
    step = 1 if end >= start else -1
    return range(start, end + step, step)


def build_interactive_args() -> argparse.Namespace:
    dataset = ask_dataset(default="fluized")
    dataset_info = get_dataset_info(dataset)
    mode = ask_file_mode(default="all")

    filename = None
    start = 1
    end = 1
    prefix = dataset_info["default_prefix"]

    if mode == "single":
        filename = choose_filename_from_directory(
            get_dataset_dir(dataset), [f".{dataset_info['file_type']}"]
        )
    elif mode == "range":
        prefix = ask_text("File prefix", prefix)
        default_end = 51 if dataset != "quickmap" else 2
        start, end = ask_range(1, default_end)
    else:
        prefix = ask_text("File prefix used to match all files", prefix)

    ellipse_points = ask_int("Ellipse points", 20)
    crop_mode = ask_choice(
        "Crop mode", {"auto": "Auto crop", "none": "No crop"}, default="auto"
    )
    plot_mode = ask_plot_mode(default="both")
    plot2d, plot3d = plot_flags_from_mode(plot_mode)

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

    default_output = build_analysis_output_path(
        OUTPUT_DIR,
        normalize_dataset_name(dataset),
        label="observables",
        filename=filename,
        start=None if filename or mode == "all" else start,
        end=None if filename or mode == "all" else end,
        prefix=prefix,
    )
    output = Path(ask_text("Output CSV path", str(default_output)))

    return argparse.Namespace(
        dataset=dataset,
        mode=mode,
        prefix=prefix,
        start=start,
        end=end,
        filename=filename,
        ellipse_points=ellipse_points,
        crop_mode=crop_mode,
        plot2d=plot2d,
        plot3d=plot3d,
        plot_observables=False,
        overwrite=False,
        skip_missing=False,
        xres=xres,
        yres=yres,
        zres=zres,
        scale=scale,
        z_shift=z_shift,
        output=output,
        interactive=True,
    )


def edit_analyzer_retry_parameters(args: argparse.Namespace) -> None:
    args.ellipse_points = ask_int("Ellipse points", args.ellipse_points)
    args.crop_mode = ask_choice(
        "Crop mode", {"auto": "Auto crop", "none": "No crop"}, default=args.crop_mode
    )
    plot_mode = ask_plot_mode(default="both" if args.plot2d and args.plot3d else "none")
    args.plot2d, args.plot3d = plot_flags_from_mode(plot_mode)
    if normalize_dataset_name(args.dataset) == "quickmap":
        args.xres = ask_float("X resolution", args.xres)
        args.yres = ask_float("Y resolution", args.yres)
        args.zres = ask_float("Z resolution", args.zres)
        args.scale = ask_text("Scale units", args.scale)
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


def load_depth_map(
    file_path: Path, args: argparse.Namespace, resolution: SensorResolution | None
) -> DepthMap:
    dataset = normalize_dataset_name(args.dataset)
    if dataset == "quickmap":
        if resolution is None:
            raise ValueError("QuickMap analysis requires a valid resolution")
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


def print_analysis_summary(filename: str, surface: Surface) -> None:
    print("\n" + "=" * 72)
    print(f"Analysis summary for: {filename}")
    print("=" * 72)
    print(f"Classified surface type: {surface.type}")
    if not surface.observables:
        print("No observables available.")
        return
    for observable_name, observable in surface.observables.items():
        print(f"  {observable_name}: {observable.value}")


def launch_fixer_for_file(dataset: str, filename: str) -> None:
    fixer_script = PROJECT_ROOT / "scripts" / "fixes" / "ellipse_fixer.py"
    command = [
        sys.executable,
        str(fixer_script),
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


def launch_visualizer_for_file(dataset: str, filename: str) -> None:
    visualizer_script = (
        PROJECT_ROOT / "scripts" / "visualization" / "depth_map_visualizer.py"
    )
    command = [
        sys.executable,
        str(visualizer_script),
        "--dataset",
        normalize_dataset_name(dataset),
        "--mode",
        "single",
        "--filename",
        filename,
    ]
    print(f"Opening visualizer: {' '.join(command)}")
    subprocess.run(command, check=False)


def ask_after_visualization(single_mode: bool = False) -> str:
    options = {
        "repeat": "Repeat visualization for this file",
        "fix": "Open fixer for this file",
        "exit": "Exit analyzer",
    }
    if not single_mode:
        options = {"continue": "Continue to the next file", **options}
    return ask_choice(
        "Next step", options, default="continue" if not single_mode else "repeat"
    )


def review_visualization_loop(
    file_path: Path,
    args: argparse.Namespace,
    depth_map: DepthMap,
    ellipse_model: EllipticalModel,
    surface: Surface,
    profile,
    stats: dict[str, list[str]],
) -> bool:
    print_analysis_summary(file_path.name, surface)
    while True:
        show_review_figures(
            depth_map=depth_map,
            profile=profile,
            ellipse_model=ellipse_model,
            surface=surface,
            show_2d=args.plot2d,
            show_profile=False,
            show_3d=args.plot3d,
            preview_scale=(1, 1, 5),
        )
        action = ask_after_visualization(
            single_mode=(args.mode == "single" or args.filename is not None)
        )
        if action == "repeat":
            continue
        if action == "fix":
            add_batch_item(stats, "problematic", file_path.name)
            launch_fixer_for_file(args.dataset, file_path.name)
            continue
        if action == "exit":
            return False
        return True


def process_one_file(
    file_path: Path,
    args: argparse.Namespace,
    resolution: SensorResolution | None,
    stats: dict[str, list[str]],
) -> tuple[list[object] | None, bool]:
    while True:
        try:
            if not file_path.exists():
                raise FileNotFoundError(f"Input file not found: {file_path}")

            print(f"Analyzing {file_path.name}")
            depth_map = load_depth_map(file_path, args, resolution)
            surface = Surface(depth_map)
            ellipse_model = EllipticalModel(depth_map, args.ellipse_points)
            profile = ellipse_model.max_profile()
            row = build_observable_row(file_path.name, surface, ALL_OBSERVABLES)
            append_session_entry(
                workflow="analyzer",
                dataset=normalize_dataset_name(args.dataset),
                category="analyzed",
                value=file_path.name,
            )
            add_batch_item(stats, "analyzed", file_path.name)

            if getattr(args, "interactive", False) and (args.plot2d or args.plot3d):
                should_continue = review_visualization_loop(
                    file_path, args, depth_map, ellipse_model, surface, profile, stats
                )
                return row, should_continue

            if args.plot2d:
                plot_2D(depth_map, profile=profile, ellipse=ellipse_model)
            if args.plot3d:
                plot_3D(
                    depth_map,
                    ellipse=ellipse_model,
                    preview_scale=(1, 1, 5),
                    block=True,
                )
            return row, True

        except FileNotFoundError as exception:
            if args.skip_missing and not getattr(args, "interactive", False):
                print(f"[WARN] {exception}")
                return None, True
            print_processing_error("analyzer", file_path.name, exception)
            log_path = append_error_log(
                workflow="analyzer",
                dataset=normalize_dataset_name(args.dataset),
                filename=file_path.name,
                exception=exception,
            )
            print(f"Logged error details to: {log_path}")
            append_session_entry(
                workflow="analyzer",
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
                    return None, True
                return None, False

        except Exception as exception:  # noqa: BLE001
            print_processing_error("analyzer", file_path.name, exception)
            log_path = append_error_log(
                workflow="analyzer",
                dataset=normalize_dataset_name(args.dataset),
                filename=file_path.name,
                exception=exception,
            )
            print(f"Logged error details to: {log_path}")
            append_session_entry(
                workflow="analyzer",
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
                if action == "fix":
                    launch_fixer_for_file(args.dataset, file_path.name)
                    continue
                if action == "edit":
                    edit_analyzer_retry_parameters(args)
                    break
                if action == "retry":
                    break
                if action == "skip":
                    return None, True
                return None, False


def revisit_problematic_files(dataset: str, problematic_files: list[str]) -> None:
    if not problematic_files:
        return
    action = ask_problematic_action()
    if action != "reopen":
        return
    revisit_mode = ask_choice(
        "How do you want to reopen the problematic files",
        {
            "visualizer": "Open them in the visualizer",
            "fixer": "Open them in the fixer",
        },
        default="visualizer",
    )
    for filename in problematic_files:
        if revisit_mode == "visualizer":
            launch_visualizer_for_file(dataset, filename)
        else:
            launch_fixer_for_file(dataset, filename)


def run_analysis(args: argparse.Namespace) -> tuple[Path, list[list[object]]]:
    dataset = normalize_dataset_name(args.dataset)
    resolution = build_resolution(args)
    rows: list[list[object]] = []
    stats = new_batch_stats()
    session_path = ensure_session_summary_path()
    append_session_note(
        "analyzer", f"Started analyzer run (mode={args.mode})", dataset=dataset
    )
    print(f"Session summary: {session_path}")

    for file_path in collect_file_paths(args):
        row, should_continue = process_one_file(file_path, args, resolution, stats)
        if row is not None:
            rows.append(row)
        if not should_continue:
            break

    output_path = args.output or build_analysis_output_path(
        OUTPUT_DIR,
        dataset,
        label="observables",
        filename=args.filename,
        start=None if args.filename or args.mode == "all" else args.start,
        end=None if args.filename or args.mode == "all" else args.end,
        prefix=args.prefix,
    )
    output_path = resolve_output_path(
        output_path, overwrite=args.overwrite, prompt_user=True
    )
    output_path = write_observables_csv(output_path, ALL_OBSERVABLES, rows)
    append_session_entry(
        workflow="analyzer", dataset=dataset, category="outputs", value=str(output_path)
    )
    add_batch_item(stats, "outputs", str(output_path))
    print(f"Saved observables CSV to: {output_path}")
    print_batch_summary("analyzer", stats)
    if getattr(args, "interactive", False):
        revisit_problematic_files(dataset, stats.get("problematic", []))
    return output_path, rows


def maybe_plot_observables(args: argparse.Namespace, rows: list[list[object]]) -> None:
    interactive = getattr(args, "interactive", False)
    if args.plot_observables or (
        interactive and ask_yes_no("Plot observables against each other", default=False)
    ):
        interactive_observable_plotting(
            rows, ALL_OBSERVABLES, title_prefix=normalize_dataset_name(args.dataset)
        )


def main() -> None:
    args = parse_args() if len(sys.argv) > 1 else build_interactive_args()
    _output_path, rows = run_analysis(args)
    maybe_plot_observables(args, rows)


if __name__ == "__main__":
    main()
