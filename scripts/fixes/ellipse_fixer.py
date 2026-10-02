from __future__ import annotations

import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from craterslab.classification import SurfaceType
from craterslab.craters import Surface
from craterslab.sensors import DepthMap, SensorResolution
from craterslab.visuals import plot_2D, plot_3D
from toolkit.batch_review import add_batch_item, ask_problematic_action, new_batch_stats, print_batch_summary
from toolkit.error_handling import append_error_log, ask_error_action, format_exception_text, print_processing_error
from toolkit.exporters import build_observable_row, write_observables_csv
from toolkit.fix_logging import append_fix_log
from toolkit.interactive import (
    ask_bbox,
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
from toolkit.output_control import build_analysis_output_path, resolve_output_path
from toolkit.session_summary import append_session_entry, append_session_note, ensure_session_summary_path
from toolkit.paths import OUTPUT_DIR, get_dataset_dir, get_dataset_info, normalize_dataset_name
from toolkit.visualization_helpers import show_review_figures

ALL_OBSERVABLES = ["D", "d_max", "V_in", "V_ex", "V_exc", "epsilon", "V_cp", "H_cp"]
SURFACE_TYPE_OPTIONS = {
    "simple_crater": SurfaceType.SIMPLE_CRATER,
    "complex_crater": SurfaceType.COMPLEX_CRATER,
    "sand_mound": SurfaceType.SAND_MOUND,
    "unknown": SurfaceType.UNKNOWN,
}


def parse_surface_type(value: str) -> SurfaceType:
    return SurfaceType[value.upper()]



def parse_bbox(value: str) -> tuple[int, int, int, int]:
    parts = [int(part.strip()) for part in value.split(",")]
    if len(parts) != 4:
        raise argparse.ArgumentTypeError("Bounding box must contain 4 integers: x,y,w,h")
    return tuple(parts)  # type: ignore[return-value]



def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="General crater fixer for ellipse fitting and surface-type correction.",
    )
    parser.add_argument("--dataset", default="compacted")
    parser.add_argument("--mode", choices=["all", "single", "range"], default="single")
    parser.add_argument("--prefix", default=None)
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--end", type=int, default=1)
    parser.add_argument("--filename", default=None)
    parser.add_argument("--surface-type", type=parse_surface_type, default=SurfaceType.COMPLEX_CRATER)
    parser.add_argument("--ellipse-points", type=int, default=20)
    parser.add_argument("--crop-mode", choices=["bbox", "auto", "borders", "none"], default="bbox")
    parser.add_argument("--bbox", type=parse_bbox, default=(10, 50, 100, 100))
    parser.add_argument("--crop-ratio", type=float, default=0.6)
    parser.add_argument("--plot2d", action="store_true")
    parser.add_argument("--plot3d", action="store_true")
    parser.add_argument("--interactive", action="store_true")
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
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="CSV output path for corrected observables.",
    )
    return parser.parse_args(argv)



def iter_indices(start: int, end: int):
    step = 1 if end >= start else -1
    return range(start, end + step, step)



