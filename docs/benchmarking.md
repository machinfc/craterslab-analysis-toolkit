# Benchmarking

This project is interactive, so benchmark results depend heavily on:

- dataset size,
- plotting mode,
- sensor backend,
- Python environment,
- whether the run is analysis-only or analysis plus review.

For that reason, I do not include fabricated benchmark numbers in the public documentation.

Instead, I provide:

1. a benchmark table with the current public status,
2. commands I use to generate timing data,
3. a suggested format for reporting future results.

---

## Current public benchmark status

| Scenario | Status | Notes |
|---|---:|---|
| Single-file analysis | Not measured yet | Pending a stable reference dataset |
| Range analysis | Not measured yet | Pending a stable reference dataset |
| Strong scaling | Not measured yet | Same total workload, varying file count split |
| Weak scaling | Not measured yet | Workload grows with file count |
| Fixer batch review | Not measured yet | Interactive workflow; depends on user actions |

This is intentional. I prefer an honest empty benchmark table over numbers that cannot be reproduced.

---

## Basic timing commands

### Analyzer, single file

```bash
/usr/bin/time -f "elapsed=%E maxrss=%MKB" \
python scripts/analysis/data_analyzer.py \
  --dataset fluized --mode single --filename fluized_1.npz
```

### Analyzer, numeric range

```bash
/usr/bin/time -f "elapsed=%E maxrss=%MKB" \
python scripts/analysis/data_analyzer.py \
  --dataset compacted --mode range --start 25 --end 49 --plot2d --plot3d
```

### Slope calculator

```bash
/usr/bin/time -f "elapsed=%E maxrss=%MKB" \
python scripts/analysis/slope_calculator.py \
  --dataset compacted --mode range --start 25 --end 49
```

---

## Recommended reporting format

When I add benchmark numbers, I plan to report them in this format.

### Before / after change

| Workflow | Before | After | Delta | Notes |
|---|---:|---:|---:|---|
| Analyzer, single file | TBD | TBD | TBD | Reference dataset required |
| Analyzer, 25 files | TBD | TBD | TBD | Same environment and inputs |
| Visual review, 10 files | TBD | TBD | TBD | Must state whether plots were enabled |

### Strong scaling

Strong scaling means keeping the total workload fixed while changing how many files are processed per run block or execution unit.

| Total files | Execution setup | Time | Notes |
|---|---|---:|---|
| TBD | TBD | TBD | Same total workload |

### Weak scaling

Weak scaling means increasing workload proportionally with the processing scope.

| Files processed | Time | Notes |
|---:|---:|---|
| TBD | TBD | Same workflow settings |
| TBD | TBD | Same workflow settings |

---

## What matters most

For this repository, the most meaningful performance measurements are usually:

- time per analyzed file,
- time per fixed file,
- memory growth across batch runs,
- effect of enabling plots,
- effect of switching from full-frame review to cropped review,
- sensor acquisition latency per averaged capture.

---

## Reproducibility rule

A benchmark entry should only be published if it includes:

- Python version,
- package versions,
- command used,
- dataset scope,
- whether plotting was enabled,
- hardware context.
