from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"
DOCS_DIR = PROJECT_ROOT / "docs"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"

DATASET_INFO = {
    "fluized": {
        "label": "Fluidized laboratory data",
        "dir": DATA_DIR / "data_Fluized",
        "file_type": "npz",
        "default_prefix": "fluized",
    },
    "compacted": {
        "label": "Compacted laboratory data",
        "dir": DATA_DIR / "data_Compacted",
        "file_type": "npz",
        "default_prefix": "compacted",
    },
    "quickmap": {
        "label": "QuickMap / LROC point-cloud data",
        "dir": DATA_DIR / "data_QuickMap",
        "file_type": "xyz",
        "default_prefix": "depthMap",
        "default_resolution": {
            "xres": 230.58527,
            "yres": 230.58527,
            "zres": 1.0,
            "scale": "m",
        },
    },
    "train_classifier_2_0": {
        "label": "Classifier training data",
        "dir": DATA_DIR / "data_train_classifier_2.0",
        "file_type": "npz",
        "default_prefix": "",
    },
}

DATASET_ALIASES = {
    "fluidized": "fluized",
    "fluized": "fluized",
    "compacted": "compacted",
    "quickmap": "quickmap",
    "lroc": "quickmap",
    "train_classifier_2.0": "train_classifier_2_0",
    "train_classifier_2_0": "train_classifier_2_0",
}


def normalize_dataset_name(name: str) -> str:
    key = name.strip().lower()
    if key not in DATASET_ALIASES:
        available = ", ".join(sorted(DATASET_INFO))
        raise KeyError(f"Unknown dataset '{name}'. Available datasets: {available}")
    return DATASET_ALIASES[key]


def ensure_directory(path: Path | str) -> Path:
    directory = Path(path)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def get_dataset_dir(name: str) -> Path:
    return DATASET_INFO[normalize_dataset_name(name)]["dir"]


def get_dataset_info(name: str) -> dict:
    return DATASET_INFO[normalize_dataset_name(name)]
