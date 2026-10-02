from __future__ import annotations

import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from craterslab.ellipse import EllipticalModel
from craterslab.profiles import Profile
from craterslab.sensors import DepthMap, SensorResolution
from craterslab.visuals import plot_2D, plot_3D
from toolkit.error_handling import append_error_log, ask_error_action, format_exception_text, print_processing_error
from toolkit.exporters import write_profile_csv
from toolkit.fix_logging import append_fix_log
from toolkit.session_summary import append_session_entry, append_session_note, ensure_session_summary_path
from toolkit.interactive import (
    ask_bbox,
    ask_choice,
    ask_dataset,
    ask_float,
    ask_int,
    ask_optional_point,
    ask_plot_mode,
    ask_text,
    ask_yes_no,
    choose_filename_from_directory,
    plot_flags_from_mode,
)
from toolkit.paths import OUTPUT_DIR, get_dataset_dir, get_dataset_info, normalize_dataset_name
from toolkit.visualization_helpers import show_review_figures


def parse_point(value: str) -> tuple[int, int]:
    parts = [int(part.strip()) for part in value.split(",")]
    if len(parts) != 2:
        raise argparse.ArgumentTypeError("Point must have format x,y")
    return tuple(parts)  # type: ignore[return-value]



def parse_bbox(value: str) -> tuple[int, int, int, int]:
    parts = [int(part.strip()) for part in value.split(",")]
    if len(parts) != 4:
        raise argparse.ArgumentTypeError("Bounding box must contain 4 integers: x,y,w,h")
    return tuple(parts)  # type: ignore[return-value]



def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract or fix a crater profile for a single file.",
    )
    parser.add_argument("--dataset", default="fluized")
    parser.add_argument("--filename", default=None)
    parser.add_argument("--ellipse-points", type=int, default=20)
    parser.add_argument("--crop-mode", choices=["auto", "none", "borders", "bbox"], default="auto")
    parser.add_argument("--crop-ratio", type=float, default=0.15)
    parser.add_argument("--bbox", type=parse_bbox, default=(10, 50, 100, 100))
    parser.add_argument("--manual-start", type=parse_point)
    parser.add_argument("--manual-end", type=parse_point)
    parser.add_argument("--plot", action="store_true")
    parser.add_argument("--plot2d", action="store_true")
    parser.add_argument("--plot3d", action="store_true")
    parser.add_argument("--interactive", action="store_true")
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
        help="Optional CSV output path. Defaults to output/<filename>_profileFixer.csv",
    )
    return parser.parse_args(argv)



