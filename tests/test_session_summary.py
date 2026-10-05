from pathlib import Path

from toolkit.session_summary import (
    append_session_entry,
    ensure_session_state_path,
    ensure_session_summary_path,
)


def test_session_summary_creates_grouped_output(tmp_path: Path, monkeypatch):
    summary_path = tmp_path / "session_summary.txt"
    state_path = tmp_path / "session_summary.json"
    monkeypatch.setenv("CRATERSLAB_SESSION_SUMMARY", str(summary_path))
    monkeypatch.setenv("CRATERSLAB_SESSION_STATE", str(state_path))

    ensure_session_state_path(summary_path)
    ensure_session_summary_path()
    append_session_entry(
        workflow="analyzer",
        dataset="fluized",
        category="analyzed",
        value="fluized_1.npz",
    )
    append_session_entry(
        workflow="analyzer", dataset="fluized", category="failed", value="fluized_2.npz"
    )

    text = summary_path.read_text(encoding="utf-8")
    assert "Workflow: analyzer" in text
    assert "Analyzed (1):" in text
    assert "Failed (1):" in text

    monkeypatch.delenv("CRATERSLAB_SESSION_SUMMARY")
    monkeypatch.delenv("CRATERSLAB_SESSION_STATE")
