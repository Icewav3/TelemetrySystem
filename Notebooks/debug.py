# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "marimo>=0.20.4",
# ]
# ///

import marimo

__generated_with = "0.22.0"
app = marimo.App(width="full")


@app.cell
def _():
    import json
    from pathlib import Path

    import marimo as mo
    import pandas as pd
    import plotly.graph_objects as go

    return Path, go, json, mo, pd


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # Telemetry Debugging Notebook

    Standalone debug & annotation view for ensuring data integrity.
    """)
    return


@app.cell(hide_code=True)
def _(Path, json, mo, pd):
    _data_dir = Path(__file__).parent.parent / "data"

    _rows = []
    if _data_dir.exists():
        for _folder in sorted(_data_dir.iterdir()):
            if not _folder.is_dir():
                continue
            _jsonl_files = list(_folder.rglob("*.jsonl"))
            if not _jsonl_files:
                continue

            _meta_path = _folder / "playtest_metadata.json"
            _description = ""
            if _meta_path.exists():
                with open(_meta_path) as _f:
                    _description = json.load(_f).get("info", "")

            _first_time = None
            _last_time = None
            for _file in _jsonl_files:
                _df = pd.read_json(_file, lines=True)
                if "server_timestamp" in _df.columns and len(_df) > 0:
                    _ts = pd.to_datetime(_df["server_timestamp"])
                    _ft = _ts.min()
                    _lt = _ts.max()
                    if _first_time is None or _ft < _first_time:
                        _first_time = _ft
                    if _last_time is None or _lt > _last_time:
                        _last_time = _lt

            _date = ""
            _duration = ""
            if _first_time is not None and _last_time is not None:
                _date = _first_time.strftime("%Y-%m-%d")
                _dur_s = int((_last_time - _first_time).total_seconds())
                _hrs = _dur_s // 3600
                _mins = (_dur_s % 3600) // 60
                _secs = _dur_s % 60
                _duration = f"{_hrs}h {_mins}m {_secs}s"

            _rows.append(
                {
                    "Folder": _folder.name,
                    "Date": _date if _date else "—",
                    "Duration": _duration if _duration else "—",
                    "Has Metadata": _meta_path.exists(),
                    "Description": _description[:120] if _description else "—",
                }
            )

    _output = (
        mo.vstack(
            [
                mo.md("### Playtest Overview"),
                mo.ui.table(pd.DataFrame(_rows), selection=None),
            ]
        )
        if _rows
        else mo.md("")
    )
    _output
    return


@app.cell(hide_code=True)
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


@app.cell(hide_code=True)
def _(file_selector, mo):
    mo.stop(not file_selector.value, mo.md("Please select a data file to begin analysis"))
    return


@app.cell(hide_code=True)
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
    _counts = (
        raw_data["event_type"]
        .value_counts()
        .reset_index()
        .rename(columns={"event_type": "Event Type", "count": "Count"})
    )
    mo.vstack(
        [
            mo.md("### Event Type Counts"),
            mo.ui.table(_counts, selection=None),
        ]
    )
    return


@app.cell(hide_code=True)
def _(mo, raw_data):
    _event_types = sorted(raw_data["event_type"].unique().tolist())
    _session_ids = sorted(raw_data["session_id"].unique().tolist())

    event_type_filter = mo.ui.dropdown(
        options=["ALL"] + _event_types,
        value="ALL",
        label="Event type",
    )

    session_filter = mo.ui.dropdown(
        options=["ALL"] + _session_ids,
        value="ALL",
        label="Session",
    )

    mo.hstack([event_type_filter, session_filter])
    return event_type_filter, session_filter


@app.cell(hide_code=True)
def _(event_type_filter, mo, raw_data, session_filter):
    _filtered = raw_data.copy()

    if event_type_filter.value != "ALL":
        _filtered = _filtered[_filtered["event_type"] == event_type_filter.value]

    if session_filter.value != "ALL":
        _filtered = _filtered[_filtered["session_id"] == session_filter.value]

    _filtered = _filtered.reset_index(drop=True)

    mo.vstack(
        [
            mo.md(f"### Filtered Events ({len(_filtered):,} rows)"),
            mo.ui.table(_filtered),
        ]
    )
    return


@app.cell(hide_code=True)
def _(mo, raw_data):
    _sorted = raw_data.sort_values(["session_id", "event_order"]).reset_index(drop=True)

    _seq_violations = (
        _sorted.groupby("session_id")["event_order"].diff().dropna().lt(0).sum()
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
                        _gap_summary.sort_values(
                            "total_missing", ascending=False
                        ).reset_index(drop=True)
                    )
                    if len(_gap_summary) > 0
                    else mo.md("✅ No gaps detected — event_order is fully contiguous!"),
                    "All Gap Locations": mo.ui.table(
                        _gap_rows[
                            [
                                "session_id",
                                "machine_id",
                                "event_order",
                                "gap_size",
                                "events_missing",
                                "game_time",
                                "event_type",
                            ]
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
    mo.md(r"""
    ## Metadata
    """)
    return


@app.cell(hide_code=True)
def _(go, mo, raw_data, x_max_input, x_min_input, z_max_input, z_min_input):
    _pos = raw_data[raw_data["event_type"] == "position"].copy()

    _fig = go.Figure()

    if len(_pos) > 0:
        _fig.add_trace(
            go.Scattergl(
                x=_pos["player_pos"].apply(lambda p: p["x"]),
                y=_pos["player_pos"].apply(lambda p: p["z"]),
                mode="markers",
                marker=dict(size=3, opacity=0.3),
                name="Positions",
            )
        )

    _xmin = x_min_input.value
    _xmax = x_max_input.value
    _zmin = z_min_input.value
    _zmax = z_max_input.value

    _fig.add_trace(
        go.Scatter(
            x=[_xmin, _xmax, _xmax, _xmin, _xmin],
            y=[_zmin, _zmin, _zmax, _zmax, _zmin],
            mode="lines",
            line=dict(color="red", dash="dash", width=2),
            name="Bounds",
        )
    )

    _x_range = _xmax - _xmin
    _z_range = _zmax - _zmin
    _fig.update_layout(
        xaxis=dict(title="X", range=[_xmax + 0.25 * _x_range, _xmin - 0.25 * _x_range]),
        yaxis=dict(title="Z", range=[_zmin - 0.25 * _z_range, _zmax + 0.25 * _z_range]),
        height=600,
        showlegend=True,
    )

    mo.ui.plotly(_fig)
    return


@app.cell(hide_code=True)
def _(Path, file_selector, json, mo, raw_data):
    meta_path = Path(file_selector.value).parent / "playtest_metadata.json"
    _defaults = {
        "info": "",
        "bounds": {"x_min": -10000, "x_max": 10000, "z_min": -10000, "z_max": 10000},
    }
    if meta_path.exists():
        with open(meta_path) as _f:
            _meta = json.load(_f)
    else:
        _meta = _defaults
    _bounds = _meta.get("bounds", _defaults["bounds"])
    _info = _meta.get("info", "")
    _saved_types = _meta.get("event_types", [])

    detected_event_types = sorted(raw_data["event_type"].unique().tolist())

    x_min_input = mo.ui.number(value=_bounds["x_min"], label="X Min", step=100)
    x_max_input = mo.ui.number(value=_bounds["x_max"], label="X Max", step=100)
    z_min_input = mo.ui.number(value=_bounds["z_min"], label="Z Min", step=100)
    z_max_input = mo.ui.number(value=_bounds["z_max"], label="Z Max", step=100)
    description_input = mo.ui.text_area(value=_info, label="Description", full_width=True)

    mo.vstack(
        [
            mo.md("### Bounds Editor"),
            mo.hstack([x_min_input, x_max_input, z_min_input, z_max_input]),
            mo.md("### Event Types"),
            mo.md(f"`{', '.join(detected_event_types)}`"),
            mo.md("### Playtest Notes"),
            description_input,
        ]
    )
    return (
        description_input,
        detected_event_types,
        meta_path,
        x_max_input,
        x_min_input,
        z_max_input,
        z_min_input,
    )


@app.cell(hide_code=True)
def excluded_data_points(
    mo,
    raw_data,
    x_max_input,
    x_min_input,
    z_max_input,
    z_min_input,
):
    _pos_data = raw_data[raw_data["player_pos"].notna()].copy()
    _pos_data["_x"] = _pos_data["player_pos"].apply(lambda p: p["x"])
    _pos_data["_z"] = _pos_data["player_pos"].apply(lambda p: p["z"])

    _x_min = x_min_input.value
    _x_max = x_max_input.value
    _z_min = z_min_input.value
    _z_max = z_max_input.value

    excluded_data_points = _pos_data[
        ~(_pos_data["_x"].between(_x_min, _x_max) & _pos_data["_z"].between(_z_min, _z_max))
    ].drop(columns=["_x", "_z"]).reset_index(drop=True)

    _count = len(excluded_data_points)
    _total = len(_pos_data)
    _pct = (_count / _total * 100) if _total > 0 else 0

    mo.vstack([
        mo.md("### Excluded Data Points"),
        mo.callout(
            mo.md(f"**{_count:,}** position events are outside the current bounds ({_pct:.1f}% of {_total:,} position events)"),
            kind="warn" if _count > 0 else "success",
        ),
        mo.ui.table(excluded_data_points) if _count > 0 else mo.md(""),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    save_button = mo.ui.run_button(label="Save")
    save_button
    return (save_button,)


@app.cell(hide_code=True)
def _(
    description_input,
    detected_event_types,
    json,
    meta_path,
    mo,
    save_button,
    x_max_input,
    x_min_input,
    z_max_input,
    z_min_input,
):
    mo.stop(not save_button.value)
    _meta = {
        "info": description_input.value,
        "bounds": {
            "x_min": x_min_input.value,
            "x_max": x_max_input.value,
            "z_min": z_min_input.value,
            "z_max": z_max_input.value,
        },
        "event_types": detected_event_types,
    }
    with open(meta_path, "w") as _f:
        json.dump(_meta, _f, indent=2)
    mo.md("**Metadata saved.**")
    return


if __name__ == "__main__":
    app.run()
