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
from toolkit.exporters import build_observable_row, write_observables_csv
from toolkit.interactive import ask_bbox, ask_choice, ask_dataset, ask_float, ask_text, ask_yes_no, choose_filename_from_directory
from toolkit.paths import OUTPUT_DIR, get_dataset_dir, get_dataset_info, normalize_dataset_name

ALL_OBSERVABLES = ["D", "d_max", "V_in", "V_ex", "V_exc", "epsilon", "V_cp", "H_cp"]
DEFAULT_CORRECTIONS = [
    ("compacted_41.npz", SurfaceType.COMPLEX_CRATER),
    ("compacted_43.npz", SurfaceType.COMPLEX_CRATER),
    ("compacted_47.npz", SurfaceType.COMPLEX_CRATER),
]
SURFACE_TYPE_OPTIONS = {
    "simple_crater": SurfaceType.SIMPLE_CRATER,
    "complex_crater": SurfaceType.COMPLEX_CRATER,
    "sand_mound": SurfaceType.SAND_MOUND,
    "unknown": SurfaceType.UNKNOWN,
}


def parse_bbox(value: str) -> tuple[int, int, int, int]:
    parts = [int(part.strip()) for part in value.split(",")]
    if len(parts) != 4:
        raise argparse.ArgumentTypeError("Bounding box must contain 4 integers: x,y,w,h")
    return tuple(parts)  # type: ignore[return-value]



def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fix mislabeled surface types for one or more crater files.",
    )
    parser.add_argument("--dataset", default="compacted")
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--skip-missing", action="store_true")
    parser.add_argument("--crop-mode", choices=["auto", "bbox", "borders", "none"], default="auto")
    parser.add_argument("--crop-ratio", type=float, default=0.15)
    parser.add_argument("--bbox", type=parse_bbox, default=(10, 50, 100, 100))
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



def build_interactive_args() -> argparse.Namespace:
    dataset = ask_dataset(default="compacted")
    crop_mode = ask_choice(
        "Crop mode",
        {
            "auto": "Automatic crop",
            "bbox": "Manual crop using bounding box",
            "borders": "Crop borders by ratio",
            "none": "No crop",
        },
        default="auto",
    )
    crop_ratio = 0.15
    bbox = (10, 50, 100, 100)
    if crop_mode == "bbox":
        bbox = ask_bbox(bbox)
    elif crop_mode == "borders":
        crop_ratio = ask_float("Crop ratio", crop_ratio)

    output = Path(ask_text("Output CSV path", str(OUTPUT_DIR / f"{dataset}_obsv_surface_type.csv")))
    xres = yres = zres = None
    scale = None
    z_shift = 0.0
    if dataset == "quickmap":
        defaults = get_dataset_info(dataset)["default_resolution"]
        xres = ask_float("X resolution", defaults["xres"])
        yres = ask_float("Y resolution", defaults["yres"])
        zres = ask_float("Z resolution", defaults["zres"])
        scale = ask_text("Scale units", defaults["scale"])
        z_shift = ask_float(
            "Z shift (lunar geodesy vertical offset used to align the LROC/QuickMap zero level)",
            0.0,
        )
    return argparse.Namespace(
        dataset=dataset,
        output=output,
        skip_missing=True,
        crop_mode=crop_mode,
        crop_ratio=crop_ratio,
        bbox=bbox,
        xres=xres,
        yres=yres,
        zres=zres,
        scale=scale,
        z_shift=z_shift,
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



def collect_corrections_interactively(dataset: str) -> list[tuple[str, SurfaceType]]:
    dataset_info = get_dataset_info(dataset)
    suffix = f".{dataset_info['file_type']}"
    corrections: list[tuple[str, SurfaceType]] = []
    while True:
        filename = choose_filename_from_directory(get_dataset_dir(dataset), [suffix])
        surface_key = ask_choice(
            "Select corrected surface type",
            {key: value.name.replace("_", " ").title() for key, value in SURFACE_TYPE_OPTIONS.items()},
            default="complex_crater",
        )
        corrections.append((filename, SURFACE_TYPE_OPTIONS[surface_key]))
        if not ask_yes_no("Add another file to this batch", default=False):
            break
    return corrections



def apply_crop(depth_map: DepthMap, args: argparse.Namespace) -> None:
    if args.crop_mode == "auto":
        depth_map.auto_crop()
    elif args.crop_mode == "borders":
        depth_map.crop_borders(args.crop_ratio)
    elif args.crop_mode == "bbox":
        depth_map.crop(args.bbox)



def run_fix(args: argparse.Namespace, corrections: list[tuple[str, SurfaceType]]) -> Path:
    dataset = normalize_dataset_name(args.dataset)
    dataset_dir = get_dataset_dir(dataset)
    resolution = build_resolution(args)
    rows: list[list[object]] = []

    for filename, surface_type in corrections:
        file_path = dataset_dir / filename
        if not file_path.exists():
            message = f"Input file not found: {file_path}"
            if args.skip_missing:
                print(f"[WARN] {message}")
                continue
            raise FileNotFoundError(message)

        print(f"Fixing {filename} -> {surface_type}")
        if dataset == "quickmap":
            if resolution is None:
                raise ValueError("QuickMap surface fixing requires valid resolution values")
            print("Using z_shift to correct the lunar geodetic zero reference in the imported LROC/QuickMap data.")
            depth_map = DepthMap.from_xyz_file(file_path.name, data_folder=str(dataset_dir), resolution=resolution, z_shift=args.z_shift)
        else:
            depth_map = DepthMap.load(file_path)
        apply_crop(depth_map, args)
        surface = Surface(depth_map)
        surface.set_type(surface_type)
        rows.append(build_observable_row(filename, surface, ALL_OBSERVABLES))

    output_path = args.output or (OUTPUT_DIR / f"{dataset}_obsv_surface_type.csv")
    output_path = write_observables_csv(output_path, ALL_OBSERVABLES, rows)
    print(f"Saved corrected observables to: {output_path}")
    return output_path



def main() -> None:
    if len(sys.argv) > 1:
        args = parse_args()
        corrections = DEFAULT_CORRECTIONS if normalize_dataset_name(args.dataset) == "compacted" else []
        if not corrections:
            print("No built-in correction list for this dataset. Use interactive mode instead.")
            return
        run_fix(args, corrections)
    else:
        args = build_interactive_args()
        corrections = collect_corrections_interactively(args.dataset)
        run_fix(args, corrections)


if __name__ == "__main__":
    main()
