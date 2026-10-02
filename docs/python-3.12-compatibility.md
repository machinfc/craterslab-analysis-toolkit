# `craterslab` and Python 3.12 Compatibility

## Executive Summary

If `craterslab` works in Python 3.11 but fails in Python 3.12, the issue is usually not caused by the analysis scripts themselves. In most cases, it is caused by an environment mismatch involving one or more of the following:

- the installed `craterslab` version,
- the installed `keras` version,
- the installed `tensorflow` version,
- a partially reused or inconsistent `pyenv` / `venv` environment.

This repository therefore treats **Python 3.11.x** as the recommended stable baseline and provides a diagnostic script to test newer environments safely.

---

## Why Python 3.12 Can Be More Fragile

Recent versions of `craterslab` rely on the modern Keras 3 ecosystem. In practice, that means the runtime environment must include a compatible deep-learning backend. In this project, the expected backend is **TensorFlow**.

A typical failure scenario looks like this:

- `pip install craterslab` appears to succeed,
- but `import craterslab` fails,
- or `Surface(depth_map)` fails when classification is triggered,
- or the bundled pretrained model cannot be loaded.

These symptoms are usually environment-related rather than script-related.

---

## Recommended Strategy

### Stable environment: Python 3.11

Use Python 3.11 when you need a predictable working setup:

```bash
pyenv install 3.11.11
pyenv local 3.11.11
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
python scripts/diagnostics/check_craterslab_env.py
```

### Experimental environment: Python 3.12

When testing Python 3.12, always start from a clean environment:

```bash
pyenv install 3.12.9
pyenv local 3.12.9
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip uninstall -y craterslab tensorflow keras tf-keras || true
pip install "tensorflow>=2.16.1" "keras>=3.0" "craterslab>=0.2.8"
python scripts/diagnostics/check_craterslab_env.py --full-traceback
```

---

## How to Diagnose the Real Failure

### 1. Confirm installed versions

```bash
python -V
pip show craterslab tensorflow keras numpy scipy matplotlib scikit-learn
```

### 2. Run the general diagnostic

```bash
python scripts/diagnostics/check_craterslab_env.py --full-traceback
```

### 3. Run the diagnostic on a real crater file

```bash
python scripts/diagnostics/check_craterslab_env.py \
  --sample-npz data/data_Fluized/fluized_1.npz \
  --full-traceback
```

If that command fails, the output will help isolate whether the issue comes from:

- TensorFlow import,
- Keras import,
- `craterslab` import,
- pretrained model loading,
- crater classification,
- or file loading / preprocessing.

---

## Repository-Level Improvements Included Here

This toolkit already includes a few safeguards that make troubleshooting easier:

- project-relative paths instead of fragile hard-coded locations,
- automatic output-directory creation,
- `argparse`-based command-line interfaces,
- shared CSV export utilities,
- a dedicated environment diagnostic script.

These changes improve maintainability, but they do not replace the need for a consistent Python / ML stack.

---

## Recommended Dependency Baseline

For public use of this repository, the suggested minimum stack is:

- `craterslab>=0.2.8`
- `keras>=3.0`
- `tensorflow>=2.16.1`

If classification works correctly in your environment, there is no immediate need to upgrade further just for version-number reasons.

---

## Practical Conclusion

For most users:

- use **Python 3.11.x** for routine work,
- use **Python 3.12** only in a clean, isolated environment,
- validate every new environment with the diagnostic script before running batch analyses.

If a Python 3.12 environment fails, collect the full traceback and compare it against a known-good Python 3.11 run. That comparison is usually enough to identify whether the problem is installation-related or data-related.
