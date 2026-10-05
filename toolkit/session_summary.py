from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from toolkit.paths import OUTPUT_DIR, ensure_directory

SESSION_LOG_DIR = ensure_directory(OUTPUT_DIR / "session_logs")
SESSION_ENV_VAR = "CRATERSLAB_SESSION_SUMMARY"
SESSION_STATE_ENV_VAR = "CRATERSLAB_SESSION_STATE"

DEFAULT_CATEGORIES = [
    "analyzed",
    "reviewed",
    "failed",
    "corrected",
    "outputs",
    "output",
    "note",
]


def _default_state() -> dict[str, Any]:
    return {
        "created": datetime.now().isoformat(timespec="seconds"),
        "updated": None,
        "events": [],
    }


def ensure_session_summary_path() -> Path:
    existing = os.environ.get(SESSION_ENV_VAR)
    if existing:
        path = Path(existing)
        path.parent.mkdir(parents=True, exist_ok=True)
        ensure_session_state_path(path)
        return path

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = SESSION_LOG_DIR / f"session_summary_{timestamp}.txt"
    os.environ[SESSION_ENV_VAR] = str(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    ensure_session_state_path(path)
    _render_session_summary(path, _load_state())
    return path


def ensure_session_state_path(summary_path: Path | None = None) -> Path:
    existing = os.environ.get(SESSION_STATE_ENV_VAR)
    if existing:
        path = Path(existing)
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_text(json.dumps(_default_state(), indent=2), encoding="utf-8")
        return path

    summary = summary_path or ensure_session_summary_path()
    state_path = summary.with_suffix(".json")
    os.environ[SESSION_STATE_ENV_VAR] = str(state_path)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    if not state_path.exists():
        state_path.write_text(json.dumps(_default_state(), indent=2), encoding="utf-8")
    return state_path


def _load_state() -> dict[str, Any]:
    state_path = ensure_session_state_path()
    try:
        return json.loads(state_path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        state = _default_state()
        state_path.write_text(json.dumps(state, indent=2), encoding="utf-8")
        return state


def _save_state(state: dict[str, Any]) -> None:
    state_path = ensure_session_state_path()
    state_path.write_text(json.dumps(state, indent=2), encoding="utf-8")


def _unique_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def _group_events(state: dict[str, Any]) -> dict[str, dict[str, list[str]]]:
    grouped: dict[str, dict[str, list[str]]] = {}
    for event in state.get("events", []):
        workflow = event.get("workflow", "unknown")
        category = event.get("category", "note")
        value = str(event.get("value", ""))
        grouped.setdefault(workflow, {})
        grouped[workflow].setdefault(category, [])
        grouped[workflow][category].append(value)
    for workflow in grouped:
        for category in list(grouped[workflow]):
            grouped[workflow][category] = _unique_preserve_order(
                grouped[workflow][category]
            )
    return grouped


def _render_session_summary(path: Path, state: dict[str, Any]) -> None:
    grouped = _group_events(state)
    lines = [
        "Craterslab Analysis Toolkit session summary",
        "=" * 80,
        f"Created: {state.get('created', 'unknown')}",
        f"Last updated: {state.get('updated', 'unknown')}",
        "",
    ]

    if not grouped:
        lines.append("No session events recorded yet.")
    else:
        for workflow, categories in grouped.items():
            lines.append(f"Workflow: {workflow}")
            lines.append("-" * 80)
            ordered_categories = [
                *DEFAULT_CATEGORIES,
                *sorted(c for c in categories if c not in DEFAULT_CATEGORIES),
            ]
            for category in ordered_categories:
                values = categories.get(category, [])
                if not values:
                    continue
                title = (
                    "Outputs"
                    if category in {"output", "outputs"}
                    else category.capitalize()
                )
                lines.append(f"{title} ({len(values)}):")
                for value in values:
                    lines.append(f"  - {value}")
                lines.append("")
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def append_session_entry(
    *,
    workflow: str,
    category: str,
    value: str,
    dataset: str | None = None,
) -> Path:
    path = ensure_session_summary_path()
    state = _load_state()
    timestamp = datetime.now().isoformat(timespec="seconds")
    state["updated"] = timestamp
    state.setdefault("events", []).append(
        {
            "timestamp": timestamp,
            "workflow": workflow,
            "dataset": dataset,
            "category": category,
            "value": value,
        }
    )
    _save_state(state)
    _render_session_summary(path, state)
    return path


def append_session_note(
    workflow: str, message: str, dataset: str | None = None
) -> Path:
    return append_session_entry(
        workflow=workflow, category="note", value=message, dataset=dataset
    )
