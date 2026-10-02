# Contributing

Thank you for your interest in contributing to this repository.

This project is structured as a scientific scripting toolkit, so contributions should prioritize the following:

- correctness,
- reproducibility,
- clarity of scientific intent,
- maintainability of command-line workflows,
- preservation of compatibility with existing dataset layouts when possible.

---

## Ways to Contribute

You can contribute by:

- reporting bugs,
- proposing workflow improvements,
- improving documentation,
- refactoring scripts for better maintainability,
- adding tests or diagnostic improvements,
- improving data validation or export behavior,
- documenting edge cases and limitations.

---

## Before Opening a Pull Request

Please try to do the following first:

1. Open an issue for significant changes.
2. Explain the scientific or workflow motivation.
3. Describe whether the change affects:
   - reproducibility,
   - path conventions,
   - expected file naming,
   - output structure,
   - or Python / dependency compatibility.

---

## Development Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

Optional:

```bash
pre-commit install
```

---

## Recommended Checks

Before submitting a pull request, run:

```bash
make smoke
make lint
```

If your change affects environment handling, also run:

```bash
make diagnose
```

If your change affects a specific workflow, include the command used to validate it.

---

## Coding Guidelines

- Prefer `pathlib` over hard-coded path strings.
- Keep scripts runnable from the repository root.
- Avoid introducing machine-specific assumptions.
- Document new command-line flags clearly.
- Preserve backward compatibility unless there is a strong reason not to.
- Keep comments scientific and operational, not personal.

---

## Documentation Guidelines

Documentation should be written for external users, not only for repository maintainers.

Please make sure new documentation explains:

- what the script does,
- what input it expects,
- what output it produces,
- any scientific assumptions or caveats,
- and any environment-specific requirements.

---

## Pull Request Checklist

Before submitting, verify that:

- [ ] the code runs from the repository root,
- [ ] no fragile local paths were introduced,
- [ ] documentation was updated when behavior changed,
- [ ] command examples remain valid,
- [ ] the change does not silently break existing dataset conventions.

---

## Scientific Responsibility

This repository supports scientific data handling. Contributors should therefore avoid making changes that alter results or interpretation without documenting the methodological consequence.

If a contribution changes the meaning of an observable, preprocessing step, classification path, or export field, that change should be explicitly documented.
