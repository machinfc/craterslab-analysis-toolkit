# Known Limitations

This repository provides a practical workflow layer around `craterslab`, but several limitations remain important for users.

## 1. Classification Quality Depends on Preprocessing

Surface classification can change depending on cropping strategy and input quality. Some files may require manual review even when the environment is correctly configured.

## 2. Certain Fix Workflows Are Intentionally Semi-Manual

Scripts such as profile and ellipse fixers are designed to support interactive review, not fully unattended processing.

## 3. Plotting Assumes a Compatible Local Environment

Interactive visualization may require a GUI-capable matplotlib backend. Headless environments may need additional configuration.

## 4. GPU Warnings Are Common on CPU-Only Machines

TensorFlow may emit CUDA or cuDNN warnings even when CPU execution works correctly. These warnings do not necessarily indicate a broken installation.

## 5. Dataset Naming Conventions Matter

Many batch scripts assume conventional names such as `fluized_<index>.npz` and `compacted_<index>.npz`. If your dataset differs, you may need to pass explicit arguments or adapt the script invocation.

## 6. This Repository Does Not Bundle Large Datasets

Users are expected to supply their own data or maintain a separate data-distribution strategy.

## 7. Python 3.12 Should Be Validated Per Environment

While Python 3.12 may work, the recommended baseline remains Python 3.11.x unless compatibility has been explicitly verified with the included diagnostic script.
