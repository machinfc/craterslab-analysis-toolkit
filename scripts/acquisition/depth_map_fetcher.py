from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import numpy as np
from craterslab.sensors import DepthMap, SensorResolution

from toolkit.error_handling import (
    append_error_log,
    ask_error_action,
    format_exception_text,
    print_processing_error,
)
from toolkit.interactive import (
    ask_bbox,
    ask_choice,
    ask_float,
    ask_int,
    ask_text,
    ask_yes_no,
)
from toolkit.paths import OUTPUT_DIR, ensure_directory
from toolkit.session_summary import (
    append_session_entry,
    append_session_note,
    ensure_session_summary_path,
)
from toolkit.visualization_helpers import show_review_figures

PROJECT_ROOT = Path(__file__).resolve().parents[2]

SENSOR_OPTIONS = {
    "kinect": "Kinect via craterslab",
    "femto_bolt": "Orbbec Femto Bolt via pyorbbecsdk / pyorbbecsdk2",
}

PROTOCOL_OPTIONS = {
    "plane_impact": "Plane capture + impact capture + subtraction (recommended)",
    "impact_only": "Impact-only capture (faster, but less robust)",
}

ROI_OPTIONS = {
    "full": "Use the full depth frame",
    "bbox": "Use a manual crop (x,y,w,h)",
}


def parse_bbox(value: str) -> tuple[int, int, int, int]:
    parts = [int(part.strip()) for part in value.split(",")]
    if len(parts) != 4:
        raise argparse.ArgumentTypeError(
            "Bounding box must contain 4 integers: x,y,w,h"
        )
    return tuple(parts)  # type: ignore[return-value]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Capture crater depth maps from Kinect or Femto Bolt."
    )
    parser.add_argument("--sensor", choices=list(SENSOR_OPTIONS), default="kinect")
    parser.add_argument(
        "--protocol", choices=list(PROTOCOL_OPTIONS), default="plane_impact"
    )
    parser.add_argument("--average-on", type=int, default=500)
    parser.add_argument("--frame-timeout-ms", type=int, default=1000)
    parser.add_argument("--xres", type=float, default=2.8025)
    parser.add_argument("--yres", type=float, default=2.8025)
    parser.add_argument("--zres", type=float, default=1.0)
    parser.add_argument("--scale", default="mm")
    parser.add_argument("--index", type=int, default=1)
    parser.add_argument("--save-intermediate", action="store_true")
    parser.add_argument("--roi-mode", choices=list(ROI_OPTIONS), default="full")
    parser.add_argument("--bbox", type=parse_bbox, default=None)
    return parser.parse_args(argv)


def build_interactive_args() -> argparse.Namespace:
    sensor = ask_choice("Depth sensor", SENSOR_OPTIONS, default="kinect")
    protocol = ask_choice("Capture protocol", PROTOCOL_OPTIONS, default="plane_impact")
    roi_mode = ask_choice("Area to capture", ROI_OPTIONS, default="full")
    bbox = ask_bbox((100, 100, 300, 300)) if roi_mode == "bbox" else None

    print("\nNote:")
    print("- Kinect works through craterslab directly.")
    print(
        "- Femto Bolt requires the Orbbec Python SDK (`pyorbbecsdk` or `pyorbbecsdk2`)."
    )
    print(
        "- Femto Bolt measurements should be recalibrated experimentally before scientific use."
    )
    if protocol == "impact_only":
        print(
            "- Impact-only mode can be useful for quick checks, but it keeps more geometric bias than plane-impact subtraction."
        )

    return argparse.Namespace(
        sensor=sensor,
        protocol=protocol,
        average_on=ask_int("Average frames", 500),
        frame_timeout_ms=ask_int("Frame timeout (ms)", 1000),
        xres=ask_float("X resolution", 2.8025),
        yres=ask_float("Y resolution", 2.8025),
        zres=ask_float("Z resolution", 1.0),
        scale=ask_text("Scale units", "mm"),
        index=ask_int("Output index", 1),
        save_intermediate=ask_yes_no(
            "Save plane and impact maps separately", default=False
        ),
        roi_mode=roi_mode,
        bbox=bbox,
        interactive=True,
    )


