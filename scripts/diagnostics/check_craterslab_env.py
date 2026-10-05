from __future__ import annotations

import argparse
import platform
import sys
import traceback
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[2]

PACKAGES = [
    "craterslab",
    "tensorflow",
    "keras",
    "numpy",
    "scipy",
    "matplotlib",
    "scikit-learn",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Diagnose import and runtime issues for craterslab across Python versions.",
    )
    parser.add_argument(
        "--sample-npz",
        type=Path,
        help="Optional .npz depth map to load with craterslab.",
    )
    parser.add_argument(
        "--sample-xyz",
        type=Path,
        help="Optional .xyz point cloud to load with craterslab.",
    )
    parser.add_argument("--xres", type=float, default=230.58527)
    parser.add_argument("--yres", type=float, default=230.58527)
    parser.add_argument("--zres", type=float, default=1.0)
    parser.add_argument("--scale", default="m")
    parser.add_argument(
        "--full-traceback",
        action="store_true",
        help="Print complete Python tracebacks when a check fails.",
    )
    return parser.parse_args()


def print_header() -> None:
    print("=" * 80)
    print("CRATERSLAB ENVIRONMENT DIAGNOSTIC")
    print("=" * 80)
    print(f"Python executable : {sys.executable}")
    print(f"Python version    : {sys.version}")
    print(f"Implementation    : {platform.python_implementation()}")
    print(f"Platform          : {platform.platform()}")
    print(f"Project root      : {PROJECT_ROOT}")
    print("=" * 80)


def print_versions() -> None:
    print("\nInstalled packages:")
    for package in PACKAGES:
        try:
            print(f"  - {package:<14} {version(package)}")
        except PackageNotFoundError:
            print(f"  - {package:<14} NOT INSTALLED")


def run_check(name: str, func, full_traceback: bool = False):
    try:
        result = func()
        message = f" -> {result}" if result not in (None, "") else ""
        print(f"[OK]   {name}{message}")
        return result
    except Exception as exc:  # noqa: BLE001
        print(f"[FAIL] {name} -> {type(exc).__name__}: {exc}")
        if full_traceback:
            traceback.print_exc()
        return None


def diagnose(args: argparse.Namespace) -> None:
    print("\nChecks:")

    def import_numpy():
        import numpy  # noqa: F401

        return f"numpy {np.__version__}"

    run_check("import numpy", import_numpy, args.full_traceback)

    def import_keras():
        import keras  # noqa: F401

        return f"keras {version('keras')}"

    run_check("import keras", import_keras, args.full_traceback)

    def import_tensorflow():
        import tensorflow as tf

        return f"tensorflow {tf.__version__}"

    run_check("import tensorflow", import_tensorflow, args.full_traceback)

    def import_craterslab():
        import craterslab  # noqa: F401

        return f"craterslab {version('craterslab')}"

    run_check("import craterslab", import_craterslab, args.full_traceback)

    def load_classifier_model():
        from craterslab.classification import get_trained_model

        model = get_trained_model()
        return f"model loaded={model is not None}"

    run_check("load classifier model", load_classifier_model, args.full_traceback)

    def import_core_objects():
        from craterslab.craters import Surface  # noqa: F401
        from craterslab.sensors import DepthMap, SensorResolution  # noqa: F401

        return "Surface, DepthMap, SensorResolution"

    run_check("import core objects", import_core_objects, args.full_traceback)

    def create_dummy_depth_map():
        from craterslab.sensors import DepthMap, SensorResolution

        dm = DepthMap(
            np.zeros((100, 100), dtype=float), SensorResolution(1.0, 1.0, 1.0, "mm")
        )
        return f"dummy depth map shape={dm.map.shape}"

    run_check("create dummy depth map", create_dummy_depth_map, args.full_traceback)

    if args.sample_npz:
        sample_npz = args.sample_npz.resolve()

        def load_npz_file():
            from craterslab.sensors import DepthMap

            dm = DepthMap.load(sample_npz)
            return f"loaded npz shape={dm.map.shape} from {sample_npz.name}"

        run_check(
            f"load sample npz ({sample_npz.name})", load_npz_file, args.full_traceback
        )

        def classify_npz_file():
            from craterslab.craters import Surface
            from craterslab.sensors import DepthMap

            dm = DepthMap.load(sample_npz)
            surface = Surface(dm)
            return f"classified as {surface.type} with {len(surface.observables)} observables"

        run_check(
            f"classify sample npz ({sample_npz.name})",
            classify_npz_file,
            args.full_traceback,
        )

    if args.sample_xyz:
        sample_xyz = args.sample_xyz.resolve()

        def load_xyz_file():
            from craterslab.sensors import DepthMap, SensorResolution

            resolution = SensorResolution(args.xres, args.yres, args.zres, args.scale)
            dm = DepthMap.from_xyz_file(
                sample_xyz.name,
                data_folder=str(sample_xyz.parent),
                resolution=resolution,
                z_shift=0,
            )
            return f"loaded xyz shape={dm.map.shape} from {sample_xyz.name}"

        run_check(
            f"load sample xyz ({sample_xyz.name})", load_xyz_file, args.full_traceback
        )

    print("\nRecommendations:")
    print("  - Stable baseline for this project: Python 3.11.x")
    print(
        "  - For Python 3.12 use a clean venv and install compatible versions together"
    )
    print("  - Suggested stack: craterslab>=0.2.8, keras>=3, tensorflow>=2.16.1")


if __name__ == "__main__":
    arguments = parse_args()
    print_header()
    print_versions()
    diagnose(arguments)
