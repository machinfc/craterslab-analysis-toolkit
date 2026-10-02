# Tool Map

Use this file when I am not sure which command to run.

---

## Best starting point

```bash
python main.py
```

---

## Main tools

### Analyze crater data

```bash
python scripts/analysis/data_analyzer.py
```

### Review crater data visually

```bash
python scripts/visualization/depth_map_visualizer.py
```

### Fix crater geometry or classification

```bash
python scripts/fixes/ellipse_fixer.py
```

### Check the environment

```bash
python scripts/diagnostics/check_craterslab_env.py --full-traceback
```

### Capture a depth map from Kinect or Femto Bolt

```bash
python scripts/acquisition/depth_map_fetcher.py
```

### Train the classifier

```bash
python scripts/training/train_classifier_2_0.py
```

### Calculate slopes

```bash
python scripts/analysis/slope_calculator.py
```

---

## Legacy wrappers

These files still exist for compatibility, but they are not the recommended entry points for new users:

- `scripts/analysis/lroc_analyzer.py`
- `scripts/fixes/lroc_fixer.py`
- `scripts/visualization/single_depth_map_visualizer.py`

Use the unified tools instead:

- `data_analyzer.py`
- `ellipse_fixer.py`
- `depth_map_visualizer.py`
