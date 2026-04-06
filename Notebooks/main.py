import marimo

__generated_with = "0.22.0"
app = marimo.App(width="full")


@app.cell
def imports():
    from pathlib import Path

    import altair as alt
    import marimo as mo
    import numpy as np
    import pandas as pd
    import plotly.express as px

    return Path, alt, mo, np, pd, px


@app.cell
def notebook_header(mo):
    mo.md("""
    # Playtester Telemetry Analysis

    This notebook analyzes telemetry data collected from playtesters in order to understand player behavior and identify potential issues within the game level.
    """)
    return


@app.cell
def file_selector_ui(Path, mo):
    data_dir = Path("data")

    available_files = []
    if data_dir.exists():
        for file in data_dir.rglob("*.jsonl"):
            available_files.append(str(file))
    if not available_files:
        raise FileNotFoundError("The 'data' directory is empty")

    file_selector = mo.ui.dropdown(
        options=available_files,
        value=available_files[0] if available_files else None,
        label="Select data file",
        full_width=True,
    )

    file_selector
    return (file_selector,)


@app.cell
def file_guard(file_selector, mo):
    mo.stop(
        not file_selector.value, mo.md("Please select a data file to begin analysis")
    )
    return


@app.cell(hide_code=True)
def load_raw_data(file_selector, pd):
    raw_data = pd.read_json(file_selector.value, lines=True)
    return (raw_data,)


@app.cell(hide_code=True)
def load_metadata(Path, file_selector, mo):
    import json

    _config_path = Path(file_selector.value).parent / "playtest_metadata.json"

    if not _config_path.exists():
        mo.output.append(
            mo.callout("No metadata found, setting bounds absurdly large", kind="warn")
        )
        LEVEL_BOUNDS = {
            "x_min": -99999999999999,
            "x_max": 99999999999999,
            "z_min": -99999999999999,
            "z_max": 99999999999999,
        }
        playtest_info = ""
        known_event_types = []
    else:
        with open(_config_path) as f:
            _config = json.load(f)

        LEVEL_BOUNDS = _config["bounds"]
        playtest_info = _config.get("info", "")
        known_event_types = _config.get("event_types", [])
    return LEVEL_BOUNDS, known_event_types, playtest_info


@app.cell(hide_code=True)
def unpack_bounds(LEVEL_BOUNDS):
    X_MIN = LEVEL_BOUNDS["x_min"]
    X_MAX = LEVEL_BOUNDS["x_max"]
    Z_MIN = LEVEL_BOUNDS["z_min"]
    Z_MAX = LEVEL_BOUNDS["z_max"]
    return X_MAX, X_MIN, Z_MAX, Z_MIN


@app.cell
def pie_toggle(mo):
    include_pie = mo.ui.checkbox(
        label="Include Play in Editor (PIE) data",
        value=False,
    )
    include_pie
    return (include_pie,)


@app.cell(hide_code=True)
def playtest_info(include_pie, mo, pd, playtest_info, raw_data):
    _data = raw_data if include_pie.value or "editor" not in raw_data.columns else raw_data[~raw_data["editor"].fillna(False).astype(bool)]

    _sessions = _data["session_id"].nunique()
    _machines = _data["machine_id"].nunique()
    _events = len(_data)
    _event_types = sorted(_data["event_type"].unique().tolist())
    _time_min = _data["game_time"].min()
    _time_max = _data["game_time"].max()

    _session_durations = _data.groupby("session_id")["game_time"].max()
    _avg_duration = _session_durations.mean()
    _median_duration = _session_durations.median()

    _date_str = ""
    if "server_timestamp" in _data.columns:
        _ts = pd.to_datetime(_data["server_timestamp"])
        _date_str = f"- **Date**: {_ts.min().strftime('%Y-%m-%d')}\n"

    _pie_str = ""
    if "editor" in raw_data.columns:
        _pie_pct = raw_data["editor"].mean() * 100
        _pie_str = f"- **PIE sessions**: {_pie_pct:.1f}% of all events (unfiltered)\n"

    _info_block = f"> {playtest_info}\n\n" if playtest_info else ""

    mo.md(f"""
    ## Playtest Info

    {_info_block}{_date_str}{_pie_str}- **Players (unique sessions)**: {_sessions}
    - **Unique machines**: {_machines}
    - **Total telemetry events**: {_events:,}
    - **Event types**: {', '.join(_event_types)}
    - **Game time range**: {_time_min:.1f}s - {_time_max:.1f}s
    - **Avg session duration**: {_avg_duration:.1f}s
    - **Median session duration**: {_median_duration:.1f}s
    """)
    return