def import_orbbec_sdk() -> Any:
    try:
        import pyorbbecsdk2 as obs

        return obs
    except ModuleNotFoundError:
        try:
            import pyorbbecsdk as obs

            return obs
        except ModuleNotFoundError as exc:
            raise ModuleNotFoundError(
                "Femto Bolt support requires `pyorbbecsdk2` or `pyorbbecsdk`. "
                "Install one of them in the active environment before using sensor=femto_bolt."
            ) from exc


def average_nonzero_depth(frames: list[np.ndarray]) -> np.ndarray:
    if not frames:
        raise RuntimeError("No valid depth frames were captured")
    stack = np.stack(frames, axis=0).astype(np.float32)
    valid = stack > 0
    count = np.sum(valid, axis=0)
    summed = np.sum(np.where(valid, stack, 0.0), axis=0)
    result = np.zeros_like(summed, dtype=np.float32)
    np.divide(summed, count, out=result, where=count > 0)
    return result


def extract_orbbec_depth_array(depth_frame: Any) -> np.ndarray:
    width = depth_frame.get_width()
    height = depth_frame.get_height()
    raw = (
        np.frombuffer(depth_frame.get_data(), dtype=np.uint16)
        .reshape((height, width))
        .astype(np.float32)
    )

    scale = 1.0
    if hasattr(depth_frame, "get_depth_scale"):
        scale = float(depth_frame.get_depth_scale())
    elif hasattr(depth_frame, "get_value_scale"):
        scale = float(depth_frame.get_value_scale())

    return raw * scale


def capture_femto_bolt_depth_map(
    resolution: SensorResolution, average_on: int, timeout_ms: int
) -> DepthMap:
    obs = import_orbbec_sdk()
    pipeline = obs.Pipeline()
    config = obs.Config()

    profile_list = pipeline.get_stream_profile_list(obs.OBSensorType.DEPTH_SENSOR)
    depth_profile = profile_list.get_default_video_stream_profile()
    config.enable_stream(depth_profile)

    if hasattr(pipeline, "enable_frame_sync"):
        try:
            pipeline.enable_frame_sync()
        except Exception:
            pass

    captured_frames: list[np.ndarray] = []
    try:
        pipeline.start(config)
        while len(captured_frames) < average_on:
            frames = pipeline.wait_for_frames(timeout_ms)
            if frames is None:
                continue
            depth_frame = frames.get_depth_frame()
            if depth_frame is None:
                continue
            captured_frames.append(extract_orbbec_depth_array(depth_frame))
    finally:
        try:
            pipeline.stop()
        except Exception:
            pass

    averaged = average_nonzero_depth(captured_frames)
    return DepthMap(averaged, resolution)


def capture_single_depth_map(
    sensor: str, resolution: SensorResolution, average_on: int, timeout_ms: int
) -> DepthMap:
    if sensor == "kinect":
        return DepthMap.from_kinect_sensor(resolution, average_on=average_on)
    if sensor == "femto_bolt":
        return capture_femto_bolt_depth_map(
            resolution, average_on=average_on, timeout_ms=timeout_ms
        )
    raise ValueError(f"Unsupported sensor: {sensor}")


def apply_roi(
    depth_map: DepthMap, roi_mode: str, bbox: tuple[int, int, int, int] | None
) -> DepthMap:
    if roi_mode == "bbox":
        if bbox is None:
            raise ValueError("ROI mode bbox requires a bounding box")
        depth_map.crop(bbox)
    return depth_map


