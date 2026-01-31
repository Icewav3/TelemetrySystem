import marimo

__generated_with = "0.19.7"
app = marimo.App()


@app.cell
def _():
    import pandas as pd
    return (pd,)


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
def _(data):
    data.dropna(inplace=True)
    return


@app.cell
def _(data, pd):
    data[['x', 'y']] = data['player_pos'].apply(pd.Series)
    return


if __name__ == "__main__":
    app.run()
