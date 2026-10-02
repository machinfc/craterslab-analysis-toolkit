# Sensor Acquisition Guide

This project can capture crater depth data with two sensor backends:

- **Kinect** through `craterslab`
- **Orbbec Femto Bolt** through the Orbbec Python SDK

The goal is to keep the rest of the repository unchanged: once a capture is saved as `.npz`, the analyzer, visualizer, and fixer can use it the same way.

---

## Main idea

The acquisition workflow follows the same experimental logic already used in the project:

1. capture a **flat reference surface**,
2. capture the **surface after impact**,
3. subtract both maps,
4. export the crater depth map as `.npz` compatible with `craterslab`.

This is the recommended protocol because it reduces geometric bias from:

- surface tilt,
- sensor offset,
- background curvature,
- setup-specific depth bias.

---

## Supported sensors

### Kinect
This path uses:

- `DepthMap.from_kinect_sensor(...)`

It is the existing route already supported by `craterslab`.

### Femto Bolt
This path uses:

- `pyorbbecsdk2`, or
- `pyorbbecsdk`

The fetcher tries `pyorbbecsdk2` first and falls back to `pyorbbecsdk`.

The integration does **not** modify `craterslab`. It only captures depth data, converts it to a NumPy depth map, and saves it in the `.npz` structure that the rest of the project already expects.

---

## Recommended installation for Femto Bolt

If you plan to use the Femto Bolt acquisition path, install one of the Orbbec Python SDK packages in the active environment.

Recommended:

```bash
pip install pyorbbecsdk2
```

Alternative:

```bash
pip install pyorbbecsdk
```

---

## Choosing the sensor in the fetcher

Run:

```bash
python scripts/acquisition/depth_map_fetcher.py
```

The workflow now lets you choose:

- `kinect`
- `femto_bolt`

---

## Capture protocol options

The fetcher supports two acquisition modes:

### `plane_impact`
Recommended scientific workflow:

- capture the plane,
- capture the impact,
- subtract both.

### `impact_only`
Faster workflow:

- capture only the impact state.

This can be useful for quick checks, but it is less robust because it keeps more measurement bias from the setup.

---

## Region of interest (ROI)

The fetcher also supports choosing how much of the depth frame to keep:

- `full` → keep the whole frame
- `bbox` → crop to a manual region

The manual crop uses:

```text
x, y, width, height
```

This is useful when you do not want to use the full field of view.

---

## Important note about Femto Bolt calibration

The Femto Bolt path can be integrated operationally, but for real measurements it should be **experimentally recalibrated** for your setup.

That includes at least:

- lateral resolution validation,
- vertical scaling validation,
- stability of the plane reference,
- comparison against the previous route or a known crater.

The repository currently provides the acquisition path, not the final scientific calibration of the device for your particular setup.

---

## Output compatibility

Captured data are saved as `.npz` files using the same structure expected by `craterslab`:

- `depthmap`
- `xres`
- `yres`
- `zres`
- `scale`

That means the rest of the repository can use the resulting files without changing the analysis code.