def capture_depth_map_pair(args: argparse.Namespace):
    resolution = SensorResolution(args.xres, args.yres, args.zres, args.scale)

    if args.protocol == "plane_impact":
        if not ask_yes_no("Ready to capture the plane depth map", default=True):
            print("Cancelled before capturing the plane depth map.")
            return None
        plane = capture_single_depth_map(
            args.sensor, resolution, args.average_on, args.frame_timeout_ms
        )
        plane = apply_roi(plane, args.roi_mode, args.bbox)

        if not ask_yes_no("Ready to capture the impact depth map", default=True):
            print("Cancelled before capturing the impact depth map.")
            return None
        impact = capture_single_depth_map(
            args.sensor, resolution, args.average_on, args.frame_timeout_ms
        )
        impact = apply_roi(impact, args.roi_mode, args.bbox)
        return plane, impact

    print(
        "Using impact-only capture. This is faster but less robust than plane-impact subtraction."
    )
    if not ask_yes_no("Ready to capture the impact depth map", default=True):
        print("Cancelled before capturing the impact depth map.")
        return None
    impact = capture_single_depth_map(
        args.sensor, resolution, args.average_on, args.frame_timeout_ms
    )
    impact = apply_roi(impact, args.roi_mode, args.bbox)
    return None, impact


def edit_fetcher_args(args: argparse.Namespace) -> None:
    args.sensor = ask_choice("Depth sensor", SENSOR_OPTIONS, default=args.sensor)
    args.protocol = ask_choice(
        "Capture protocol", PROTOCOL_OPTIONS, default=args.protocol
    )
    args.average_on = ask_int("Average frames", args.average_on)
    args.frame_timeout_ms = ask_int("Frame timeout (ms)", args.frame_timeout_ms)
    args.xres = ask_float("X resolution", args.xres)
    args.yres = ask_float("Y resolution", args.yres)
    args.zres = ask_float("Z resolution", args.zres)
    args.scale = ask_text("Scale units", args.scale)
    args.index = ask_int("Output index", args.index)
    args.save_intermediate = ask_yes_no(
        "Save plane and impact maps separately", default=args.save_intermediate
    )
    args.roi_mode = ask_choice("Area to capture", ROI_OPTIONS, default=args.roi_mode)
    args.bbox = (
        ask_bbox(args.bbox or (100, 100, 300, 300)) if args.roi_mode == "bbox" else None
    )


def run_fetcher(args: argparse.Namespace) -> Path | None:
    while True:
        try:
            result = capture_depth_map_pair(args)
            if result is None:
                return None
            plane, impact = result
            depth_map = impact - plane if plane is not None else impact

            show_review_figures(
                depth_map=depth_map,
                profile=None,
                ellipse_model=None,
                surface=None,
                show_2d=False,
                show_profile=False,
                show_3d=True,
                preview_scale=(1, 1, 4),
            )

            output_dir = ensure_directory(OUTPUT_DIR / "depth_maps")
            if args.save_intermediate:
                if plane is not None:
                    plane.save(output_dir / f"plane_{args.index}.npz")
                impact.save(output_dir / f"impact_{args.index}.npz")
            output_path = output_dir / f"depthMap_{args.index}.npz"
            depth_map.save(output_path)
            append_session_entry(
                workflow="fetcher",
                dataset=args.sensor,
                category="output",
                value=str(output_path),
            )
            print(f"Saved result to: {output_path}")
            return output_path

        except Exception as exception:  # noqa: BLE001
            print_processing_error(
                "depth map fetcher", f"depthMap_{args.index}", exception
            )
            log_path = append_error_log(
                workflow="depth map fetcher",
                dataset=args.sensor,
                filename=f"depthMap_{args.index}",
                exception=exception,
            )
            print(f"Logged error details to: {log_path}")
            append_session_entry(
                workflow="fetcher",
                dataset=args.sensor,
                category="failed",
                value=f"depthMap_{args.index}",
            )
            if not getattr(args, "interactive", False):
                raise
            while True:
                action = ask_error_action(
                    allow_edit=True, allow_skip=False, allow_stop=True, default="retry"
                )
                if action == "details":
                    print(format_exception_text(exception))
                    continue
                if action == "edit":
                    edit_fetcher_args(args)
                    break
                if action == "retry":
                    break
                return None


def main() -> None:
    args = parse_args() if len(sys.argv) > 1 else build_interactive_args()
    session_path = ensure_session_summary_path()
    append_session_note(
        "fetcher",
        f"Started sensor capture workflow ({args.sensor}, {args.protocol})",
        dataset=args.sensor,
    )
    print(f"Session summary: {session_path}")
    run_fetcher(args)


if __name__ == "__main__":
    main()
