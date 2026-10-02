# Dataset Preparation Guide

This document explains how to prepare and organize input data for the repository.

---

## 1. Expected directory structure

The repository expects datasets under:

```text
data/
├── data_Fluized/
├── data_Compacted/
├── data_QuickMap/
└── data_train_classifier_2.0/
```

If these directories are respected, the toolkit can usually find files automatically.

---

## 2. Supported file types

### Laboratory datasets

Expected file type:

- `.npz`

Typical folders:

- `data/data_Fluized/`
- `data/data_Compacted/`

### QuickMap / LROC datasets

Expected file type:

- `.xyz`

Typical folder:

- `data/data_QuickMap/`

### Classifier training datasets

Expected file type:

- `.npz`

Typical folder:

- `data/data_train_classifier_2.0/`

---

## 3. Naming conventions

Most batch workflows assume names such as:

### Fluidized / Fluized

- `fluized_1.npz`
- `fluized_2.npz`
- `fluized_3.npz`

### Compacted

- `compacted_1.npz`
- `compacted_2.npz`
- `compacted_48.npz`

### QuickMap / LROC

- `depthMap_1.xyz`
- `depthMap_2.xyz`

### Classifier training support files

- `plane_1.npz`
- `plane_2.npz`
- `fluized_1.npz`
- `compacted_25.npz`

---

## 4. What if my file names are different?

If your files use a different naming pattern, you have three main options:

1. rename the files to match the expected conventions,
2. run workflows in **single-file mode** and choose the file interactively,
3. specify an explicit file prefix where supported.

---

## 5. Notes for QuickMap / LROC data

QuickMap / LROC workflows require additional numeric parameters:

- `xres`
- `yres`
- `zres`
- `scale`
- `z_shift`

### About `z_shift`

`z_shift` is used as a vertical offset to align the imported data with the intended lunar geodetic zero reference.

Users should treat this as a scientifically relevant preprocessing parameter rather than an arbitrary technical option.

---

## 6. Notes for crop behavior

The repository supports multiple crop modes in analysis and fixing workflows:

- `auto`
- `borders`
- `bbox`
- `none`

### `bbox`

`bbox` means a manual crop by bounding box:

```text
x, y, width, height
```

This is especially useful when automatic crop behavior does not isolate the crater correctly.

---

## 7. Recommendations before batch processing

Before processing an entire dataset:

1. run the environment diagnostic,
2. inspect one sample visually,
3. confirm crop behavior,
4. confirm the selected `z_shift` if using QuickMap / LROC,
5. test analyzer and fixer workflows on a single file first.

---

## 8. GitHub data policy recommendation

Large datasets should generally not be committed directly into the repository unless you intentionally manage them with:

- Git LFS,
- a reduced example dataset,
- an external distribution source.

A common best practice is:

- keep the code repository lightweight,
- keep the raw or heavy datasets in a dedicated archive or companion repository.
