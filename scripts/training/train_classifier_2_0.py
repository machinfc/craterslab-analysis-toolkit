from __future__ import annotations

import argparse
import random
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
from keras.utils import to_categorical
from sklearn.model_selection import train_test_split

from craterslab.classification import (
    NUM_CLASSES,
    get_trained_model,
    get_untrained_model,
    normalize,
    save_trained_model,
)
from craterslab.sensors import DepthMap
from toolkit.paths import get_dataset_dir

SIMPLE_INDICES = [1, 2, 3, 4, 5, 6, 7, 8, 26, 27, 29, 31, 35, 42, 43, 48, 49, 51]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Train the Craterslab surface classifier on NPZ crater maps.",
    )
    parser.add_argument("--epochs", type=int, default=4)
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--learning-rate", type=float, default=0.0001)
    parser.add_argument("--test-size", type=float, default=0.1)
    parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args()


def regularize(dm: DepthMap) -> DepthMap:
    cropping_coin = random.random()
    if cropping_coin < 0.25:
        dm.crop_borders(ratio=cropping_coin)
    elif cropping_coin < 0.90:
        dm.auto_crop()
    if random.random() > 0.5:
        dm.map = dm.map.T
    return dm


def main() -> None:
    args = parse_args()
    random.seed(args.seed)
    np.random.seed(args.seed)

    training_dir = get_dataset_dir("train_classifier_2_0")

    categories = {
        "empty": {
            "files": [f"plane_{i}.npz" for i in range(1, 17)],
            "id": 0,
        },
        "simple_craters": {
            "files": [f"fluized_{i}.npz" for i in SIMPLE_INDICES],
            "id": 1,
        },
        "complex_craters": {
            "files": [f"fluized_{i}.npz" for i in range(1, 52) if i not in SIMPLE_INDICES]
            + [f"compacted_{i}.npz" for i in range(25, 50)],
            "id": 2,
        },
        "sand_mounds": {
            "files": [f"compacted_{i}.npz" for i in range(1, 25)],
            "id": 3,
        },
    }

    images = []
    labels = []
    for details in categories.values():
        for file_name in details["files"]:
            path = training_dir / file_name
            if not path.exists():
                raise FileNotFoundError(f"Training file not found: {path}")
            dm = DepthMap.load(path)
            if details["id"]:
                dm = regularize(dm)
            img = normalize(dm.map, expand=False)
            images.append(img)
            labels.append(details["id"])

    images = np.expand_dims(np.array(images), axis=-1)
    labels = to_categorical(np.array(labels), num_classes=NUM_CLASSES)

    train_images, test_images, train_labels, test_labels = train_test_split(
        images,
        labels,
        test_size=args.test_size,
        random_state=args.seed,
    )

    model = get_untrained_model(lr=args.learning_rate)
    model.fit(
        train_images,
        train_labels,
        epochs=args.epochs,
        batch_size=args.batch_size,
    )
    save_trained_model(model)

    model = get_trained_model()
    test_loss, test_acc = model.evaluate(test_images, test_labels)
    print(f"Test loss: {test_loss}")
    print(f"Test accuracy: {test_acc}")


if __name__ == "__main__":
    main()
