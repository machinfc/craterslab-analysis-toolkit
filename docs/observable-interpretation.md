# Observable Interpretation Guide

This document explains the main crater observables used by the repository, how they are treated operationally in the toolkit, and how users may interpret them in a morphometric workflow.

The goal is not to replace the scientific literature, but to provide a practical guide for users who need to understand what the exported values mean and how they can be compared.

---

## Scope

The observables described here are the ones most commonly exported by the analyzer and fixer workflows:

- `D`
- `d_max`
- `d_exc`
- `mean_h_rim`
- `V_in`
- `V_ex`
- `V_exc`
- `V_cp`
- `H_cp`
- `epsilon`

Depending on crater type and workflow, not every observable will be available for every file.

---

## Important Interpretation Note

These observables depend on:

- the quality of the input depth map or point cloud,
- the crop strategy,
- the ellipse fit,
- the inferred or manually assigned `SurfaceType`,
- and, for QuickMap / LROC workflows, the chosen `z_shift`.

Therefore, crater observables should always be interpreted together with:

- the visual inspection,
- the chosen preprocessing parameters,
- and the correction history when manual fixing has been applied.

---

## Main Observables

### `D` — Diameter

**Operational meaning in this repository:**
The crater diameter estimated from the ellipse fit.

**Interpretation:**
This is one of the most important lateral size measures in the workflow. It represents the characteristic horizontal scale of the crater as inferred from the fitted morphology.

**Typical use:**
- compare crater size across experiments,
- examine scaling trends,
- correlate diameter with depth or volume metrics.

---

### `d_max` — Apparent Depth

**Operational meaning in this repository:**
A depth-like measure combining the excavated depression and the rim elevation contribution.

**Interpretation:**
This quantity is useful when users want a practical measure of crater depth relative to the surrounding morphology, not only the deepest point below the reference level.

**Typical use:**
- compare crater depth between experiments,
- relate lateral size (`D`) to apparent depth,
- identify unusually shallow or deep morphologies.

---

### `d_exc` — Maximum Excavated Depth

**Operational meaning in this repository:**
The deepest excavated point inside the crater morphology relative to the measurement reference.

**Interpretation:**
This is closer to a "true excavation depth" measure than `d_max` in the practical toolkit sense.

**Typical use:**
- compare excavation efficiency,
- assess the vertical penetration of the impact process,
- compare with rim-based or apparent-depth metrics.

---

### `mean_h_rim` — Mean Rim Height

**Operational meaning in this repository:**
The mean height measured around the ellipse perimeter associated with the crater rim.

**Interpretation:**
This is a useful descriptor of how strongly the rim is elevated above the surrounding reference surface.

**Typical use:**
- distinguish craters with strongly uplifted rims,
- compare rim development across material states,
- interpret the balance between excavation and displacement.

---

### `V_in` — Concavity Volume

**Operational meaning in this repository:**
An inward or concavity-related volume associated with the crater depression.

**Interpretation:**
This quantity characterizes how much volume is associated with the crater cavity itself.

**Typical use:**
- compare cavity development,
- relate crater size to excavated shape,
- compare crater families statistically.

---

### `V_ex` — Excavated Volume

**Operational meaning in this repository:**
A volume measure associated with the excavated portion of the crater.

**Interpretation:**
This is one of the main volume metrics for evaluating how much material displacement is associated with the impact-generated depression.

**Typical use:**
- compare excavation behavior between experiments,
- identify scaling relations with `D` or `d_exc`,
- compare different granular states or impact conditions.

---

### `V_exc` — Excess Volume

**Operational meaning in this repository:**
A volume-like measure associated with positive relief, i.e. material above the chosen reference level.

**Interpretation:**
This can be understood as a practical measure of the excess or uplifted material associated with crater formation.

**Typical use:**
- compare displaced/uplifted material with excavated material,
- examine asymmetries between cavity and positive-relief development,
- study rim and ejecta-related morphometric tendencies.

---

### `V_cp` — Central Peak Volume

**Operational meaning in this repository:**
A volume measure associated with a central peak morphology.

**Interpretation:**
This is only meaningful when the crater type supports a central-peak-like structure.

**Typical use:**
- characterize complex crater interiors,
- compare central-peak prominence,
- distinguish morphologies beyond simple-crater behavior.

---

### `H_cp` — Central Peak Height

**Operational meaning in this repository:**
A height measure associated with the central peak structure.

**Interpretation:**
Like `V_cp`, this is specific to morphologies where a central peak is relevant.

**Typical use:**
- quantify central peak prominence,
- compare complex crater morphologies,
- interpret internal uplift relative to total crater geometry.

---

### `epsilon` — Eccentricity

**Operational meaning in this repository:**
The eccentricity of the fitted ellipse.

**Interpretation:**
This indicates how circular or elongated the fitted crater geometry is.

- low eccentricity → more circular crater fit
- higher eccentricity → more elongated crater fit

**Typical use:**
- assess crater symmetry,
- identify oblique or irregular morphologies,
- evaluate whether the ellipse fit may need manual review.

---

## Additional Derived Review Quantities

### Slopes (`m1`, `m2`)

These are not always exported in the main observables CSV, but they are important in profile workflows.

**Interpretation:**
They describe the inclination of the crater flanks along the selected or automatically generated profile.

**Typical use:**
- compare crater side steepness,
- identify asymmetric profiles,
- validate whether the automatically chosen profile is scientifically useful.

---

## Why Some Observables May Be Missing

Some crater observables are only available for certain crater classes.

For example:

- central peak observables (`V_cp`, `H_cp`) are only meaningful for crater types where a central peak exists,
- some observables may be absent when the crater is classified as `Unknown`,
- some observables may be absent when the fitted geometry is poor or the morphology is not compatible with the expected model.

In exported CSV files, unavailable observables may appear with a placeholder value such as `-1`.

---

## Interpretation Best Practices

When comparing observables across files, users should:

1. inspect the crater visually,
2. verify the crop behavior,
3. verify the ellipse fit,
4. verify the `SurfaceType`,
5. review whether manual fixing was applied,
6. consult the correction log if relevant,
7. compare observables only after confirming that the underlying geometry is acceptable.

---

## QuickMap / LROC Note on `z_shift`

For planetary workflows, `z_shift` should be treated as a scientifically relevant preprocessing parameter.

It is used to adjust the vertical reference level of the imported data so that the morphometric measurements are taken relative to a more appropriate zero level.

This is especially important in lunar geodetic workflows where the raw elevation reference may not directly match the interpretation needed for crater measurements.

---

## Related Publications

The repository is directly relevant to the following background works supplied by the project author.

### Article

Corrales-Machín, F., Viera-López, G., Bartali, R., & Nahmad-Molinar, Y. (2024). *Morphological study of granular--granular impact craters through time-of-flight cameras: from concept to automation in Python*. **Granular Matter, 26**(3), 72.

### Thesis

Corrales Machín, F. et al. (2024). *Morphometric Analysis of Granular Impact Craters through Time-of-Flight Cameras. Depth Prediction Model and Lateral Opening Mechanisms*. **Repositorio Nacional CONACYT**.

For machine-readable citation entries, see [`references.md`](references.md).
