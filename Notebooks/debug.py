# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "marimo>=0.20.4",
# ]
# ///

import marimo

__generated_with = "0.20.4"
app = marimo.App(width="full")


@app.cell
def _():
    from pathlib import Path

    import marimo as mo
    import pandas as pd

    return Path, mo, pd


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # Telemetry Debugging Notebook
    Standalone debug & annotation view for ensuring data integrity.
    """)
    return


@app.cell
def _(Path, mo):
    data_dir = Path(__file__).parent.parent / "data"

    available_files = []
    if data_dir.exists():
        for file in data_dir.rglob("*.jsonl"):
            available_files.append(str(file))

    if not available_files:
        raise FileNotFoundError("No .jsonl files found in 'data' or its subdirectories")

    file_selector = mo.ui.dropdown(
        options=available_files,
        value=available_files[0] if available_files else None,
        label="Select data file",
        full_width=True,
    )

    file_selector
    return (file_selector,)


@app.cell
def _(file_selector, mo):
    mo.stop(
        not file_selector.value, mo.md("Please select a data file to begin analysis")
    )
    return


@app.cell
def _(file_selector, pd):
    raw_data = pd.read_json(file_selector.value, lines=True)
    return (raw_data,)


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Session Health & Diagnostics
    """)
    return


@app.cell(hide_code=True)
def _(mo, raw_data):
    mo.md(f"""
    ### Event Integrity
    - **Total raw events**: {len(raw_data)}
    - **Unique sessions**: {raw_data["session_id"].nunique()}
    - **Unique machines**: {raw_data["machine_id"].nunique()}
    - **Event types seen**: {sorted(raw_data["event_type"].unique().tolist())}
    """)
    return


@app.cell(hide_code=True)
def _(mo, raw_data):
    _sorted = raw_data.sort_values(["session_id", "event_order"]).reset_index(drop=True)

    _seq_violations = (
        _sorted.groupby("session_id")["event_order"]
        .diff()
        .dropna()
        .lt(0)
        .sum()
    )

    mo.md(f"""
    ### Event Sequence
    - **Time sequence violations** *(event_order decreases within a session)*: {_seq_violations}
    """)
    return


@app.cell(hide_code=True)
def _(mo, raw_data):
    _sorted = raw_data.sort_values(["session_id", "event_order"]).reset_index(drop=True)

    _diffs = _sorted.groupby("session_id")["event_order"].diff()
    _gap_mask = _diffs.gt(1)
    _gap_rows = _sorted[_gap_mask].copy()
    _gap_rows["gap_size"] = _diffs[_gap_mask].astype(int)
    _gap_rows["events_missing"] = _gap_rows["gap_size"] - 1

    _gap_summary = (
        _gap_rows.groupby("session_id")["events_missing"]
        .agg(gap_count="count", max_gap="max", total_missing="sum")
        .reset_index()
    )
    _total_missing = int(_gap_rows["events_missing"].sum())

    mo.vstack(
        [
            mo.md(f"""
    ### Missing Event Detection
    - **Sessions with gaps**: {_gap_rows["session_id"].nunique()}
    - **Total gap locations**: {len(_gap_rows)}
    - **Estimated missing events**: {_total_missing}
    """),
            mo.ui.tabs(
                {
                    "Gap Summary by Session": mo.ui.table(
                        _gap_summary.sort_values("total_missing", ascending=False).reset_index(drop=True)
                    )
                    if len(_gap_summary) > 0
                    else mo.md("✅ No gaps detected — event_order is fully contiguous!"),
                    "All Gap Locations": mo.ui.table(
                        _gap_rows[
                            ["session_id", "machine_id", "event_order", "gap_size", "events_missing", "game_time", "event_type"]
                        ]
                        .sort_values(["session_id", "event_order"])
                        .reset_index(drop=True)
                    )
                    if len(_gap_rows) > 0
                    else mo.md("✅ No gaps detected!"),
                }
            ),
        ]
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    ## Schema Generator
    Scans all `.jsonl` files under `data/` and writes a merged `data/telemetry.schema.json`.
    """)
    return


@app.cell
def _(mo):
    generate_schema_btn = mo.ui.run_button(label="Generate Schema")
    generate_schema_btn
    return (generate_schema_btn,)


@app.cell
def _(Path, generate_schema_btn, mo):
    import json

    from genson import SchemaBuilder

    mo.stop(not generate_schema_btn.value)

    _builder = SchemaBuilder()
    _data_dir = Path(__file__).parent.parent / "data"
    _files = list(_data_dir.rglob("*.jsonl"))

    for _file in _files:
        with open(_file) as _f:
            for _line in _f:
                _line = _line.strip()
                if _line:
                    _builder.add_object(json.loads(_line))

    _schema = _builder.to_schema()
    _out = _data_dir / "telemetry.schema.json"

    with open(_out, "w") as _f:
        json.dump(_schema, _f, indent=2)

    mo.md(f"✅ Schema written to `{_out}` — scanned **{len(_files)}** files.").callout(kind="success")
    return


if __name__ == "__main__":
    app.run()
