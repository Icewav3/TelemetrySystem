import marimo

__generated_with = "0.19.7"
app = marimo.App()


@app.cell
def _():
    import pandas as pd
    import plotly.express as px
    import plotly.graph_objects as go
    import numpy as np
    return pd, px


@app.cell
def _(pd):
    data = pd.read_json("telemetry_data/telemetry.jsonl", lines=True)
    return (data,)


@app.cell
def _(data):
    data
    return


@app.cell
def _(data):
    data['player_pos']
    return


@app.cell
def _(data, pd):
    # First, drop rows with null player_pos values
    clean_data = data.dropna(subset=['player_pos'])

    # Extract x and y coordinates from player_pos
    pos_df = clean_data['player_pos'].apply(pd.Series)
    # merge extracted coordinates back into the original dataframe
    combined_data = pd.concat([
        clean_data.drop('player_pos', axis=1).reset_index(drop=True),
        pos_df.reset_index(drop=True)
    ], axis=1)

    combined_data
    return (combined_data,)


@app.cell
def _(combined_data, px):
    fig1 = px.line(combined_data, x='x', y='y', color='session_id', title="Player Positions by Session ID", labels={"x": "X Coordinate", "y": "Y Coordinate"})
    fig1.update_traces(
        mode='markers+lines', 
        marker=dict(size=5),
        line=dict(width=1)
        )
    fig1
    return


@app.cell
def _(combined_data, px):
    anim_data = combined_data.copy()
    # Create a relative frame number for animation
    anim_data['relative_frame'] = anim_data.groupby('session_id')['frame'].transform(
        lambda x: x - x.min()
    )

    fig2 = px.scatter(
        anim_data,
        x='x',
        y='y',
        animation_frame='relative_frame',  # Animate by this column
        animation_group='session_id',      # Group points by session
        color='session_id',
        range_x=[anim_data['x'].min()-100, anim_data['x'].max()+100],
        range_y=[anim_data['y'].min()-100, anim_data['y'].max()+100],
    )

    fig2.update_traces(marker=dict(size=10))
    fig2.update_layout(title='Animated Player Positions', height=600)
    fig2
    return


if __name__ == "__main__":
    app.run()
