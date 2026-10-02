# Workflow Examples

This document provides practical examples of common repository workflows.

All examples assume that:

- you are located at the repository root,
- the virtual environment is activated,
- the expected datasets are already placed under `data/`.

---

## 1. Start from the central launcher

The recommended entry point for most users is:

```bash
python main.py
```

This opens the central interactive menu and lets you choose between:

- analysis,
- visual review,
- fixing,
- acquisition,
- diagnostics,
- slope calculation,
- classifier training.

---

## 2. Analyze all files from the Fluidized dataset

### Interactive mode

```bash
python scripts/analysis/data_analyzer.py
```

Suggested choices:

- dataset: `fluized`
- processing mode: `all`
- file prefix: `fluized`
- crop mode: `auto`
- visualization: `2D and 3D` or `none`

At the end of the run, the analyzer can optionally:

- export a CSV of observables,
- ask whether to overwrite an existing CSV,
- offer interactive plots between selected observables.

### Direct mode

```bash
python scripts/analysis/data_analyzer.py --dataset fluized --mode all --prefix fluized
```

---

## 3. Analyze a range from the Compacted dataset

### Interactive mode

```bash
python scripts/analysis/data_analyzer.py
```

Suggested choices:

- dataset: `compacted`
- processing mode: `range`
- file prefix: `compacted`
- start: `25`
- end: `49`

### Direct mode

```bash
python scripts/analysis/data_analyzer.py --dataset compacted --mode range --start 25 --end 49
```

---

## 4. Analyze a single QuickMap / LROC file

### Interactive mode

```bash
python scripts/analysis/data_analyzer.py
```

Suggested choices:

- dataset: `quickmap`
- processing mode: `single`
- choose one `.xyz` file
- provide `xres`, `yres`, `zres`, `scale`
- provide `z_shift`

### Direct mode

```bash
python scripts/analysis/data_analyzer.py \
  --dataset quickmap \
  --mode single \
  --filename depthMap_2.xyz \
  --xres 230.58527 --yres 230.58527 --zres 1.0 --scale m \
  --z-shift 0.0
```

### Why `z_shift` matters

In QuickMap / LROC workflows, `z_shift` is used as a vertical offset to align the imported topography with the intended lunar geodetic zero reference.

---

## 5. Analyze and open the fixer during review

The analyzer can now be used as a review workflow.

### Interactive mode

```bash
python scripts/analysis/data_analyzer.py
```

If visualization is enabled, after each reviewed file you may choose:

- `repeat`
- `fix`
- `continue`
- `exit`

If you choose `fix`, the repository opens the general fixer workflow for that same file.

This is useful when a crater needs immediate intervention after visual inspection.

---

## 6. Use the general fixer on a single file

### Interactive mode

```bash
python scripts/fixes/ellipse_fixer.py
```

Suggested choices:

- dataset
- processing mode: `single`
- file name
- corrected `SurfaceType`
- ellipse points
- crop mode (`bbox`, `auto`, `borders`, `none`)
- visual review mode

You can then iteratively adjust the parameters until the result is acceptable.

### Direct mode

```bash
python scripts/fixes/ellipse_fixer.py \
  --dataset compacted \
  --mode single \
  --filename compacted_48.npz \
  --surface-type COMPLEX_CRATER \
  --ellipse-points 20 \
  --crop-mode bbox \
  --bbox 10,50,100,100 \
  --plot2d --plot3d
```

---

## 7. Use the general fixer on all matching files

### Interactive mode

```bash
python scripts/fixes/ellipse_fixer.py
```

Suggested choices:

- dataset
- processing mode: `all`
- file prefix
- default fixing parameters

The workflow will iterate through files one by one. For each file, the user can refine the correction interactively before accepting it.

### Direct mode

```bash
python scripts/fixes/ellipse_fixer.py --dataset fluized --mode all --prefix fluized
```

---

## 8. Apply manual crop with `bbox`

When a crater is poorly framed, select crop mode `bbox` and provide:

```text
x, y, width, height
```

Example:

```text
10,50,100,100
```

This is useful when automatic cropping does not isolate the crater correctly.

---

## 9. Review a crater visually before fixing it

### Interactive mode

```bash
python scripts/visualization/depth_map_visualizer.py
```

Suggested choices:

- dataset
- mode: `single`, `range`, or `all`
- visualizer mode: `2D`, `profile`, `3D`, or combined

After each file, choose:

- `repeat` to inspect again,
- `fix` to open the general fixer,
- `continue` to move on,
- `exit` to stop.

---

## 10. Capture a new depth map from the sensor workflow

### Interactive mode

```bash
python scripts/acquisition/depth_map_fetcher.py
```

The current acquisition workflow asks whether you want to:

- capture the plane depth map,
- capture the impact depth map,
- save the resulting depth map,
- optionally save intermediate captures.

This workflow is included in the repository now so that it can be further refined later.

---

## 11. Plot observables against each other after analysis

At the end of an analyzer workflow, the user can optionally open an interactive scatter-plot workflow.

Typical use cases:

- `D` vs `d_max`
- `V_in` vs `V_ex`
- `epsilon` vs `D`

This is useful for comparing crater populations after exporting observables.

---

## 12. Diagnose environment problems before running real data

```bash
python scripts/diagnostics/check_craterslab_env.py --full-traceback
```

With a real file:

```bash
python scripts/diagnostics/check_craterslab_env.py \
  --sample-npz data/data_Fluized/fluized_1.npz \
  --full-traceback
```

QuickMap example:

```bash
python scripts/diagnostics/check_craterslab_env.py \
  --sample-xyz data/data_QuickMap/depthMap_2.xyz \
  --xres 230.58527 --yres 230.58527 --zres 1.0 --scale m \
  --full-traceback
```

---

## 13. Recommended user progression

For new users, a good sequence is:

1. run the environment diagnostic,
2. test one file with the visualizer,
3. test one file with the analyzer,
4. test the general fixer on a single file,
5. scale up to ranges or complete datasets.


---

## 14. Capture a crater with Femto Bolt

Install the optional sensor package first:

```bash
pip install pyorbbecsdk2
```

Then run:

```bash
python scripts/acquisition/depth_map_fetcher.py
```

Suggested choices:

- sensor: `femto_bolt`
- protocol: `plane_impact`
- ROI: `full` or `bbox`
- average frames: according to your experimental stability

This workflow captures the flat surface first, then the impacted surface, subtracts both maps, and saves an `.npz` file compatible with the rest of the toolkit.
