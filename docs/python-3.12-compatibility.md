# `craterslab` and Python 3.12 Compatibility

## Executive Summary

If `craterslab` works in Python 3.11 but fails in Python 3.12, the issue is usually not caused by the analysis scripts themselves. In most cases, it is caused by an environment mismatch involving one or more of the following:

- the installed `craterslab` version,
- the installed `keras` version,
- the installed `tensorflow` version,
- a partially reused or inconsistent `pyenv` / `venv` environment.

This repository treats **Python 3.11.x** as the recommended stable baseline.

---

## Recommended setup

### Stable environment: Python 3.11

```bash
pyenv install 3.11.11
pyenv local 3.11.11
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
pip install -e .
python scripts/diagnostics/check_craterslab_env.py --full-traceback
```

### Experimental environment: Python 3.12

```bash
pyenv install 3.12.9
pyenv local 3.12.9
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip uninstall -y craterslab tensorflow keras tf-keras || true
pip install "tensorflow>=2.16.1" "keras>=3.0" "craterslab>=0.2.8"
pip install -e .
python scripts/diagnostics/check_craterslab_env.py --full-traceback
```

---

## Why this matters

This project now assumes a cleaner installation model:

```bash
pip install -e .
```

That makes the repository behave like a local editable package instead of relying on manual path hacks inside scripts.

This is better for:

- local development,
- VS Code,
- tests,
- GitHub Actions,
- reproducibility.

---

## Minimal checks

### Check the active Python

```bash
python -V
which python
```

### Check installed packages

```bash
pip show craterslab tensorflow keras numpy scipy matplotlib scikit-learn
```

### Run the diagnostic

```bash
python scripts/diagnostics/check_craterslab_env.py --full-traceback
```

### Test with a real file

```bash
python scripts/diagnostics/check_craterslab_env.py \
  --sample-npz data/data_Fluized/fluized_1.npz \
  --full-traceback
```

---

## Practical conclusion

For most users:

- use **Python 3.11.x** for routine work,
- use **Python 3.12** only in a clean environment,
- install the repository with `pip install -e .`,
- validate the environment before running batch workflows.
