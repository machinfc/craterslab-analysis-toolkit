from __future__ import annotations

from typing import Sequence

import matplotlib.pyplot as plt

from toolkit.interactive import ask_choice, ask_yes_no


def rows_to_records(rows: Sequence[Sequence[object]], observables: Sequence[str]) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for row in rows:
        record = {"filename": row[0], "type": row[1]}
        for observable, value in zip(observables, row[2:]):
            record[observable] = value
        records.append(record)
    return records



def interactive_observable_plotting(
    rows: Sequence[Sequence[object]],
    observables: Sequence[str],
    title_prefix: str = "",
) -> None:
    if not rows:
        print("No rows available for plotting.")
        return

    records = rows_to_records(rows, observables)
    options = {observable: observable for observable in observables}

    while True:
        print("\nAvailable observables for plotting:")
        x_observable = ask_choice("Select X observable", options, default=observables[0])
        y_observable = ask_choice(
            "Select Y observable",
            options,
            default=observables[1] if len(observables) > 1 else observables[0],
        )
        annotate = ask_yes_no("Annotate points with file names", default=False)

        x_values = []
        y_values = []
        labels = []
        for record in records:
            x_value = record[x_observable]
            y_value = record[y_observable]
            if x_value == -1 or y_value == -1:
                continue
            x_values.append(x_value)
            y_values.append(y_value)
            labels.append(str(record["filename"]))

        if not x_values:
            print("No valid data points found for that observable pair.")
        else:
            fig, ax = plt.subplots()
            ax.scatter(x_values, y_values)
            ax.set_xlabel(x_observable)
            ax.set_ylabel(y_observable)
            title = f"{title_prefix} {y_observable} vs {x_observable}".strip()
            ax.set_title(title)
            ax.grid(True)
            if annotate:
                for label, x_value, y_value in zip(labels, x_values, y_values):
                    ax.annotate(label, (x_value, y_value), fontsize=8)
            plt.show(block=True)

        if not ask_yes_no("Plot another observable pair", default=False):
            break
