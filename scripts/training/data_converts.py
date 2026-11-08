from __future__ import annotations

from pathlib import Path

from craterslab.depth_map import SensorResolution
from craterslab.readers import read_mat

PROJECT_ROOT = Path(__file__).resolve().parents[2]
INPUT_FOLDER = PROJECT_ROOT / "data_CAGEO" / "matlab_ALL.CAGEO"
OUTPUT_FOLDER = PROJECT_ROOT / "data_CAGEO"
FILE_RANGE = range(1, 38)
RESOLUTION = SensorResolution(2.8025, 2.8025, 1, "mm")



def main() -> None:
    OUTPUT_FOLDER.mkdir(parents=True, exist_ok=True)

    for index in FILE_RANGE:
        d0 = read_mat(
            INPUT_FOLDER / f"planoexp{index}.mat",
            resolution=RESOLUTION,
        )
        df = read_mat(
            INPUT_FOLDER / f"craterexp{index}.mat",
            resolution=RESOLUTION,
        )
        depth_map = d0 - df
        output_path = OUTPUT_FOLDER / f"CAGEO_{index}.npz"
        depth_map.save(output_path)
        print(f"Saved: {output_path}")


if __name__ == "__main__":
    main()