@app.cell(hide_code=True)
def section_user_events(mo):
    mo.md(r"""
    ## Telemetry Events received per user
    """)
    return


@app.cell
def events_per_user(raw_data):
    if "user_name" in raw_data.columns:
        data_per_user = raw_data["user_name"].value_counts()
    else:
        data_per_user = None
    data_per_user
    return


@app.cell(hide_code=True)
def data_transform(X_MAX, X_MIN, Z_MAX, Z_MIN, include_pie, pd, raw_data):
    _data = raw_data if include_pie.value or "editor" not in raw_data.columns else raw_data[~raw_data["editor"].fillna(False).astype(bool)]
    clean_data = _data.dropna(subset=["player_pos"])

    pos_df = clean_data["player_pos"].apply(pd.Series)
    combined_data = pd.concat(
        [
            clean_data.drop("player_pos", axis=1).reset_index(drop=True),
            pos_df.reset_index(drop=True),
        ],
        axis=1,
    )

    level_data = (
        combined_data[
            combined_data["z"].between(Z_MIN, Z_MAX)
            & combined_data["x"].between(X_MIN, X_MAX)
        ]
        .sort_values(["session_id", "server_timestamp"])
    )
    return combined_data, level_data


@app.cell(hide_code=True)
def section_pathing(mo):
    mo.md(r"""
    # Player Pathing Visualization
    """)
    return


@app.cell
def player_pathing(level_data, np, px):
    _dist = np.sqrt(level_data.groupby("session_id")["x"].diff()**2 + level_data.groupby("session_id")["z"].diff()**2)
    _plot = level_data.copy()
    _plot.loc[_dist > 1000, ["x", "z"]] = np.nan

    fig1 = px.line(
        _plot,
        x="x",
        y="z",
        color="session_id",
        title="Player Positions by Session ID over Time",
        labels={"x": "X Coordinate", "z": "Z Coordinate"},
    )
    fig1.update_traces(
        mode="markers+lines", marker=dict(size=5), line=dict(width=1), opacity=0.9
    )
    fig1.update_layout(height=600)
    fig1.update_xaxes(autorange="reversed")
    fig1
    return


@app.cell
def section_velocity(mo):
    mo.md("""
    ## Player Velocity Analysis

    Shows where players speed up or slow down
    """)
    return


@app.cell(hide_code=True)
def compute_velocity(level_data, np):
    velocity_data = level_data.copy()

    velocity_data["dx"] = velocity_data.groupby("session_id")["x"].diff()
    velocity_data["dz"] = velocity_data.groupby("session_id")["z"].diff()
    velocity_data["dt"] = velocity_data.groupby("session_id")["game_time"].diff()

    velocity_data["speed"] = (
        np.sqrt(velocity_data["dx"] ** 2 + velocity_data["dz"] ** 2)
        / velocity_data["dt"]
    )
    velocity_data["speed"] = velocity_data["speed"].replace([np.inf, -np.inf], np.nan)
    velocity_data = velocity_data.dropna(subset=["speed"])

    velocity_data = velocity_data[
        velocity_data["speed"] < velocity_data["speed"].quantile(0.99)
    ]
    return (velocity_data,)


