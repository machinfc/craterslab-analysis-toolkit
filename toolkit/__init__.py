"""Utilities shared by the standalone Craterslab analysis scripts."""

from .batch_review import add_batch_item, ask_problematic_action, new_batch_stats, print_batch_summary
from .error_handling import append_error_log, ask_error_action, format_exception_text, print_processing_error
from .exporters import DEFAULT_OBS_VAL, write_observables_csv, write_profile_csv
from .fix_logging import append_fix_log
from .observable_plotting import interactive_observable_plotting
from .output_control import build_analysis_output_path, next_available_path, resolve_output_path
from .paths import (
    DATASET_INFO,
    DATA_DIR,
    OUTPUT_DIR,
    PROJECT_ROOT,
    ensure_directory,
    get_dataset_dir,
    get_dataset_info,
    normalize_dataset_name,
)
from .session_summary import append_session_entry, append_session_note, ensure_session_summary_path
from .visualization_helpers import plot_profile_safe, profile_supports_slopes, show_review_figures

__all__ = [
    "DEFAULT_OBS_VAL",
    "DATASET_INFO",
    "DATA_DIR",
    "OUTPUT_DIR",
    "PROJECT_ROOT",
    "add_batch_item",
    "append_error_log",
    "append_fix_log",
    "append_session_entry",
    "append_session_note",
    "ask_error_action",
    "ask_problematic_action",
    "build_analysis_output_path",
    "ensure_directory",
    "ensure_session_summary_path",
    "format_exception_text",
    "get_dataset_dir",
    "get_dataset_info",
    "interactive_observable_plotting",
    "new_batch_stats",
    "next_available_path",
    "normalize_dataset_name",
    "plot_profile_safe",
    "print_batch_summary",
    "print_processing_error",
    "profile_supports_slopes",
    "resolve_output_path",
    "show_review_figures",
    "write_observables_csv",
    "write_profile_csv",
]
