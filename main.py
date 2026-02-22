import marimo

__generated_with = "0.19.11"
app = marimo.App(width="full")


@app.cell
def _():
    import marimo as mo
    import pandas as pd
    import plotly.express as px
    import plotly.graph_objects as go
    import numpy as np
    import altair as alt
    from pathlib import Path

    return Path, alt, mo, np, pd, px


@app.cell
def _(mo):
    mo.md("""
    # Playtester Telemetry Analysis
    This notebook analyzes telemetry data collected from playtesters in order to understand player behavior and identify potential issues within the game level.
    """)
    return


@app.cell
def _(Path, mo):
    data_dir = Path("data")

    available_files = []
    if data_dir.exists():
        for subdir in data_dir.iterdir():
            if subdir.is_dir():
                for file in subdir.glob("*.jsonl"):
                    available_files.append(str(file))
    if not available_files:
        raise FileNotFoundError("The 'data' directory is empty")

    file_selector = mo.ui.dropdown(
        options=available_files,
        value=available_files[0] if available_files else None,
        label="Select data file",
        full_width=True
    )

    file_selector
    return (file_selector,)


@app.cell
def _(file_selector, mo):
    mo.stop(not file_selector.value, mo.md("Please select a data file to begin analysis"))
    return


@app.cell
def _(file_selector, pd):
    raw_data = pd.read_json(file_selector.value, lines=True)
    return (raw_data,)


@app.cell
def _(Path, file_selector):
    import json

    _config_path = Path(file_selector.value).parent / "playtest_metadata.json"

    if not _config_path.exists():
        raise FileNotFoundError(f"No playtest_metadata.json found in {_config_path.parent}")

    with open(_config_path) as f:
        _config = json.load(f)

    LEVEL_BOUNDS = _config["bounds"]
    return (LEVEL_BOUNDS,)


@app.cell
def _(LEVEL_BOUNDS):
    X_MIN = LEVEL_BOUNDS["x_min"]
    X_MAX = LEVEL_BOUNDS["x_max"]
    Z_MIN = LEVEL_BOUNDS["z_min"]
    Z_MAX = LEVEL_BOUNDS["z_max"]
    return X_MAX, X_MIN, Z_MAX, Z_MIN


@app.cell
def _(mo, raw_data):
    mo.md(f"""
    ## Data Summary

    - **Total records**: {len(raw_data):,}
    - **Unique sessions**: {raw_data['session_id'].nunique()}
    - **Time range**: {raw_data['game_time'].min():.1f}s - {raw_data['game_time'].max():.1f}s
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ## Telemetry Events recieved per user
    """)
    return


@app.cell
def _(raw_data):
    if 'user_name' in raw_data.columns:
        data_per_user = raw_data['user_name'].value_counts()
    else:
        data_per_user = None
    data_per_user
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Preview of the raw data
    """)
    return


@app.cell
def _(pd, raw_data):
    clean_data = raw_data.dropna(subset=['player_pos'])

    # Extract x and y
    pos_df = clean_data['player_pos'].apply(pd.Series)
    # merge extracted coordinates back into the original dataframe
    combined_data = pd.concat([
        clean_data.drop('player_pos', axis=1).reset_index(drop=True),
        pos_df.reset_index(drop=True)
    ], axis=1)

    combined_data
    return (combined_data,)


@app.cell
def _(mo):
    mo.md("""
    ## Data Cleaning Pipeline

    Removing outliers and invalid data points.
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ### Showcase of what raw data graphed looks like
    """)
    return


@app.cell
def _(combined_data, px):
    uncleanGraph = px.line(combined_data, x='x', y='z', color='session_id', 
                   title="Player Positions by Session ID", 
                   labels={"x": "X Coordinate", "z": "Z Coordinate"})
    uncleanGraph.update_traces(
        mode='markers+lines', 
        marker=dict(size=5),
        line=dict(width=1)
    )
    uncleanGraph.update_layout(height=600)
    uncleanGraph.update_xaxes(autorange="reversed")   
    uncleanGraph
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Drop players who went out of bounds
    """)
    return


@app.cell
def _(mo):
    mo.md(r"""
    ### Drop data from players who fell off the map
    """)
    return


@app.cell
def _(Z_MAX, Z_MIN, combined_data):
    level_data_trim_z = combined_data[combined_data['z'].between(Z_MIN, Z_MAX)]
    return (level_data_trim_z,)


@app.cell
def _(mo):
    mo.md(r"""
    ### Temporal data
    """)
    return


@app.cell
def _(level_data_trim_z):
    temporal_chart = level_data_trim_z
    temporal_chart
    return


@app.cell
def _(mo):
    mo.md(r"""
    ### Drop data from people who have passed the end of the level
    """)
    return


@app.cell
def _(X_MAX, X_MIN, level_data_trim_z):
    level_data_trim_x = level_data_trim_z[level_data_trim_z['x'].between(X_MIN, X_MAX)]
    level_data = level_data_trim_x
    return (level_data,)


@app.cell
def _(mo):
    mo.md(r"""
    ### Sort data
    """)
    return


@app.cell
def _(level_data):
    sorted_level_data = level_data.sort_values(["session_id", "game_time"])
    return (sorted_level_data,)


@app.cell(hide_code=True)
def _(mo, sorted_level_data):
    mo.md(f"""
    ### Ensure all data is in correct time sequence

    - **Time sequence violations**: {sorted_level_data.groupby("session_id")["game_time"].diff().dropna().lt(0).sum()}
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Player Pathing visualizaton
    """)
    return


