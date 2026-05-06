# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "marimo>=0.20.4",
# ]
# ///

import marimo

__generated_with = "0.23.2"
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
    ## Schema Validation

    Validates every event against `telemetry.schema.json`. The schema is the source of truth — see `data/README.md` for time-model and editor-vs-build naming notes that are not enforceable in JSON Schema.
    """)
    return


@app.cell(hide_code=True)
def _(Path, json):
    _schema_path = Path(__file__).parent.parent / "telemetry.schema.json"
    with open(_schema_path) as _f:
        schema = json.load(_f)
    return (schema,)


@app.cell(hide_code=True)
def _(pd, raw_data):
    def _clean(rec):
        # pandas turns absent JSONL keys into NaN; drop those so checks see true absence
        return {
            k: v for k, v in rec.items() if not (isinstance(v, float) and pd.isna(v))
        }

    records = [_clean(r) for r in raw_data.to_dict(orient="records")]
    return (records,)


@app.cell(hide_code=True)
def _(mo, pd, records, schema):
    def _is_empty(v):
        if v is None:
            return True
        if isinstance(v, str) and v == "":
            return True
        if isinstance(v, float) and pd.isna(v):
            return True
        return False

    def _status(passed, total):
        if total == 0:
            return "—", "no applicable events"
        pct = passed / total * 100
        if passed == total:
            return "✅", f"{passed:,} / {total:,} (100%)"
        if passed == 0:
            return "❌", f"{passed:,} / {total:,} (0%)"
        return "⚠️", f"{passed:,} / {total:,} ({pct:.1f}%)"

    # Build per-event-type required-field map from the schema's oneOf branches
    _branches = {}
    for _b in schema.get("oneOf", []):
        _props = _b.get("properties", {})
        _et = _props.get("event_type", {}).get("const")
        if _et:
            _branches[_et] = list(_b.get("required", []))

    _checks = []

    def _add(section, field, applies_to, predicate, applicable_filter=None):
        applicable = [r for r in records if (applicable_filter is None or applicable_filter(r))]
        passed = sum(1 for r in applicable if predicate(r))
        s, d = _status(passed, len(applicable))
        _checks.append(
            {
                "Section": section,
                "Field / Rule": field,
                "Applies to": applies_to,
                "Status": s,
                "Pass / Total": d,
            }
        )

    # ---- Top-level required fields ----
    for _f in schema.get("required", []):
        if _f == "run_data":
            _add("Top-level required", _f, "all events",
                 lambda r, k=_f: isinstance(r.get(k), dict))
        else:
            _add("Top-level required", _f, "all events",
                 lambda r, k=_f: not _is_empty(r.get(k)))

    # ---- run_data sub-fields (required by schema on every event) ----
    _rd_required = schema["properties"]["run_data"].get("required", [])
    for _f in _rd_required:
        _add("run_data sub-field present", _f, "all events",
             lambda r, k=_f: isinstance(r.get("run_data"), dict) and k in r["run_data"])

    # ---- run_data semantic checks (during active runs only) ----
    _sorted = sorted(records, key=lambda r: (r.get("session_id", ""), r.get("event_order", 0)))
    _active = {}
    _during_run_ids = set()
    for _i, _r in enumerate(_sorted):
        _sid = _r.get("session_id")
        _et = _r.get("event_type")
        if _et == "run_start":
            _active[_sid] = True
        in_run = _active.get(_sid, False)
        if in_run:
            _during_run_ids.add(id(_r))
        if _et == "run_end":
            _active[_sid] = False

    def _during(r):
        return id(r) in _during_run_ids

    _add("run_data semantic coverage", "run_id non-empty",
         "events between run_start..run_end (inclusive)",
         lambda r: isinstance(r.get("run_data"), dict) and not _is_empty(r["run_data"].get("run_id")),
         applicable_filter=_during)

    _add("run_data semantic coverage", "run_start_time > 0",
         "events during an active run (key is present always; this checks it's actually populated)",
         lambda r: isinstance(r.get("run_data"), dict) and (r["run_data"].get("run_start_time") or 0) > 0,
         applicable_filter=_during)

    _add("run_data semantic coverage", "run_end_time > 0",
         "`run_end` events only",
         lambda r: isinstance(r.get("run_data"), dict) and (r["run_data"].get("run_end_time") or 0) > 0,
         applicable_filter=lambda r: r.get("event_type") == "run_end")

    _add("run_data semantic coverage", "run_total_time > 0",
         "`run_end` events only",
         lambda r: isinstance(r.get("run_data"), dict) and (r["run_data"].get("run_total_time") or 0) > 0,
         applicable_filter=lambda r: r.get("event_type") == "run_end")

    _add("run_data semantic coverage", "end_reason non-empty",
         "`run_end` events only",
         lambda r: isinstance(r.get("run_data"), dict) and not _is_empty(r["run_data"].get("end_reason")),
         applicable_filter=lambda r: r.get("event_type") == "run_end")

    # ---- Per-event-type required fields (oneOf branches) ----
    for _et, _required in _branches.items():
        _filt = (lambda et: lambda r: r.get("event_type") == et)(_et)
        for _f in _required:
            if _f == "player_pos":
                _add(f"`{_et}` required", _f, f"`{_et}` events",
                     lambda r, k=_f: isinstance(r.get(k), dict)
                     and not _is_empty(r[k].get("x"))
                     and not _is_empty(r[k].get("z")),
                     applicable_filter=_filt)
            else:
                _add(f"`{_et}` required", _f, f"`{_et}` events",
                     lambda r, k=_f: not _is_empty(r.get(k)),
                     applicable_filter=_filt)

    # ---- player_pos shape (when present, must have x and z) ----
    _add("player_pos shape", "x and z both present (when player_pos is emitted)",
         "events with a player_pos object",
         lambda r: not _is_empty(r["player_pos"].get("x")) and not _is_empty(r["player_pos"].get("z")),
         applicable_filter=lambda r: isinstance(r.get("player_pos"), dict) and len(r["player_pos"]) > 0)

    _add("player_pos shape", "no empty `{}` (omit instead)", "all events",
         lambda r: not (isinstance(r.get("player_pos"), dict) and len(r["player_pos"]) == 0))

    # ---- Deprecated fields should not appear ----
    _add("Deprecated fields", "no `packed_level_instance` (deprecated → use `rooms`)",
         "all events",
         lambda r: "packed_level_instance" not in r)
    _add("Deprecated fields", "no `packed_level_actor` (deprecated)",
         "all events",
         lambda r: "packed_level_actor" not in r)

    _results = pd.DataFrame(_checks)
    _passes = (_results["Status"] == "✅").sum()
    _warns = (_results["Status"] == "⚠️").sum()
    _fails = (_results["Status"] == "❌").sum()
    _na = (_results["Status"] == "—").sum()

    _banner = mo.callout(
        mo.md(
            f"**{_passes} pass · {_warns} partial · {_fails} fail · {_na} n/a** "
            f"across {len(_results)} schema rules · {len(records):,} events"
        ),
        kind="success" if _fails == 0 and _warns == 0 else ("warn" if _fails == 0 else "danger"),
    )

    _by_section = {}
    for _section, _grp in _results.groupby("Section", sort=False):
        _by_section[_section] = mo.ui.table(_grp.reset_index(drop=True), selection=None)

    mo.vstack(
        [
            _banner,
            mo.ui.table(_results, selection=None),
            mo.md("### Per-Section Detail"),
            mo.ui.tabs(_by_section),
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