@app.cell
def velocity_scatter(px, velocity_data):
    velocity_scatter = px.scatter(
        velocity_data,
        x="x",
        y="z",
        color="speed",
        color_continuous_scale="Viridis",
        title="Player Speed Throughout Level",
        labels={"x": "X Position", "z": "Z Position", "speed": "Speed (units/s)"},
        opacity=0.6,
    )

    velocity_scatter.update_layout(height=600)
    velocity_scatter.update_xaxes(autorange="reversed")

    velocity_scatter
    return


@app.cell(hide_code=True)
def section_damage(mo):
    mo.md(r"""
    # Damage and Death Analysis
    """)
    return


@app.cell(hide_code=True)
def enrich_run_data(combined_data, known_event_types, mo, pd):
    _has_damage = "damage" in known_event_types or not known_event_types
    mo.stop(not _has_damage, mo.md("*No damage events in this playtest.*"))

    run_cols = combined_data["run_data"].apply(pd.Series)
    enriched_data = pd.concat(
        [
            combined_data.drop("run_data", axis=1).reset_index(drop=True),
            run_cols.reset_index(drop=True),
        ],
        axis=1,
    )
    return (enriched_data,)


@app.cell
def section_damage_map(mo):
    mo.md("""
    ### Damage Events by Source

    Each point is a damage event. Color coding is repersentative of source, while size repersents the amount of damage taken.
    """)
    return


@app.cell
def damage_scatter(enriched_data, mo, px):
    damage_events = enriched_data[
        (enriched_data["event_type"] == "damage")
        & enriched_data["damage_source"].notna()
    ]

    damage_scatter = px.scatter(
        damage_events,
        x="x",
        y="z",
        color="damage_source",
        size="damage",
        opacity=0.7,
        title="Damage Events by Source",
        labels={"x": "X Position", "z": "Z Position", "damage_source": "Source"},
        hover_data=["session_id", "health_before", "health_after", "game_time"],
    )
    damage_scatter.update_layout(height=600)
    damage_scatter.update_xaxes(autorange="reversed")
    mo.ui.plotly(damage_scatter)
    return (damage_events,)


@app.cell
def section_damage_bar(mo):
    mo.md("""
    ### Damage by Source

    Which enemy or hazard is dealing the most damage overall?
    """)
    return


@app.cell
def damage_by_source(alt, damage_events, mo):
    damage_by_source = (
        damage_events.groupby("damage_source")["damage"]
        .sum()
        .reset_index()
        .rename(columns={"damage": "total_damage"})
        .sort_values("total_damage", ascending=False)
    )

    damage_bar = (
        alt.Chart(damage_by_source)
        .mark_bar()
        .encode(
            x=alt.X("total_damage:Q", title="Total Damage Dealt"),
            y=alt.Y("damage_source:N", sort="-x", title="Damage Source"),
            color=alt.Color("damage_source:N", legend=None),
            tooltip=["damage_source", "total_damage"],
        )
        .properties(title="Total Damage by Source", width=600, height=300)
    )
    mo.ui.altair_chart(damage_bar)
    return


@app.cell
def section_health(mo):
    mo.md("""
    ### Player Health Over Time

    This shows how the player's health decreases over the duration of their run.

    **IMPORTANT NOTE:** This does NOT correspond to position in the level, this is over time.
    """)
    return


@app.cell
def health_over_time(enriched_data, mo, px):
    health_events = enriched_data[enriched_data["health_after"].notna()].sort_values(
        ["session_id", "game_time"]
    )

    health_fig = px.line(
        health_events,
        x="game_time",
        y="health_after",
        color="session_id",
        title="Health Over Time by Session",
        labels={"game_time": "Game Time (s)", "health_after": "Health"},
        hover_data=["damage_source", "damage"],
    )
    health_fig.update_layout(height=500)
    mo.ui.plotly(health_fig)
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