@app.cell
def _(level_data, px):
    fig1 = px.line(level_data, x='x', y='z', color='session_id', 
                   title="Player Positions by Session ID over Time", 
                   labels={"x": "X Coordinate", "z": "Z Coordinate"})
    fig1.update_traces(
        mode='markers+lines', 
        marker=dict(size=5),
        line=dict(width=1),
        opacity=0.9
    )
    fig1.update_layout(height=600)
    fig1.update_xaxes(autorange="reversed")   
    fig1
    return


@app.cell
def _(mo):
    mo.md("""
    ## Player Velocity Analysis

    Shows where players speed up or slow down
    """)
    return


@app.cell
def _(np, sorted_level_data):
    velocity_data = sorted_level_data.copy()

    velocity_data['dx'] = velocity_data.groupby('session_id')['x'].diff()
    velocity_data['dz'] = velocity_data.groupby('session_id')['z'].diff()
    velocity_data['dt'] = velocity_data.groupby('session_id')['game_time'].diff()

    velocity_data['speed'] = np.sqrt(velocity_data['dx']**2 + velocity_data['dz']**2) / velocity_data['dt']
    velocity_data['speed'] = velocity_data['speed'].replace([np.inf, -np.inf], np.nan)
    velocity_data = velocity_data.dropna(subset=['speed'])

    velocity_data = velocity_data[velocity_data['speed'] < velocity_data['speed'].quantile(0.99)]

    velocity_data
    return (velocity_data,)


@app.cell
def _(px, velocity_data):
    velocity_scatter = px.scatter(
        velocity_data,
        x='x',
        y='z',
        color='speed',
        color_continuous_scale='Viridis',
        title='Player Speed Throughout Level',
        labels={'x': 'X Position', 'z': 'Z Position', 'speed': 'Speed (units/s)'},
        opacity=0.6
    )

    velocity_scatter.update_layout(height=600)
    velocity_scatter.update_xaxes(autorange="reversed")

    velocity_scatter
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Damage and Death Analysis
    """)
    return


@app.cell
def _(combined_data, mo):
    if not combined_data['damage'].sum() and not combined_data['death'].sum():
        print("No damage or death events detected. Stopping monitoring.")
        mo.stop()
    return


@app.cell
def _(mo):
    mo.md("""
    ## Damage & Death Analysis

    Using the new telemetry fields: `event_type`, `damage`, `health_before`, `health_after`, `damage_source`, `run_data`.
    """)
    return


@app.cell
def _(combined_data, pd):
    # Expand run_data dict into columns
    run_cols = combined_data['run_data'].apply(pd.Series)
    enriched_data = pd.concat([
        combined_data.drop('run_data', axis=1).reset_index(drop=True),
        run_cols.reset_index(drop=True)
    ], axis=1)
    enriched_data
    return (enriched_data,)


@app.cell
def _(mo):
    mo.md("""
    ### Damage Events by Source

    Each point is a damage event. Color coding is repersentative of source, while size repersents the amount of damage taken.
    """)
    return


@app.cell
def _(enriched_data, mo, px):
    damage_events = enriched_data[
        (enriched_data['event_type'] == 'damage') & enriched_data['damage_source'].notna()
    ]

    damage_scatter = px.scatter(
        damage_events,
        x='x',
        y='z',
        color='damage_source',
        size='damage',
        opacity=0.7,
        title='Damage Events by Source',
        labels={'x': 'X Position', 'z': 'Z Position', 'damage_source': 'Source'},
        hover_data=['session_id', 'health_before', 'health_after', 'game_time']
    )
    damage_scatter.update_layout(height=600)
    damage_scatter.update_xaxes(autorange="reversed")
    mo.ui.plotly(damage_scatter)
    return (damage_events,)


@app.cell
def _(mo):
    mo.md("""
    ### Damage by Source

    Which enemy or hazard is dealing the most damage overall?
    """)
    return


@app.cell
def _(alt, damage_events, mo):
    damage_by_source = (
        damage_events.groupby('damage_source')['damage']
        .sum()
        .reset_index()
        .rename(columns={'damage': 'total_damage'})
        .sort_values('total_damage', ascending=False)
    )

    damage_bar = (
        alt.Chart(damage_by_source)
        .mark_bar()
        .encode(
            x=alt.X('total_damage:Q', title='Total Damage Dealt'),
            y=alt.Y('damage_source:N', sort='-x', title='Damage Source'),
            color=alt.Color('damage_source:N', legend=None),
            tooltip=['damage_source', 'total_damage']
        )
        .properties(title='Total Damage by Source', width=600, height=300)
    )
    mo.ui.altair_chart(damage_bar)
    return


@app.cell
def _(mo):
    mo.md("""
    ### Player Health Over Time

    This shows how the player's health decreases over the duration of their run.

    **IMPORTANT NOTE:** This does NOT correspond to position in the level, this is over time.
    """)
    return


@app.cell
def _(enriched_data, mo, px):
    health_events = enriched_data[
        enriched_data['health_after'].notna()
    ].sort_values(['session_id', 'game_time'])

    health_fig = px.line(
        health_events,
        x='game_time',
        y='health_after',
        color='session_id',
        title='Health Over Time by Session',
        labels={'game_time': 'Game Time (s)', 'health_after': 'Health'},
        hover_data=['damage_source', 'damage']
    )
    health_fig.update_layout(height=500)
    mo.ui.plotly(health_fig)
    return


if __name__ == "__main__":
    app.run()
