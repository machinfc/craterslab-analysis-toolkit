# Usage Guide

This guide answers one simple question:

**What do I want to do now?**

---

## Start here

If I am starting fresh, I run:

```bash
python main.py
```

That opens the central menu.

---

## I want to analyze crater data

Run:

```bash
python scripts/analysis/data_analyzer.py
```

Use this for:

- all matching files,
- one file,
- a numeric range,
- laboratory `.npz` data,
- QuickMap / LROC `.xyz` data.

At the end, I can also plot observables against each other.

If a file fails, the analyzer:

- prints the problem,
- logs the error,
- lets me inspect the traceback,
- lets me edit quick parameters before retrying,
- and lets me retry, skip, stop, or open the fixer.

---

## I want to review crater files visually

Run:

```bash
python scripts/visualization/depth_map_visualizer.py
```

This can show:

- 2D crater map,
- profile plot,
- 3D crater view.

For each file, the selected views open together.

After reviewing a file, I can:

- repeat,
- open the fixer,
- continue,
- exit.

If a file fails, the visualizer prints the error, logs it, and lets me retry, edit parameters, skip, or stop. At the end of the batch, it can reopen only the problematic files.

---

## I want to fix crater geometry or classification

Run:

```bash
python scripts/fixes/ellipse_fixer.py
```

This is the main fixer.

I can change:

- `SurfaceType`,
- ellipse points,
- crop mode,
- manual crop (`bbox`),
- crop ratio,
- QuickMap `z_shift`.

The fixer exports corrected observables and logs the correction.

If the result is not satisfactory, I can change parameters and immediately visualize the updated result.

If a file fails, the fixer prints the error, logs it, and lets me retry or edit parameters, including dataset-specific values for QuickMap workflows. At the end of the batch, it can reopen only the problematic files.

---

## I want to capture a new depth map from a sensor

Run:

```bash
python scripts/acquisition/depth_map_fetcher.py
```

This workflow can use:

- Kinect
- Femto Bolt

It supports:

- plane + impact subtraction (recommended)
- impact-only capture
- full frame or manual `bbox` crop

If capture fails, it prints the error, logs it, and lets me retry or edit capture parameters.

See also:

- [`sensor-acquisition.md`](sensor-acquisition.md)

---

## I want to diagnose the environment

Run:

```bash
python scripts/diagnostics/check_craterslab_env.py --full-traceback
```

Use this before processing real data if I suspect a Python, TensorFlow, Keras, or `craterslab` problem.

---

## I want to calculate slopes

Run:

```bash
python scripts/analysis/slope_calculator.py
```

If a file fails, the workflow prints the error, logs it, and lets me retry, edit, skip, or stop.

---

## I want to train the classifier

Run:

```bash
python scripts/training/train_classifier_2_0.py
```

Only do this when the expected training dataset is already in place.

---

## I am using VS Code

Use the integrated terminal:

```bash
source .venv/bin/activate
python main.py
```

See also:

- [`vscode-usage.md`](vscode-usage.md)

---

## I need examples

- [`workflow-examples.md`](workflow-examples.md)

## I need to understand outputs

- [`output-reference.md`](output-reference.md)

## I need to understand observables

- [`observable-interpretation.md`](observable-interpretation.md)

## I need a quick map of the tools

- [`tool-map.md`](tool-map.md)

---

## Session summary

The toolkit writes a session summary under:

```text
output/session_logs/
```

It tracks items such as:

- analyzed files
- reviewed files
- failed files
- corrected files
- generated outputs
