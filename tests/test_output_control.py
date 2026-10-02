from pathlib import Path

from toolkit.output_control import build_analysis_output_path, next_available_path



def test_build_analysis_output_path_single_file(tmp_path: Path):
    result = build_analysis_output_path(tmp_path, "fluized", "observables", filename="fluized_1.npz")
    assert result.name == "fluized_1_observables.csv"



def test_next_available_path(tmp_path: Path):
    base = tmp_path / "result.csv"
    base.write_text("x", encoding="utf-8")
    next_path = next_available_path(base)
    assert next_path.name == "result_1.csv"
