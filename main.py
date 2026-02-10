import marimo

__generated_with = "0.19.9"
app = marimo.App(width="full")


@app.cell
def _():
    import marimo as mo
    import pandas as pd
    import polars as pl
    import plotly.express as px
    import plotly.graph_objects as go
    import numpy as np
    import altair as alt
    from pathlib import Path

    return Path, mo, np, pd, px


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
    	available_files = [
    		"data/test_data/telemetry.jsonl",
    		"data/playtest1_data/telemetry_testers.jsonl"
    	]

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
def _(mo, raw_data):
    mo.md(f"""
    ## Data Summary

    - **Total records**: {len(raw_data):,}
    - **Unique sessions**: {raw_data['session_id'].nunique()}
    - **Time range**: {raw_data['game_time'].min():.1f}s - {raw_data['game_time'].max():.1f}s
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
    ### Showcase of raw data
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


@app.cell
def _(mo):
    mo.md(r"""
    ### Drop data from players who fell off the map
    """)
    return


@app.cell
def _(combined_data):
    level_data_trim_z = combined_data[combined_data['z'] >= -70]
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
def _(level_data_trim_z):
    level_data_trim_x = level_data_trim_z[level_data_trim_z['x'] >= -7500]

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


@app.cell
def _(mo):
    mo.md(r"""
    ### Ensure all data is in correct time sequence
    """)
    return


@app.cell
def _(sorted_level_data):
    sorted_level_data.groupby("session_id")["game_time"].diff().dropna().lt(0).sum()
    return


@app.cell
def _(level_data, px):
    fig1 = px.line(level_data, x='x', y='z', color='session_id', 
    			   title="Player Positions by Session ID", 
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

    Shows where players speed up or slow down which can show
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


if __name__ == "__main__":
    app.run()