def build_interactive_batch_args(initial: argparse.Namespace | None = None) -> argparse.Namespace:
    initial = initial or argparse.Namespace(dataset="compacted", filename=None)
    dataset = normalize_dataset_name(getattr(initial, "dataset", "compacted"))
    dataset_info = get_dataset_info(dataset)
    mode = getattr(initial, "mode", None) or ask_file_mode(default="all")
    prefix = getattr(initial, "prefix", None) or dataset_info["default_prefix"]
    start = getattr(initial, "start", 1)
    end = getattr(initial, "end", 51 if dataset != "quickmap" else 2)
    filename = getattr(initial, "filename", None)

    if mode == "single":
        filename = filename or choose_filename_from_directory(get_dataset_dir(dataset), [f".{dataset_info['file_type']}"])
    elif mode == "range":
        prefix = ask_text("File prefix", prefix)
        start, end = ask_range(start, end)
    else:
        prefix = ask_text("File prefix used to match all files", prefix)

    crop_mode = ask_choice(
        "Default crop mode",
        {
            "bbox": "Manual crop using bounding box",
            "auto": "Automatic crop",
            "borders": "Crop borders by ratio",
            "none": "No crop",
        },
        default=getattr(initial, "crop_mode", "bbox" if dataset != "quickmap" else "borders"),
    )
    bbox = getattr(initial, "bbox", (10, 50, 100, 100))
    crop_ratio = getattr(initial, "crop_ratio", 0.15 if dataset == "quickmap" else 0.6)
    if crop_mode == "bbox":
        bbox = ask_bbox(bbox)
    elif crop_mode == "borders":
        crop_ratio = ask_float("Crop ratio", crop_ratio)

    plot_mode = ask_plot_mode(default="both")
    plot2d, plot3d = plot_flags_from_mode(plot_mode)

    xres = yres = zres = None
    scale = None
    z_shift = getattr(initial, "z_shift", 0.0)
    if dataset == "quickmap":
        resolution = dataset_info["default_resolution"]
        xres = ask_float("X resolution", getattr(initial, "xres", resolution["xres"]))
        yres = ask_float("Y resolution", getattr(initial, "yres", resolution["yres"]))
        zres = ask_float("Z resolution", getattr(initial, "zres", resolution["zres"]))
        scale = ask_text("Scale units", getattr(initial, "scale", resolution["scale"]))
        z_shift = ask_float(
            "Z shift (lunar geodesy vertical offset used to align the LROC/QuickMap zero level)",
            z_shift,
        )

    default_output = build_analysis_output_path(
        OUTPUT_DIR,
        dataset,
        label="fixed_observables",
        filename=filename if mode == "single" else None,
        start=None if mode != "range" else start,
        end=None if mode != "range" else end,
        prefix=prefix,
    )

    return argparse.Namespace(
        dataset=dataset,
        mode=mode,
        prefix=prefix,
        start=start,
        end=end,
        filename=filename,
        surface_type=getattr(initial, "surface_type", SurfaceType.COMPLEX_CRATER),
        ellipse_points=getattr(initial, "ellipse_points", 20),
        crop_mode=crop_mode,
        bbox=bbox,
        crop_ratio=crop_ratio,
        plot2d=plot2d,
        plot3d=plot3d,
        interactive=True,
        overwrite=getattr(initial, "overwrite", False),
        skip_missing=getattr(initial, "skip_missing", True),
        xres=xres,
        yres=yres,
        zres=zres,
        scale=scale,
        z_shift=z_shift,
        output=Path(ask_text("Output CSV path", str(getattr(initial, "output", default_output)))),
    )



def collect_file_paths(args: argparse.Namespace) -> list[Path]:
    dataset_dir = get_dataset_dir(args.dataset)
    dataset_info = get_dataset_info(args.dataset)
    suffix = f".{dataset_info['file_type']}"
    if args.mode == "single" or args.filename:
        if not args.filename:
            raise ValueError("Single mode requires a filename")
        return [dataset_dir / args.filename]
    prefix = args.prefix or dataset_info["default_prefix"]
    if args.mode == "all":
        return sorted(path for path in dataset_dir.glob(f"{prefix}_*{suffix}") if path.is_file())
    return [dataset_dir / f"{prefix}_{index}{suffix}" for index in iter_indices(args.start, args.end)]



def build_resolution(args: argparse.Namespace) -> SensorResolution | None:
    dataset = normalize_dataset_name(args.dataset)
    if dataset != "quickmap":
        return None
    defaults = get_dataset_info(dataset)["default_resolution"]
    return SensorResolution(
        args.xres if args.xres is not None else defaults["xres"],
        args.yres if args.yres is not None else defaults["yres"],
        args.zres if args.zres is not None else defaults["zres"],
        args.scale if args.scale is not None else defaults["scale"],
    )



def load_depth_map(file_path: Path, args: argparse.Namespace) -> DepthMap:
    dataset = normalize_dataset_name(args.dataset)
    dataset_dir = get_dataset_dir(dataset)
    if dataset == "quickmap":
        resolution = build_resolution(args)
        if resolution is None:
            raise ValueError("QuickMap fixing requires valid resolution values")
        print("Using z_shift to correct the lunar geodetic zero reference in the imported LROC/QuickMap data.")
        depth_map = DepthMap.from_xyz_file(file_path.name, data_folder=str(dataset_dir), resolution=resolution, z_shift=args.z_shift)
    else:
        depth_map = DepthMap.load(file_path)

    if args.crop_mode == "auto":
        depth_map.auto_crop()
    elif args.crop_mode == "borders":
        depth_map.crop_borders(args.crop_ratio)
    elif args.crop_mode == "bbox":
        depth_map.crop(args.bbox)
    return depth_map



def display_fix_summary(filename: str, surface: Surface) -> None:
    print("\n" + "=" * 72)
    print(f"Proposed fix for: {filename}")
    print("=" * 72)
    print(f"Surface type: {surface.type}")
    for observable in ALL_OBSERVABLES:
        if observable in surface.observables:
            print(f"  {observable}: {surface.observables[observable].value}")
        else:
            print(f"  {observable}: not found")