def build_interactive_args(initial: argparse.Namespace | None = None) -> argparse.Namespace:
    initial = initial or argparse.Namespace(dataset="fluized", filename=None)
    dataset = normalize_dataset_name(getattr(initial, "dataset", "fluized"))
    dataset_info = get_dataset_info(dataset)
    suffix = f".{dataset_info['file_type']}"
    filename = getattr(initial, "filename", None) or choose_filename_from_directory(get_dataset_dir(dataset), [suffix])
    ellipse_points = ask_int("Ellipse points", getattr(initial, "ellipse_points", 20))
    crop_mode = ask_choice(
        "Crop mode",
        {
            "auto": "Automatic crop",
            "borders": "Crop borders by ratio",
            "bbox": "Manual crop using bounding box",
            "none": "No crop",
        },
        default=getattr(initial, "crop_mode", "auto" if dataset != "quickmap" else "borders"),
    )
    crop_ratio = getattr(initial, "crop_ratio", 0.15)
    bbox = getattr(initial, "bbox", (10, 50, 100, 100))
    if crop_mode == "borders":
        crop_ratio = ask_float("Crop ratio", crop_ratio)
    elif crop_mode == "bbox":
        bbox = ask_bbox(bbox)
    manual_start = ask_optional_point("Manual profile start point x,y")
    manual_end = ask_optional_point("Manual profile end point x,y")
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

    default_output = OUTPUT_DIR / filename.replace(suffix, "_profileFixer.csv")
    output = Path(ask_text("Output CSV path", str(getattr(initial, "output", default_output))))

    return argparse.Namespace(
        dataset=dataset,
        filename=filename,
        ellipse_points=ellipse_points,
        crop_mode=crop_mode,
        crop_ratio=crop_ratio,
        bbox=bbox,
        manual_start=manual_start,
        manual_end=manual_end,
        plot=plot2d or plot3d,
        plot2d=plot2d,
        plot3d=plot3d,
        interactive=True,
        xres=xres,
        yres=yres,
        zres=zres,
        scale=scale,
        z_shift=z_shift,
        output=output,
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



def load_depth_map(args: argparse.Namespace) -> DepthMap:
    dataset = normalize_dataset_name(args.dataset)
    dataset_dir = get_dataset_dir(dataset)
    file_path = dataset_dir / args.filename
    if not file_path.exists():
        raise FileNotFoundError(f"Input file not found: {file_path}")

    if dataset == "quickmap":
        resolution = build_resolution(args)
        if resolution is None:
            raise ValueError("QuickMap profile fixing requires valid resolution values")
        depth_map = DepthMap.from_xyz_file(
            file_path.name,
            data_folder=str(dataset_dir),
            resolution=resolution,
            z_shift=args.z_shift,
        )
    else:
        depth_map = DepthMap.load(file_path)

    if args.crop_mode == "auto":
        depth_map.auto_crop()
    elif args.crop_mode == "borders":
        depth_map.crop_borders(args.crop_ratio)
    elif args.crop_mode == "bbox":
        depth_map.crop(args.bbox)
    return depth_map



def run_profile_fix(args: argparse.Namespace) -> Path:
    session_path = ensure_session_summary_path()
    append_session_note("profile fixer", "Started profile fixer run", dataset=normalize_dataset_name(args.dataset))
    print(f"Session summary: {session_path}")
    while True:
        try:
            depth_map = load_depth_map(args)
            ellipse_model = EllipticalModel(depth_map, args.ellipse_points)
            if args.manual_start and args.manual_end:
                profile = Profile(depth_map, start_point=args.manual_start, end_point=args.manual_end)
            else:
                profile = ellipse_model.max_profile()

            m1, m2 = profile.slopes()
            print(f"Computed slopes: m1={m1}, m2={m2}")

            if getattr(args, "plot2d", False) or getattr(args, "plot3d", False) or args.plot:
                show_review_figures(
                    depth_map=depth_map,
                    profile=profile,
                    ellipse_model=ellipse_model,
                    surface=None,
                    show_2d=getattr(args, "plot2d", False) or args.plot,
                    show_profile=True,
                    show_3d=getattr(args, "plot3d", False) or args.plot,
                    preview_scale=(1, 1, 4),
                )

            output_path = args.output or (OUTPUT_DIR / f"{args.filename.rsplit('.', 1)[0]}_profileFixer.csv")
            write_profile_csv(output_path, profile)
            log_path = append_fix_log(
                script_name="profile_fixer.py",
                dataset=normalize_dataset_name(args.dataset),
                filename=args.filename,
                parameters={
                    "ellipse_points": args.ellipse_points,
                    "crop_mode": args.crop_mode,
                    "bbox": getattr(args, "bbox", None),
                    "crop_ratio": getattr(args, "crop_ratio", None),
                    "manual_start": args.manual_start,
                    "manual_end": args.manual_end,
                    "z_shift": getattr(args, "z_shift", None),
                },
                observables={
                    "m1": m1,
                    "m2": m2,
                    "profile_points": len(profile.s),
                },
                output_path=output_path,
                notes=["Profile correction exported as distance-height CSV."],
            )
            print(f"Saved profile CSV to: {output_path}")
            print(f"Logged correction details to: {log_path}")
            append_session_entry(workflow="profile fixer", dataset=normalize_dataset_name(args.dataset), category="corrected", value=args.filename)
            append_session_entry(workflow="profile fixer", dataset=normalize_dataset_name(args.dataset), category="output", value=str(output_path))
            return output_path

        except Exception as exception:  # noqa: BLE001
            print_processing_error("profile fixer", args.filename or "<unknown>", exception)
            log_path = append_error_log(
                workflow="profile fixer",
                dataset=normalize_dataset_name(args.dataset),
                filename=args.filename or "<unknown>",
                exception=exception,
            )
            print(f"Logged error details to: {log_path}")
            append_session_entry(workflow="profile fixer", dataset=normalize_dataset_name(args.dataset), category="failed", value=args.filename or "<unknown>")
            if not getattr(args, "interactive", False):
                raise
            while True:
                action = ask_error_action(allow_fix=False, allow_edit=True, allow_skip=False, allow_stop=True, default="retry")
                if action == "details":
                    print(format_exception_text(exception))
                    continue
                if action == "edit":
                    args.ellipse_points = ask_int("Ellipse points", args.ellipse_points)
                    args.crop_mode = ask_choice(
                        "Crop mode",
                        {"auto": "Automatic crop", "borders": "Crop borders by ratio", "bbox": "Manual crop using bounding box", "none": "No crop"},
                        default=args.crop_mode,
                    )
                    if args.crop_mode == "borders":
                        args.crop_ratio = ask_float("Crop ratio", args.crop_ratio)
                    elif args.crop_mode == "bbox":
                        args.bbox = ask_bbox(args.bbox)
                    if normalize_dataset_name(args.dataset) == "quickmap":
                        args.xres = ask_float("X resolution", args.xres)
                        args.yres = ask_float("Y resolution", args.yres)
                        args.zres = ask_float("Z resolution", args.zres)
                        args.scale = ask_text("Scale units", args.scale)
                        args.z_shift = ask_float(
                            "Z shift (lunar geodesy vertical offset used to align the LROC/QuickMap zero level)",
                            args.z_shift,
                        )
                    args.manual_start = ask_optional_point("Manual profile start point x,y")
                    args.manual_end = ask_optional_point("Manual profile end point x,y")
                    plot_mode = ask_plot_mode(default="both" if args.plot2d and args.plot3d else "none")
                    args.plot2d, args.plot3d = plot_flags_from_mode(plot_mode)
                    args.plot = args.plot2d or args.plot3d
                    break
                if action == "retry":
                    break
                raise SystemExit(1)



def interactive_loop(initial_args: argparse.Namespace | None = None) -> None:
    args = build_interactive_args(initial_args)
    while True:
        run_profile_fix(args)
        if ask_yes_no("Are you satisfied with this profile", default=True):
            break
        print("\nLet's adjust the profile parameters.")
        args.ellipse_points = ask_int("Ellipse points", args.ellipse_points)
        args.crop_mode = ask_choice(
            "Crop mode",
            {
                "auto": "Automatic crop",
                "borders": "Crop borders by ratio",
                "bbox": "Manual crop using bounding box",
                "none": "No crop",
            },
            default=args.crop_mode,
        )
        if args.crop_mode == "borders":
            args.crop_ratio = ask_float("Crop ratio", args.crop_ratio)
        elif args.crop_mode == "bbox":
            args.bbox = ask_bbox(args.bbox)
        args.manual_start = ask_optional_point("Manual profile start point x,y")
        args.manual_end = ask_optional_point("Manual profile end point x,y")
        plot_mode = ask_plot_mode(default="both" if args.plot2d and args.plot3d else "none")
        args.plot2d, args.plot3d = plot_flags_from_mode(plot_mode)
        args.plot = args.plot2d or args.plot3d



def main() -> None:
    if len(sys.argv) > 1:
        args = parse_args()
        if args.interactive:
            interactive_loop(args)
        else:
            run_profile_fix(args)
    else:
        interactive_loop()


if __name__ == "__main__":
    main()
