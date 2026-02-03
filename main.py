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
    return mo, pd, px


@app.cell
def _(pd):
    testing_data= pd.read_json("data/test_data/telemetry.jsonl", lines=True)
    playtest1_dev_data= pd.read_json("data/playtest1_data/telemetry_testers.jsonl", lines=True)
    playtest1_tester_data= pd.read_json("data/playtest1_data/telemetry_testers.jsonl", lines=True)
    return (playtest1_tester_data,)


@app.cell
def _(playtest1_tester_data):
    playtest1_tester_data
    return


@app.cell
def _(playtest1_tester_data):
    playtest1_tester_data['player_pos']
    return


@app.cell
def _(pd, playtest1_tester_data):
    clean_data = playtest1_tester_data.dropna(subset=['player_pos'])

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
def _(combined_data):
    # # drop end of level
    level_data_trim_x = combined_data[combined_data['x'] >= -7500]
    level_data_trim_z = level_data_trim_x[level_data_trim_x['z'] >= -70]
    level_data = level_data_trim_z
    return (level_data,)


@app.cell
def _():
    # speedrun_data = level_data.query
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
def _(level_data, px):
    fig1 = px.line(level_data, x='x', y='z', color='session_id', 
                   title="Player Positions by Session ID", 
                   labels={"x": "X Coordinate", "z": "Z Coordinate"})
    fig1.update_traces(
        mode='markers+lines', 
        marker=dict(size=5),
        line=dict(width=1)
    )
    fig1.update_layout(height=600)
    fig1.update_xaxes(autorange="reversed")   
    fig1
    return


@app.cell
def _():
    # dwell_data = combined_data.copy()
    # dwell_data['x_zone'] = pd.cut(dwell_data['x'], bins=10)
    # dwell_data['z_zone'] = pd.cut(dwell_data['z'], bins=10)

    # dwell = dwell_data.groupby(['x_zone', 'z_zone']).size().reset_index(name='dwell_time')
    # dwell['x_mid'] = dwell['x_zone'].apply(lambda x: x.mid)
    # dwell['z_mid'] = dwell['z_zone'].apply(lambda x: x.mid)

    # fig5 = alt.Chart(dwell).mark_rect().encode(
    #     x=alt.X('x_mid:Q', title='X Zone (Right)'),
    #     y=alt.Y('z_mid:Q', title='Z Zone (Up)'),
    #     color=alt.Color('dwell_time:Q', scale=alt.Scale(scheme='orangered'), title='Frames Spent'),
    #     tooltip=['x_mid:Q', 'z_mid:Q', 'dwell_time:Q']
    # ).properties(
    #     width=700,
    #     height=600,
    #     title='Dwell Time Heatmap - Where Players Linger'
    # )

    # mo.ui.altair_chart(fig5)
    return


@app.cell
def _():
    # anim_data = level_data.copy()
    # anim_data['relative_frame'] = anim_data.groupby('session_id')['frame'].transform(
    #     lambda x: x - x.min()
    # )
    # anim_data = anim_data.sort_values(['session_id', 'relative_frame'])

    # # Create cumulative dataset
    # cumulative_data = []
    # for frame in sorted(anim_data['relative_frame'].unique()):
    #     # Get all data up to and including this frame for each session
    #     frame_data = anim_data[anim_data['relative_frame'] <= frame].copy()
    #     frame_data['animation_frame'] = frame  # All historical points 
    #     cumulative_data.append(frame_data)

    # cumulative_df = pd.concat(cumulative_data, ignore_index=True)

    # # Now animate with the cumulative data
    # fig2 = px.line(
    #     cumulative_df,
    #     x='x',
    #     y='y',
    #     animation_frame='animation_frame',
    #     color='session_id',
    #     line_group='session_id',
    #     range_x=[anim_data['x'].min()-100, anim_data['x'].max()+100],
    #     range_y=[anim_data['y'].min()-100, anim_data['y'].max()+100],
    # )

    # fig2.update_traces(
    #     mode='markers+lines',
    #     line=dict(width=2),
    #     marker=dict(size=5, opacity=1.0),  # Full opacity for markers
    #     opacity=0.4  # This applies to the line portion
    # )

    # # Override marker opacity to be full
    # for trace in fig2.data:
    #     trace.marker.opacity = 1.0

    # fig2.update_layout(title='Animated Player Pathing with Trails', height=600)
    # fig2.update_xaxes(autorange="reversed")   
    # fig2
    return


@app.cell
def _(mo):
    mo.md(r"""
    ### messing around
    """)
    return


@app.cell
def _():
    # heatmap_data = combined_data.copy()
    # heatmap_data['x_bin'] = pd.cut(heatmap_data['x'], bins=25)
    # heatmap_data['y_bin'] = pd.cut(heatmap_data['y'], bins=25)

    # heat = heatmap_data.groupby(['x_bin', 'y_bin']).size().reset_index(name='count')
    # heat['x_mid'] = heat['x_bin'].apply(lambda x: x.mid)
    # heat['y_mid'] = heat['y_bin'].apply(lambda x: x.mid)

    # chart = alt.Chart(heat).mark_rect().encode(
    #     x=alt.X('x_mid:Q', title='X Position'),
    #     y=alt.Y('y_mid:Q', title='Y Position'),
    #     color=alt.Color('count:Q', scale=alt.Scale(scheme='reds'), title='Activity'),
    #     tooltip=['count:Q']
    # ).properties(
    #     width=700,
    #     height=600,
    #     title='Player Activity Heatmap'
    # )

    # mo.ui.altair_chart(chart)
    return


if __name__ == "__main__":
    app.run()
