# Changelog

All notable changes to this project should be documented in this file.

The format is inspired by [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project aims to follow semantic versioning where practical.

## [Unreleased]

### Added
- Professional repository structure for public GitHub publication.
- Shared toolkit utilities for paths and CSV export.
- Environment diagnostic script for `craterslab` / Python compatibility testing.
- English-language public documentation for installation, usage, and troubleshooting.
- Scientific repository support files: contribution guide, citation file, code of conduct, security policy, CI workflow, and issue templates.
- Central launcher `main.py` integrating analysis, visualization, fixing, acquisition, diagnostics, training, and slope workflows.
- Text-based correction logging under `output/fix_logs/`.
- User-facing usage documentation for both Bash and VS Code.
- Technical documentation for workflows, outputs, dataset preparation, observable interpretation, and related references.

### Changed
- Refactored scripts to use project-relative paths.
- Reworked command-line interfaces with `argparse` and interactive terminal prompts.
- Unified analyzer workflow across laboratory and QuickMap datasets.
- Unified fixer workflow around `ellipse_fixer.py`.
- Unified visual review workflow around `depth_map_visualizer.py`.
- Added safer interactive cancellation handling.
- Improved output naming and overwrite protection.

### Notes
- Python 3.11 is treated as the recommended stable baseline.
- Python 3.12 support should be validated per environment.