def review_single_file(file_path: Path, base_args: argparse.Namespace, batch_output_path: Path) -> list[object] | None:
    file_args = argparse.Namespace(**vars(base_args))
    file_args.filename = file_path.name
    while True:
        try:
            depth_map = load_depth_map(file_path, file_args)
            surface = Surface(depth_map, ellipse_points=file_args.ellipse_points)
            surface.set_type(file_args.surface_type)
            profile = surface.max_profile

            if file_args.plot2d or file_args.plot3d:
                show_review_figures(
                    depth_map=depth_map,
                    profile=profile,
                    ellipse_model=surface.em,
                    surface=surface,
                    show_2d=file_args.plot2d,
                    show_profile=False,
                    show_3d=file_args.plot3d,
                    preview_scale=(1, 1, 4),
                )

            display_fix_summary(file_path.name, surface)
            if ask_yes_no("Are you satisfied with this fix", default=True):
                row = build_observable_row(file_path.name, surface, ALL_OBSERVABLES)
                log_path = append_fix_log(
                    script_name="ellipse_fixer.py",
                    dataset=normalize_dataset_name(file_args.dataset),
                    filename=file_path.name,
                    parameters={
                        "surface_type": file_args.surface_type,
                        "ellipse_points": file_args.ellipse_points,
                        "crop_mode": file_args.crop_mode,
                        "bbox": getattr(file_args, "bbox", None),
                        "crop_ratio": getattr(file_args, "crop_ratio", None),
                        "z_shift": getattr(file_args, "z_shift", None),
                    },
                    observables={
                        observable: surface.observables[observable].value if observable in surface.observables else "not found"
                        for observable in ALL_OBSERVABLES
                    },
                    output_path=batch_output_path,
                )
                print(f"Logged correction details to: {log_path}")
                return row

            print("\nLet's adjust the fixer parameters and try again.")
            surface_key = ask_choice(
                "Select corrected surface type",
                {key: value.name.replace("_", " ").title() for key, value in SURFACE_TYPE_OPTIONS.items()},
                default=file_args.surface_type.name.lower(),
            )
            file_args.surface_type = SURFACE_TYPE_OPTIONS[surface_key]
            file_args.ellipse_points = ask_int("Ellipse points", file_args.ellipse_points)
            file_args.crop_mode = ask_choice(
                "Crop mode",
                {
                    "bbox": "Manual crop using bounding box",
                    "auto": "Automatic crop",
                    "borders": "Crop borders by ratio",
                    "none": "No crop",
                },
                default=file_args.crop_mode,
            )
            if file_args.crop_mode == "bbox":
                file_args.bbox = ask_bbox(file_args.bbox)
            elif file_args.crop_mode == "borders":
                file_args.crop_ratio = ask_float("Crop ratio", file_args.crop_ratio)
            if normalize_dataset_name(file_args.dataset) == "quickmap":
                file_args.z_shift = ask_float(
                    "Z shift (lunar geodesy vertical offset used to align the LROC/QuickMap zero level)",
                    file_args.z_shift,
                )
            plot_mode = ask_plot_mode(default="both" if file_args.plot2d and file_args.plot3d else "none")
            file_args.plot2d, file_args.plot3d = plot_flags_from_mode(plot_mode)

        except Exception as exception:  # noqa: BLE001
            print_processing_error("fixer", file_path.name, exception)
            log_path = append_error_log(
                workflow="fixer",
                dataset=normalize_dataset_name(file_args.dataset),
                filename=file_path.name,
                exception=exception,
            )
            print(f"Logged error details to: {log_path}")
            append_session_entry(workflow="fixer", dataset=normalize_dataset_name(file_args.dataset), category="failed", value=file_path.name)
            if hasattr(base_args, "stats"):
                add_batch_item(base_args.stats, "failed", file_path.name)
                add_batch_item(base_args.stats, "problematic", file_path.name)
            while True:
                action = ask_error_action(allow_fix=False, allow_edit=True, allow_skip=True, allow_stop=True, default="retry")
                if action == "details":
                    print(format_exception_text(exception))
                    continue
                if action == "edit":
                    surface_key = ask_choice(
                        "Select corrected surface type",
                        {key: value.name.replace("_", " ").title() for key, value in SURFACE_TYPE_OPTIONS.items()},
                        default=file_args.surface_type.name.lower(),
                    )
                    file_args.surface_type = SURFACE_TYPE_OPTIONS[surface_key]
                    file_args.ellipse_points = ask_int("Ellipse points", file_args.ellipse_points)
                    file_args.crop_mode = ask_choice(
                        "Crop mode",
                        {
                            "bbox": "Manual crop using bounding box",
                            "auto": "Automatic crop",
                            "borders": "Crop borders by ratio",
                            "none": "No crop",
                        },
                        default=file_args.crop_mode,
                    )
                    if file_args.crop_mode == "bbox":
                        file_args.bbox = ask_bbox(file_args.bbox)
                    elif file_args.crop_mode == "borders":
                        file_args.crop_ratio = ask_float("Crop ratio", file_args.crop_ratio)
                    if normalize_dataset_name(file_args.dataset) == "quickmap":
                        file_args.xres = ask_float("X resolution", file_args.xres)
                        file_args.yres = ask_float("Y resolution", file_args.yres)
                        file_args.zres = ask_float("Z resolution", file_args.zres)
                        file_args.scale = ask_text("Scale units", file_args.scale)
                        file_args.z_shift = ask_float(
                            "Z shift (lunar geodesy vertical offset used to align the LROC/QuickMap zero level)",
                            file_args.z_shift,
                        )
                    plot_mode = ask_plot_mode(default="both" if file_args.plot2d and file_args.plot3d else "none")
                    file_args.plot2d, file_args.plot3d = plot_flags_from_mode(plot_mode)
                    break
                if action == "retry":
                    break
                if action == "skip":
                    return None
                raise SystemExit(1)



