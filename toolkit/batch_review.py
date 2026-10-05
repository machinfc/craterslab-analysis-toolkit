from __future__ import annotations

from collections import defaultdict

from toolkit.interactive import ask_choice


def new_batch_stats() -> dict[str, list[str]]:
    return defaultdict(list)  # type: ignore[return-value]


def add_batch_item(stats: dict[str, list[str]], category: str, value: str) -> None:
    if value not in stats[category]:
        stats[category].append(value)


def print_batch_summary(workflow: str, stats: dict[str, list[str]]) -> None:
    print("\n" + "=" * 80)
    print(f"Batch summary: {workflow}")
    print("=" * 80)
    for category in [
        "analyzed",
        "reviewed",
        "corrected",
        "failed",
        "outputs",
        "problematic",
    ]:
        values = stats.get(category, [])
        if values:
            print(f"{category.capitalize()}: {len(values)}")
            for value in values:
                print(f"  - {value}")
    if not any(stats.get(category) for category in stats):
        print("No items were processed.")


def ask_problematic_action() -> str:
    return ask_choice(
        "Problematic files found. What do you want to do",
        {
            "reopen": "Reopen only the problematic files",
            "continue": "Finish without reopening",
        },
        default="continue",
    )
