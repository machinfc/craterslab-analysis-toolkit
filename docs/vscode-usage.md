# VS Code Usage

This repository works well in VS Code if I run it through the terminal.

---

## Basic setup

1. Open the repository folder in VS Code.
2. Select the `.venv` interpreter.
3. Open the integrated terminal.
4. Activate the environment:

```bash
source .venv/bin/activate
```

---

## Recommended first command

```bash
python main.py
```

That is the easiest entry point for a new user.

---

## Direct commands

Analyzer:

```bash
python scripts/analysis/data_analyzer.py
```

Visualizer:

```bash
python scripts/visualization/depth_map_visualizer.py
```

Fixer:

```bash
python scripts/fixes/ellipse_fixer.py
```

Diagnostic:

```bash
python scripts/diagnostics/check_craterslab_env.py --full-traceback
```

---

## Important note

Use one of these:

- **Run Python File in Terminal**
- commands typed manually in the integrated terminal

Do **not** use a runner that cannot handle `input()` prompts.

Most workflows in this repository are interactive.

---

## If I use Code Runner

Make sure it runs inside the terminal.

Typical setting:

```json
"code-runner.runInTerminal": true
```

---

## If I cancel a prompt

I can stop an interactive prompt with:

```text
Ctrl+C
```

The toolkit exits interactive prompts more cleanly now.