def run_batch_fix(args: argparse.Namespace) -> tuple[Path, list[list[object]]]:
    session_path = ensure_session_summary_path()
    append_session_note("fixer", f"Started fixer run (mode={args.mode})", dataset=normalize_dataset_name(args.dataset))
    print(f"Session summary: {session_path}")
    output_path = args.output or build_analysis_output_path(
        OUTPUT_DIR,
        normalize_dataset_name(args.dataset),
        label="fixed_observables",
        filename=args.filename if args.mode == "single" else None,
        start=None if args.mode != "range" else args.start,
        end=None if args.mode != "range" else args.end,
        prefix=args.prefix,
    )
    output_path = resolve_output_path(output_path, overwrite=args.overwrite, prompt_user=True)

    rows: list[list[object]] = []
    stats = new_batch_stats()
    args.stats = stats
    for file_path in collect_file_paths(args):
        if not file_path.exists():
            message = f"Input file not found: {file_path}"
            if args.skip_missing:
                print(f"[WARN] {message}")
                continue
            raise FileNotFoundError(message)

        if getattr(args, "interactive", False):
            row = review_single_file(file_path, args, output_path)
        else:
            depth_map = load_depth_map(file_path, args)
            surface = Surface(depth_map, ellipse_points=args.ellipse_points)
            surface.set_type(args.surface_type)
            row = build_observable_row(file_path.name, surface, ALL_OBSERVABLES)
            log_path = append_fix_log(
                script_name="ellipse_fixer.py",
                dataset=normalize_dataset_name(args.dataset),
                filename=file_path.name,
                parameters={
                    "surface_type": args.surface_type,
                    "ellipse_points": args.ellipse_points,
                    "crop_mode": args.crop_mode,
                    "bbox": getattr(args, "bbox", None),
                    "crop_ratio": getattr(args, "crop_ratio", None),
                    "z_shift": getattr(args, "z_shift", None),
                },
                observables={
                    observable: surface.observables[observable].value if observable in surface.observables else "not found"
                    for observable in ALL_OBSERVABLES
                },
                output_path=output_path,
            )
            print(f"Logged correction details to: {log_path}")
            append_session_entry(workflow="fixer", dataset=normalize_dataset_name(args.dataset), category="corrected", value=file_path.name)
            add_batch_item(stats, "corrected", file_path.name)

        if row is not None:
            rows.append(row)

        if getattr(args, "interactive", False) and args.mode != "single":
            if not ask_yes_no("Continue to the next file", default=True):
                break

    output_path = write_observables_csv(output_path, ALL_OBSERVABLES, rows)
    append_session_entry(workflow="fixer", dataset=normalize_dataset_name(args.dataset), category="outputs", value=str(output_path))
    add_batch_item(stats, "outputs", str(output_path))
    print(f"Saved corrected observables to: {output_path}")
    print_batch_summary("fixer", stats)
    if getattr(args, "interactive", False) and stats.get("problematic"):
        if ask_problematic_action() == "reopen":
            for filename in stats.get("problematic", []):
                review_single_file(get_dataset_dir(args.dataset) / filename, args, output_path)
    return output_path, rows



def main() -> None:
    if len(sys.argv) > 1:
        args = parse_args()
        if args.interactive:
            args = build_interactive_batch_args(args)
    else:
        args = build_interactive_batch_args()
    run_batch_fix(args)


if __name__ == "__main__":
    main()
