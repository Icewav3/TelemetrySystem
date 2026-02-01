import marimo

__generated_with = "0.19.7"
app = marimo.App()


@app.cell
def _():
    import pandas as pd
    import plotly.express as px
    import plotly.graph_objects as go
    import numpy as np
    import altair as alt
    import marimo as mo
    return alt, mo, pd, px


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
    clean_data = data.dropna(subset=['player_pos'])

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
def _(combined_data, pd, px):
    anim_data = combined_data.copy()
    anim_data['relative_frame'] = anim_data.groupby('session_id')['frame'].transform(
        lambda x: x - x.min()
    )
    anim_data = anim_data.sort_values(['session_id', 'relative_frame'])

    # Create cumulative dataset
    cumulative_data = []
    for frame in sorted(anim_data['relative_frame'].unique()):
        # Get all data up to and including this frame for each session
        frame_data = anim_data[anim_data['relative_frame'] <= frame].copy()
        frame_data['animation_frame'] = frame  # All historical points 
        cumulative_data.append(frame_data)

    cumulative_df = pd.concat(cumulative_data, ignore_index=True)

    # Now animate with the cumulative data
    fig2 = px.line(
        cumulative_df,
        x='x',
        y='y',
        animation_frame='animation_frame',
        color='session_id',
        line_group='session_id',
        range_x=[anim_data['x'].min()-100, anim_data['x'].max()+100],
        range_y=[anim_data['y'].min()-100, anim_data['y'].max()+100],
    )

    fig2.update_traces(
        mode='markers+lines',
        line=dict(width=2),
        marker=dict(size=5, opacity=1.0),  # Full opacity for markers
        opacity=0.4  # This applies to the line portion
    )

    # Override marker opacity to be full
    for trace in fig2.data:
        trace.marker.opacity = 1.0

    fig2.update_layout(title='Animated Player Pathing with Trails', height=600)
    fig2
    return


@app.cell
def _(mo):
    mo.md(r"""
    ### messing around
    """)
    return


@app.cell
def _(alt, combined_data, mo, pd):
    heatmap_data = combined_data.copy()
    heatmap_data['x_bin'] = pd.cut(heatmap_data['x'], bins=25)
    heatmap_data['y_bin'] = pd.cut(heatmap_data['y'], bins=25)

    heat = heatmap_data.groupby(['x_bin', 'y_bin']).size().reset_index(name='count')
    heat['x_mid'] = heat['x_bin'].apply(lambda x: x.mid)
    heat['y_mid'] = heat['y_bin'].apply(lambda x: x.mid)

    chart = alt.Chart(heat).mark_rect().encode(
        x=alt.X('x_mid:Q', title='X Position'),
        y=alt.Y('y_mid:Q', title='Y Position'),
        color=alt.Color('count:Q', scale=alt.Scale(scheme='reds'), title='Activity'),
        tooltip=['count:Q']
    ).properties(
        width=700,
        height=600,
        title='Player Activity Heatmap'
    )

    mo.ui.altair_chart(chart)
    return


if __name__ == "__main__":
    app.run()
