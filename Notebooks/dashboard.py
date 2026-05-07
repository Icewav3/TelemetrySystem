import marimo

__generated_with = "0.23.5"
app = marimo.App(width="full")


@app.cell
def _():
    import datetime as dt
    import json
    import math
    import re
    import time
    from collections import deque
    from pathlib import Path

    import marimo as mo
    import numpy as np
    import orjson
    import plotly.graph_objects as go
    from scipy.ndimage import gaussian_filter

    DATA_PATH = Path("data/telemetry.jsonl")
    META_PATH = Path("data/playtest6_external/playtest_metadata.json")

    MAX_KIOSKS = 4
    TRAIL_POINTS = 400
    HEATMAP_GRID = 140
    BLUR_SIGMA = 2.5
    TRAIL_FADE_SECS = 20
    AUTO_CYCLE_IDLE_SECS = 30
    AUTO_CYCLE_INTERVAL_SECS = 15

    SESSION_PALETTE = ["#4FC3F7", "#FF7043", "#81C784", "#BA68C8"]
    return (
        AUTO_CYCLE_IDLE_SECS,
        AUTO_CYCLE_INTERVAL_SECS,
        BLUR_SIGMA,
        DATA_PATH,
        HEATMAP_GRID,
        MAX_KIOSKS,
        META_PATH,
        SESSION_PALETTE,
        TRAIL_FADE_SECS,
        TRAIL_POINTS,
        deque,
        dt,
        gaussian_filter,
        go,
        json,
        math,
        mo,
        np,
        orjson,
        re,
        time,
    )


@app.cell
def _(mo):
    mo.md("""
    <style>
    @keyframes ts_pulse {
      0%   { opacity: 1.0; box-shadow: 0 0 0 0 rgba(76, 217, 100, 0.6); }
      70%  { opacity: 0.6; box-shadow: 0 0 0 10px rgba(76, 217, 100, 0); }
      100% { opacity: 1.0; box-shadow: 0 0 0 0 rgba(76, 217, 100, 0); }
    }
    </style>
    <div style="
        display: flex; align-items: center; gap: 14px;
        padding: 14px 22px; background: linear-gradient(90deg, #0d1117 0%, #1a1d23 100%);
        border-bottom: 1px solid #2a2f38; border-radius: 4px;
    ">
      <span style="
          display: inline-block; width: 12px; height: 12px;
          background: #4cd964; border-radius: 50%;
          animation: ts_pulse 1.6s infinite;
      "></span>
      <span style="
          color: #f5f5f5; font-size: 28px; font-weight: 700;
          letter-spacing: 4px;
      ">TELEMETRY</span>
      <span style="color: #4cd964; font-size: 14px; font-weight: 600; letter-spacing: 3px;">LIVE</span>
    </div>
    """)
    return


@app.cell
def _(META_PATH, json):
    # Bounds are read for plot framing only; no UI surface.
    with open(META_PATH) as f:
        _metadata = json.load(f)
    BOUNDS = _metadata["bounds"]
    return (BOUNDS,)


@app.cell
def _(HEATMAP_GRID, deque, mo, np):
    get_cursor, set_cursor = mo.state(0)
    get_heatmaps, set_heatmaps = mo.state(
        {
            "deaths": np.zeros((HEATMAP_GRID, HEATMAP_GRID), dtype=np.int32),
            "damage": np.zeros((HEATMAP_GRID, HEATMAP_GRID), dtype=np.float32),
            "positions": np.zeros((HEATMAP_GRID, HEATMAP_GRID), dtype=np.int32),
        }
    )
    get_trails, set_trails = mo.state({})
    get_session_meta, set_session_meta = mo.state({})
    get_recent_deaths, set_recent_deaths = mo.state(deque(maxlen=20))
    get_stats, set_stats = mo.state(
        {
            "total_deaths": 0,
            "total_damage": 0.0,
            "active_sessions": 0,
            "peak_concurrent": 0,
            "events_per_sec": 0.0,
            "total_events": 0,
        }
    )
    get_last_error, set_last_error = mo.state(None)
    get_schema_versions, set_schema_versions = mo.state(set())
    get_event_arrivals, set_event_arrivals = mo.state(deque(maxlen=2000))
    get_run_fallback, set_run_fallback = mo.state({})
    get_cause_counts, set_cause_counts = mo.state({})
    get_auto_cycle, set_auto_cycle = mo.state(
        {"index": 0, "last_change": 0.0, "last_user": 0.0}
    )
    # Plot snapshot — frozen view of state at last throttled tick. Plot cell
    # depends ONLY on this, so it reruns when (and only when) we actually
    # publish a new snap. The `sig` field is the change-detection hash;
    # `last_plot_t` enforces a wall-clock floor on rebuild rate. Together
    # these eliminate the grey-out flicker from too-frequent Plotly replaces.
    get_plot_snap, set_plot_snap = mo.state(
        {
            "sig": None,
            "view": "Live Arena",
            "trails": {},
            "session_meta": {},
            "deaths": [],
            "heatmaps": None,
        }
    )
    get_last_plot_t, set_last_plot_t = mo.state(0.0)
    return (
        get_auto_cycle,
        get_cause_counts,
        get_cursor,
        get_event_arrivals,
        get_heatmaps,
        get_last_plot_t,
        get_plot_snap,
        get_recent_deaths,
        get_run_fallback,
        get_schema_versions,
        get_session_meta,
        get_stats,
        get_trails,
        set_auto_cycle,
        set_cause_counts,
        set_cursor,
        set_event_arrivals,
        set_heatmaps,
        set_last_error,
        set_last_plot_t,
        set_plot_snap,
        set_recent_deaths,
        set_run_fallback,
        set_schema_versions,
        set_session_meta,
        set_stats,
        set_trails,
    )


@app.cell
def _(mo):
    # Two-tier refresh: data ingest is fast (live stats), plot rebuilds slow
    # (avoids grey-out flicker during heavy figure replacement).
    data_refresh = mo.ui.refresh(
        default_interval="1.5s",
        options=["1s", "1.5s", "3s", "10s"],
    )
    plot_refresh = mo.ui.refresh(
        default_interval="4s",
        options=["2s", "4s", "8s"],
    )
    mo.hstack(
        [
            mo.md("**data**"),
            data_refresh,
            mo.md("**plots**"),
            plot_refresh,
        ],
        justify="start",
        gap=1.0,
    )
    return data_refresh, plot_refresh


@app.cell
def _(math, re):
    _UAID_RE = re.compile(r"_C_UAID_[A-F0-9_]+$")
    _TRAILING_C = re.compile(r"_C$")
    _TRAILING_DIGITS = re.compile(r"\d+$")

    def xz_to_bin(x, z, bounds, grid):
        if not (math.isfinite(x) and math.isfinite(z)):
            return None
        xr = bounds["x_max"] - bounds["x_min"]
        zr = bounds["z_max"] - bounds["z_min"]
        if xr <= 0 or zr <= 0:
            return None
        ix = int((x - bounds["x_min"]) / xr * grid)
        iz = int((z - bounds["z_min"]) / zr * grid)
        if 0 <= ix < grid and 0 <= iz < grid:
            return ix, iz
        return None

    def clean_damage_source(raw):
        if not raw:
            return "unknown"
        s = _UAID_RE.sub("", str(raw))
        s = _TRAILING_C.sub("", s)
        # Editor builds emit instance labels like BP_GruntEnemy10; strip
        # trailing digits so cooked-build classes and editor labels collapse
        # to the same display name.
        s = _TRAILING_DIGITS.sub("", s)
        return s or "unknown"

    def short_session(sid):
        if not sid:
            return "?"
        return str(sid)[-6:]

    def safe_float(v, default=0.0):
        try:
            f = float(v)
            return f if math.isfinite(f) else default
        except (TypeError, ValueError):
            return default

    return clean_damage_source, safe_float, short_session, xz_to_bin


@app.cell
def _(
    BOUNDS,
    DATA_PATH,
    HEATMAP_GRID,
    SESSION_PALETTE,
    TRAIL_POINTS,
    clean_damage_source,
    data_refresh,
    deque,
    get_cause_counts,
    get_cursor,
    get_event_arrivals,
    get_heatmaps,
    get_recent_deaths,
    get_run_fallback,
    get_schema_versions,
    get_session_meta,
    get_stats,
    get_trails,
    orjson,
    safe_float,
    set_cause_counts,
    set_cursor,
    set_event_arrivals,
    set_heatmaps,
    set_last_error,
    set_recent_deaths,
    set_run_fallback,
    set_schema_versions,
    set_session_meta,
    set_stats,
    set_trails,
    time,
    xz_to_bin,
):
    # Trigger on each fast data tick. The ingest path is incremental — cursor-based
    # seek + read-from-EOF, so old lines are NEVER re-parsed regardless of file
    # size. Plot rebuilds are throttled separately via `plot_refresh`.
    data_refresh.value

    _cursor = get_cursor()
    _heatmaps = get_heatmaps()
    _trails = get_trails()
    _session_meta = get_session_meta()
    _recent_deaths = get_recent_deaths()
    _stats = dict(get_stats())
    _schema_versions = set(get_schema_versions())
    _event_arrivals = get_event_arrivals()
    _run_fallback = get_run_fallback()
    _cause_counts = dict(get_cause_counts())

    _errors_this_tick = 0
    _last_err = None

    # Outer try/except: any unexpected error (file lock, decode glitch, OS race)
    # is swallowed silently. Stale data for one tick is always better than a
    # visible traceback in front of strangers.
    try:
        try:
            _file_size = DATA_PATH.stat().st_size
        except FileNotFoundError:
            _file_size = None

        if _file_size is None:
            _last_err = "telemetry.jsonl not found"
        else:
            if _file_size < _cursor:
                _cursor = 0
                _heatmaps["deaths"][:] = 0
                _heatmaps["damage"][:] = 0.0
                _heatmaps["positions"][:] = 0
                _trails.clear()
                _session_meta.clear()
                _recent_deaths.clear()
                _schema_versions.clear()
                _event_arrivals.clear()
                _run_fallback.clear()
                _cause_counts.clear()
                _stats.update(
                    {
                        "total_deaths": 0,
                        "total_damage": 0.0,
                        "active_sessions": 0,
                        "peak_concurrent": 0,
                        "events_per_sec": 0.0,
                        "total_events": 0,
                    }
                )

            try:
                with open(DATA_PATH, "rb") as _f:
                    _f.seek(_cursor)
                    _buf = _f.read()
            except OSError as exc:
                _buf = b""
                _last_err = f"read: {exc}"

            _last_nl = _buf.rfind(b"\n")
            if _last_nl >= 0:
                _complete = _buf[: _last_nl + 1]
                _new_cursor = _cursor + _last_nl + 1
                _now_mono = time.monotonic()

                for _line in _complete.split(b"\n"):
                    if not _line.strip():
                        continue
                    try:
                        evt = orjson.loads(_line)
                    except Exception as exc:
                        _errors_this_tick += 1
                        _last_err = f"parse: {exc}"
                        continue

                    try:
                        sid = evt.get("session_id", "") or ""
                        etype = evt.get("event_type", "") or ""
                        ts = evt.get("server_timestamp", "") or ""
                        schema = evt.get("schema_version", "unknown")
                        _schema_versions.add(schema)

                        run_data = evt.get("run_data") or {}
                        rid = run_data.get("run_id") or ""

                        if etype == "run_start" and rid:
                            _run_fallback[sid] = rid
                        if not rid:
                            rid = _run_fallback.get(sid, f"{sid}_run0" if sid else "")

                        if sid and sid not in _session_meta:
                            _session_meta[sid] = {
                                "start": ts,
                                "last": ts,
                                "color": SESSION_PALETTE[
                                    len(_session_meta) % len(SESSION_PALETTE)
                                ],
                                "active": True,
                                "deaths": 0,
                                "damage_dealt": 0.0,
                            }
                        if sid and sid in _session_meta:
                            _session_meta[sid]["last"] = ts

                        _event_arrivals.append(_now_mono)
                        _stats["total_events"] += 1

                        if etype == "session_start":
                            if sid in _session_meta:
                                _session_meta[sid]["active"] = True
                        elif etype == "session_end":
                            if sid in _session_meta:
                                _session_meta[sid]["active"] = False
                        elif etype == "position":
                            pos = evt.get("player_pos") or {}
                            _rx = pos.get("x")
                            _rz = pos.get("z")
                            if _rx is not None and _rz is not None:
                                x = safe_float(_rx, default=None)
                                z = safe_float(_rz, default=None)
                                if x is not None and z is not None:
                                    b = xz_to_bin(x, z, BOUNDS, HEATMAP_GRID)
                                    if b:
                                        _heatmaps["positions"][b[1], b[0]] += 1
                                    if sid not in _trails:
                                        _trails[sid] = deque(maxlen=TRAIL_POINTS)
                                    _trails[sid].append((ts, x, z))
                        elif etype == "damage":
                            amt = safe_float(evt.get("damage"))
                            _stats["total_damage"] += amt
                            if sid in _session_meta:
                                _session_meta[sid]["damage_dealt"] += amt
                            pos = evt.get("player_pos") or {}
                            _rx = pos.get("x")
                            _rz = pos.get("z")
                            if _rx is not None and _rz is not None:
                                x = safe_float(_rx, default=None)
                                z = safe_float(_rz, default=None)
                                if x is not None and z is not None:
                                    b = xz_to_bin(x, z, BOUNDS, HEATMAP_GRID)
                                    if b:
                                        _heatmaps["damage"][b[1], b[0]] += amt
                        elif etype == "death":
                            _stats["total_deaths"] += 1
                            if sid in _session_meta:
                                _session_meta[sid]["deaths"] += 1
                            pos = evt.get("player_pos") or {}
                            _rx = pos.get("x")
                            _rz = pos.get("z")
                            cause_raw = (
                                evt.get("cause")
                                or evt.get("damage_source")
                                or "unknown"
                            )
                            cause = clean_damage_source(cause_raw)
                            src_class = clean_damage_source(
                                evt.get("damage_source_class")
                                or evt.get("damage_source")
                            )
                            _cause_counts[cause] = _cause_counts.get(cause, 0) + 1
                            x = (
                                safe_float(_rx, default=None)
                                if _rx is not None
                                else None
                            )
                            z = (
                                safe_float(_rz, default=None)
                                if _rz is not None
                                else None
                            )
                            if x is not None and z is not None:
                                b = xz_to_bin(x, z, BOUNDS, HEATMAP_GRID)
                                if b:
                                    _heatmaps["deaths"][b[1], b[0]] += 1
                                _recent_deaths.append((ts, x, z, cause, src_class, sid))
                            else:
                                _recent_deaths.append(
                                    (ts, 0.0, 0.0, cause, src_class, sid)
                                )
                    except Exception as exc:
                        _errors_this_tick += 1
                        _last_err = f"dispatch: {exc}"
                        continue

                _cursor = _new_cursor

            _cutoff = time.monotonic() - 30.0
            while _event_arrivals and _event_arrivals[0] < _cutoff:
                _event_arrivals.popleft()
            _stats["events_per_sec"] = len(_event_arrivals) / 30.0

            _active = sum(1 for m in _session_meta.values() if m.get("active"))
            _stats["active_sessions"] = _active
            _stats["peak_concurrent"] = max(_stats["peak_concurrent"], _active)
    except Exception as exc:
        _errors_this_tick += 1
        _last_err = f"tick: {exc}"

    if _last_err is not None:
        set_last_error(_last_err)

    set_cursor(_cursor)
    set_heatmaps(_heatmaps)
    set_trails(_trails)
    set_session_meta(_session_meta)
    set_recent_deaths(_recent_deaths)
    set_stats(_stats)
    set_schema_versions(_schema_versions)
    set_event_arrivals(_event_arrivals)
    set_run_fallback(_run_fallback)
    set_cause_counts(_cause_counts)
    return


@app.cell
def _(mo):
    view = mo.ui.radio(
        options=["Live Arena", "Death Heatmap", "Session Paths"],
        value="Live Arena",
        label="",
        inline=True,
    )
    auto_cycle_switch = mo.ui.switch(value=True, label="auto-cycle when idle")
    mo.hstack(
        [view, auto_cycle_switch],
        justify="end",
        align="center",
        gap=1.5,
    )
    return auto_cycle_switch, view


@app.cell
def _(
    AUTO_CYCLE_IDLE_SECS,
    AUTO_CYCLE_INTERVAL_SECS,
    auto_cycle_switch,
    data_refresh,
    get_auto_cycle,
    set_auto_cycle,
    time,
    view,
):
    # Drive a derived `effective_view` so the plot cell can be advanced by
    # both the user (radio) and the idle auto-cycle without mutating
    # `view.value` (which marimo doesn't support).
    data_refresh.value

    _options = ["Live Arena", "Death Heatmap", "Session Paths"]

    try:
        _state = dict(get_auto_cycle())
    except Exception:
        _state = {}
    _now = time.monotonic()

    _user_v = view.value if view.value in _options else _options[0]

    # Detect user interaction (radio changed since last tick).
    if _state.get("user_value") != _user_v:
        _state["user_value"] = _user_v
        _state["last_user"] = _now
        _state["index"] = _options.index(_user_v)
        _state["last_change"] = _now

    _enabled = bool(getattr(auto_cycle_switch, "value", True))
    _idle = (_now - _state.get("last_user", 0.0)) > AUTO_CYCLE_IDLE_SECS
    if (
        _enabled
        and _idle
        and (_now - _state.get("last_change", 0.0)) > AUTO_CYCLE_INTERVAL_SECS
    ):
        _state["index"] = (_state.get("index", 0) + 1) % len(_options)
        _state["last_change"] = _now

    effective_view = _options[_state.get("index", 0) % len(_options)]
    set_auto_cycle(_state)
    return (effective_view,)


@app.cell
def _(
    effective_view,
    get_heatmaps,
    get_last_plot_t,
    get_plot_snap,
    get_recent_deaths,
    get_session_meta,
    get_stats,
    get_trails,
    plot_refresh,
    set_last_plot_t,
    set_plot_snap,
    time,
):
    # Throttle cell — the only writer of `plot_snap`. The plot cell reads only
    # from the snap, so plot rebuilds happen iff we publish here. We gate on
    # both a wall-clock floor (PLOT_MIN_INTERVAL) and a content signature, so
    # data ingest can fire as fast as it wants without dragging the plot
    # rebuild rate up with it.
    PLOT_MIN_INTERVAL = 3.0

    plot_refresh.value  # bind to the slow tick

    _now = time.monotonic()
    _new_snap = None

    if _now - get_last_plot_t() >= PLOT_MIN_INTERVAL:
        try:
            _trails = get_trails()
            _session_meta = get_session_meta()
            _deaths = list(get_recent_deaths())
            _heatmaps = get_heatmaps()
            _stats = get_stats()
            _sig = (
                effective_view,
                int(_stats.get("total_events", 0)),
                int(_stats.get("total_deaths", 0)),
                sum(len(_t) for _t in _trails.values()),
                len(_deaths),
            )
            _prev = get_plot_snap()
            if _prev is None or _prev.get("sig") != _sig:
                _new_snap = {
                    "sig": _sig,
                    "view": effective_view,
                    # Shallow-copy trail deques to plain lists so the plot
                    # cell sees an immutable view that can't be mutated
                    # mid-render by the ingest cell.
                    "trails": {k: list(v) for k, v in _trails.items()},
                    "session_meta": dict(_session_meta),
                    "deaths": _deaths,
                    # Heatmap arrays are large; the plot cell only reads
                    # them, so share the reference rather than deep-copying.
                    "heatmaps": _heatmaps,
                    # Stats snapshotted here so the side-by-side layout cell
                    # rebuilds at this throttled cadence too, instead of the
                    # 1.5s data tick (which would re-flash the figure).
                    "stats": dict(_stats),
                }
        except Exception:
            _new_snap = None

    if _new_snap is not None:
        set_plot_snap(_new_snap)
        set_last_plot_t(_now)
    return


@app.cell
def _(
    BLUR_SIGMA,
    BOUNDS,
    SESSION_PALETTE,
    TRAIL_FADE_SECS,
    gaussian_filter,
    get_plot_snap,
    go,
    np,
):
    # Render from the throttled snapshot only. Reruns iff `plot_snap` changes.
    _snap = get_plot_snap()
    _v = _snap.get("view", "Live Arena")
    _trails = _snap.get("trails", {})
    _session_meta = _snap.get("session_meta", {})
    _deaths = _snap.get("deaths", [])
    _heatmaps = _snap.get("heatmaps")
    _x_range = [BOUNDS["x_min"], BOUNDS["x_max"]]
    _z_range = [BOUNDS["z_min"], BOUNDS["z_max"]]

    _base_layout = dict(
        paper_bgcolor="#0d1117",
        plot_bgcolor="#0d1117",
        font=dict(color="#c9d1d9", size=14),
        margin=dict(l=40, r=40, t=50, b=40),
        height=720,
        showlegend=False,
        xaxis=dict(
            range=_x_range,
            showgrid=False,
            zeroline=False,
            title="",
            color="#666",
        ),
        yaxis=dict(
            range=_z_range,
            showgrid=False,
            zeroline=False,
            scaleanchor="x",
            scaleratio=1,
            title="",
            color="#666",
        ),
        transition=dict(duration=300, easing="cubic-in-out"),
        # Preserve user-driven zoom/pan across figure replacements. As long as
        # this value stays constant between rebuilds, Plotly does not reset
        # axis ranges or other UI state when the figure is replaced. See
        # https://plotly.com/python/uirevision/
        uirevision="arena",
    )

    try:
        if _v == "Live Arena":
            fig = go.Figure()
            fig.add_shape(
                type="rect",
                x0=BOUNDS["x_min"],
                x1=BOUNDS["x_max"],
                y0=BOUNDS["z_min"],
                y1=BOUNDS["z_max"],
                line=dict(color="#2a2f38", width=2),
                fillcolor="rgba(0,0,0,0)",
                layer="below",
            )

            _fade_window = TRAIL_FADE_SECS * 4
            for _sid, _trail in _trails.items():
                if not _trail:
                    continue
                _recent = list(_trail)[-_fade_window:]
                _xs = [p[1] for p in _recent]
                _zs = [p[2] for p in _recent]
                _meta = _session_meta.get(_sid, {})
                _color = _meta.get("color", SESSION_PALETTE[0])
                _active = _meta.get("active", True)
                fig.add_trace(
                    go.Scatter(
                        x=_xs,
                        y=_zs,
                        mode="lines",
                        line=dict(color=_color, width=3),
                        opacity=0.85 if _active else 0.2,
                        hoverinfo="skip",
                    )
                )
                if _recent and _active:
                    # Glow halo
                    fig.add_trace(
                        go.Scatter(
                            x=[_recent[-1][1]],
                            y=[_recent[-1][2]],
                            mode="markers",
                            marker=dict(color=_color, size=34, opacity=0.25),
                            hoverinfo="skip",
                        )
                    )
                    fig.add_trace(
                        go.Scatter(
                            x=[_recent[-1][1]],
                            y=[_recent[-1][2]],
                            mode="markers",
                            marker=dict(
                                color=_color,
                                size=20,
                                line=dict(color="white", width=2),
                            ),
                            hoverinfo="skip",
                        )
                    )

            if _deaths:
                fig.add_trace(
                    go.Scatter(
                        x=[d[1] for d in _deaths],
                        y=[d[2] for d in _deaths],
                        mode="markers",
                        marker=dict(
                            color="#FF5252",
                            size=16,
                            symbol="x",
                            line=dict(width=3, color="#FF5252"),
                        ),
                        hoverinfo="skip",
                    )
                )

            fig.update_layout(
                title=dict(text="Live Arena", font=dict(size=20)), **_base_layout
            )

        elif _v == "Death Heatmap":
            if _heatmaps is None:
                fig = go.Figure()
                fig.update_layout(
                    title=dict(text="Death Heatmap", font=dict(size=20)), **_base_layout
                )
            else:
                _grid = gaussian_filter(
                    _heatmaps["deaths"].astype(np.float32), BLUR_SIGMA
                )
                _gh, _gw = _grid.shape
                _xcoords = np.linspace(BOUNDS["x_min"], BOUNDS["x_max"], _gw)
                _zcoords = np.linspace(BOUNDS["z_min"], BOUNDS["z_max"], _gh)

                fig = go.Figure(
                    go.Heatmap(
                        x=_xcoords,
                        y=_zcoords,
                        z=_grid,
                        colorscale="Inferno",
                        showscale=True,
                        colorbar=dict(
                            thickness=12, outlinewidth=0, tickfont=dict(color="#c9d1d9")
                        ),
                        hoverinfo="skip",
                        zsmooth="best",
                    )
                )
                # Faint individual death markers on top so passersby see
                # individual events, not just the smoothed field.
                if _deaths:
                    fig.add_trace(
                        go.Scatter(
                            x=[d[1] for d in _deaths],
                            y=[d[2] for d in _deaths],
                            mode="markers",
                            marker=dict(
                                color="#FF5252",
                                size=10,
                                symbol="x",
                                line=dict(width=2, color="#FF5252"),
                                opacity=0.4,
                            ),
                            hoverinfo="skip",
                        )
                    )
                fig.update_layout(
                    title=dict(text="Death Heatmap", font=dict(size=20)), **_base_layout
                )

        else:  # Session Paths
            fig = go.Figure()
            fig.add_shape(
                type="rect",
                x0=BOUNDS["x_min"],
                x1=BOUNDS["x_max"],
                y0=BOUNDS["z_min"],
                y1=BOUNDS["z_max"],
                line=dict(color="#2a2f38", width=2),
                fillcolor="rgba(0,0,0,0)",
                layer="below",
            )
            for _sid, _trail in _trails.items():
                if not _trail:
                    continue
                _pts = list(_trail)
                _color = _session_meta.get(_sid, {}).get("color", SESSION_PALETTE[0])
                fig.add_trace(
                    go.Scatter(
                        x=[p[1] for p in _pts],
                        y=[p[2] for p in _pts],
                        mode="lines",
                        line=dict(color=_color, width=3),
                        opacity=0.95,
                        hoverinfo="skip",
                    )
                )
            fig.update_layout(
                title=dict(text="Session Paths", font=dict(size=20)), **_base_layout
            )
    except Exception:
        # Last-resort: always render *something*. Bare frame, no error UI.
        fig = go.Figure()
        fig.update_layout(title=dict(text=_v, font=dict(size=20)), **_base_layout)

    fig.update_xaxes(autorange="reversed")  # GOTTA MOVE ELSEWHERE
    arena_fig = fig
    return (arena_fig,)


@app.cell
def _(arena_fig, mo, stats_column):
    # Side-by-side layout: stats column left, arena right. Both inputs change
    # together (throttled snapshot), so this cell rebuilds at the throttled
    # cadence — no figure re-flash on the 1.5s data tick.
    mo.hstack(
        [stats_column, arena_fig],
        widths=[1, 4],
        align="stretch",
        gap=1.0,
    )
    return


@app.cell
def _(get_plot_snap, mo):
    # Stats column drives off the throttled plot_snap (not get_stats directly)
    # so this cell rebuilds at the same cadence as the figure. That keeps the
    # side-by-side layout cell from re-flashing the figure on every 1.5s data
    # tick. Stats can lag by up to PLOT_MIN_INTERVAL — fine for "Total Deaths".
    _snap = get_plot_snap()
    _s = _snap.get("stats") or {}

    def _tile(label, value, accent):
        return mo.md(
            f"""
            <div style="
                padding: 22px 26px;
                background: linear-gradient(180deg, #1a1d23 0%, #15181d 100%);
                border-top: 2px solid {accent};
                border-radius: 6px;
                box-shadow: 0 0 28px {accent}26, inset 0 0 0 1px #23272f;
            ">
              <div style="color: #7d8590; font-size: 12px; text-transform: uppercase; letter-spacing: 2px; font-weight: 600;">{label}</div>
              <div style="color: #f5f5f5; font-size: 56px; font-weight: 700; line-height: 1.05; margin-top: 8px; font-variant-numeric: tabular-nums;">{value}</div>
            </div>
            """
        )

    def _fmt_int(v):
        try:
            return f"{int(v):,}"
        except Exception:
            return "0"

    def _fmt_float(v, prec=1):
        try:
            return f"{float(v):,.{prec}f}"
        except Exception:
            return "0"

    stats_column = mo.vstack(
        [
            _tile("Active Sessions", _fmt_int(_s.get("active_sessions", 0)), "#4FC3F7"),
            _tile("Total Deaths", _fmt_int(_s.get("total_deaths", 0)), "#FF5252"),
            _tile(
                "Total Damage", _fmt_float(_s.get("total_damage", 0.0), 0), "#FF7043"
            ),
            _tile("Peak Concurrent", _fmt_int(_s.get("peak_concurrent", 0)), "#BA68C8"),
            _tile(
                "Events / sec", _fmt_float(_s.get("events_per_sec", 0.0), 1), "#81C784"
            ),
        ],
        gap=0.75,
    )
    return (stats_column,)


@app.cell
def _(data_refresh, dt, get_recent_deaths, mo, short_session):
    # Re-run each tick so "seconds ago" stays current and the card auto-dims.
    data_refresh.value

    try:
        _deaths = list(get_recent_deaths())
    except Exception:
        _deaths = []

    if not _deaths:
        _card = """
        <div style="
            padding: 22px 28px;
            background: linear-gradient(180deg, #1a1d23 0%, #15181d 100%);
            border-top: 2px solid #2a2f38;
            border-radius: 6px;
            box-shadow: inset 0 0 0 1px #23272f;
        ">
          <div style="color: #7d8590; font-size: 12px; text-transform: uppercase; letter-spacing: 2px; font-weight: 600;">Last Death</div>
          <div style="color: #555; font-size: 22px; margin-top: 10px; font-style: italic;">awaiting first event</div>
        </div>
        """
    else:
        try:
            _ts, _x, _z, _cause, _src, _sid = _deaths[-1]
        except Exception:
            _ts, _x, _z, _cause, _src, _sid = "", 0.0, 0.0, "unknown", "unknown", ""

        try:
            _event_dt = dt.datetime.fromisoformat(str(_ts).replace("Z", "+00:00"))
            if _event_dt.tzinfo:
                _now = dt.datetime.now(_event_dt.tzinfo)
            else:
                _now = dt.datetime.now()
            _secs_ago = max(0, int((_now - _event_dt).total_seconds()))
        except Exception:
            _secs_ago = 0

        _fresh = _secs_ago < 15
        _accent = "#FF5252" if _fresh else "#444"
        _opacity = 1.0 if _fresh else 0.35
        _headline_color = "#f5f5f5" if _fresh else "#888"

        try:
            _coord_str = f"({int(_x):,}, {int(_z):,})"
        except Exception:
            _coord_str = ""

        _glow = "0 0 32px rgba(255,82,82,0.28)" if _fresh else "0 0 0 rgba(0,0,0,0)"
        _card = f"""
        <div style="
            padding: 22px 28px;
            background: linear-gradient(180deg, #1a1d23 0%, #15181d 100%);
            border-top: 2px solid {_accent};
            border-radius: 6px;
            opacity: {_opacity};
            transition: opacity 0.6s, border-color 0.6s, box-shadow 0.6s;
            box-shadow: {_glow}, inset 0 0 0 1px #23272f;
        ">
          <div style="color: #7d8590; font-size: 12px; text-transform: uppercase; letter-spacing: 2px; font-weight: 600;">Last Death</div>
          <div style="color: {_headline_color}; font-size: 38px; font-weight: 700; line-height: 1.1; margin-top: 8px;">
            {_cause} <span style="color: #555; font-weight: 400;">&middot;</span> {_src}
          </div>
          <div style="color: #7d8590; font-size: 14px; margin-top: 12px; font-family: 'SF Mono', Consolas, monospace; letter-spacing: 0.5px;">
            <span style="color: #c9d1d9;">{short_session(_sid)}</span>
            <span style="color: #3a3f47; margin: 0 10px;">|</span>
            {_secs_ago}s ago
            <span style="color: #3a3f47; margin: 0 10px;">|</span>
            {_coord_str}
          </div>
        </div>
        """
    mo.md(_card)
    return


@app.cell
def _(MAX_KIOSKS, dt, get_session_meta, mo, short_session):
    try:
        _meta = dict(get_session_meta())
    except Exception:
        _meta = {}

    # Sort: active sessions first, then by start time (so latest 4 stay in view).
    _items = sorted(
        _meta.items(),
        key=lambda kv: (not kv[1].get("active", False), kv[1].get("start", "")),
    )[:MAX_KIOSKS]

    def _fmt_duration(start_ts, last_ts):
        try:
            _s = dt.datetime.fromisoformat(str(start_ts).replace("Z", "+00:00"))
            _e = dt.datetime.fromisoformat(str(last_ts).replace("Z", "+00:00"))
            secs = max(0, int((_e - _s).total_seconds()))
            return f"{secs // 60}:{secs % 60:02d}"
        except Exception:
            return "—"

    _rows_html = []
    for _sid, _m in _items:
        try:
            _color = _m.get("color", "#888")
            _active = _m.get("active", False)
            _dur = _fmt_duration(_m.get("start", ""), _m.get("last", ""))
            _dth = int(_m.get("deaths", 0))
            _dmg = int(_m.get("damage_dealt", 0.0))
            _dot_op = "1" if _active else "0.35"
            _row_op = "1" if _active else "0.5"
            _status_text = "live" if _active else "ended"
            _status_color = "#4cd964" if _active else "#555"
            _rows_html.append(
                f"""
                <div style="
                    display: grid;
                    grid-template-columns: 18px 1fr 70px 130px 120px 140px;
                    align-items: center; gap: 22px;
                    padding: 16px 24px; border-bottom: 1px solid #23272f;
                    opacity: {_row_op}; transition: opacity 0.4s;
                ">
                  <span style="
                      width: 12px; height: 12px; border-radius: 50%;
                      background: {_color}; opacity: {_dot_op};
                      box-shadow: 0 0 12px {_color}aa;
                  "></span>
                  <span style="color: #f5f5f5; font-size: 20px; font-family: 'SF Mono', Consolas, monospace; letter-spacing: 0.5px;">
                      {short_session(_sid)}
                  </span>
                  <span style="color: {_status_color}; font-size: 11px; text-transform: uppercase; letter-spacing: 2px; font-weight: 700;">{_status_text}</span>
                  <span style="color: #c9d1d9; font-size: 20px; font-variant-numeric: tabular-nums;">{_dur}</span>
                  <span style="color: #FF5252; font-size: 20px; font-weight: 700; font-variant-numeric: tabular-nums;">{_dth}</span>
                  <span style="color: #FF7043; font-size: 20px; font-weight: 700; font-variant-numeric: tabular-nums;">{_dmg:,}</span>
                </div>
                """
            )
        except Exception:
            _rows_html.append(
                """
                <div style="padding: 16px 24px; color: #555; font-size: 14px;">
                  (row unavailable)
                </div>
                """
            )

    if not _rows_html:
        _rows_html.append(
            """
            <div style="padding: 22px 24px; color: #555; font-size: 18px; font-style: italic;">
              awaiting kiosks
            </div>
            """
        )

    _header = """
    <div style="
        display: grid;
        grid-template-columns: 18px 1fr 70px 130px 120px 140px;
        gap: 22px; padding: 14px 24px;
        color: #7d8590; font-size: 11px; text-transform: uppercase; letter-spacing: 2px; font-weight: 600;
        background: #15181d;
        border-bottom: 1px solid #23272f;
    ">
      <span></span><span>Session</span><span></span><span>Duration</span><span>Deaths</span><span>Damage</span>
    </div>
    """

    _table = (
        '<div style="background: #1a1d23; border-radius: 6px; overflow: hidden; box-shadow: inset 0 0 0 1px #23272f;">'
        + _header
        + "".join(_rows_html)
        + "</div>"
    )
    mo.md(_table)
    return


@app.cell
def _(get_cause_counts, go, mo):
    try:
        _counts = dict(get_cause_counts())
    except Exception:
        _counts = {}

    if not _counts:
        mo.md(
            """
            <div style="
                padding: 22px 26px;
                background: linear-gradient(180deg, #1a1d23 0%, #15181d 100%);
                border-radius: 6px;
                box-shadow: inset 0 0 0 1px #23272f;
            ">
              <div style="color: #7d8590; font-size: 12px; text-transform: uppercase; letter-spacing: 2px; font-weight: 600;">Cause of Death</div>
              <div style="color: #555; font-size: 18px; margin-top: 12px; font-style: italic;">no deaths recorded yet</div>
            </div>
            """
        )
    else:
        try:
            _sorted = sorted(_counts.items(), key=lambda kv: kv[1], reverse=True)[:8]
            _causes = [c for c, _ in _sorted]
            _vals = [v for _, v in _sorted]
            _max_v = max(_vals) if _vals else 1
            # Per-bar opacity ramp so the most common cause reads strongest.
            _bar_colors = [
                f"rgba(255, 112, 67, {0.35 + 0.55 * (v / _max_v):.2f})" for v in _vals
            ]

            _fig = go.Figure(
                go.Bar(
                    x=_vals,
                    y=_causes,
                    orientation="h",
                    marker=dict(
                        color=_bar_colors,
                        line=dict(width=0),
                    ),
                    text=[f"{v:,}" for v in _vals],
                    textposition="outside",
                    textfont=dict(color="#c9d1d9", size=14),
                    hoverinfo="skip",
                    cliponaxis=False,
                )
            )
            _fig.update_layout(
                title=dict(
                    text="Cause of Death",
                    font=dict(size=13, color="#7d8590", family="system-ui"),
                    x=0.0,
                    xanchor="left",
                ),
                paper_bgcolor="#1a1d23",
                plot_bgcolor="#1a1d23",
                font=dict(color="#c9d1d9"),
                margin=dict(l=200, r=80, t=50, b=24),
                height=260,
                xaxis=dict(
                    showgrid=False,
                    zeroline=False,
                    color="#3a3f47",
                    tickfont=dict(size=12),
                ),
                yaxis=dict(
                    autorange="reversed",
                    showgrid=False,
                    zeroline=False,
                    tickfont=dict(size=15, color="#c9d1d9"),
                ),
                showlegend=False,
                bargap=0.35,
            )
            _fig
        except Exception:
            mo.md(
                """
                <div style="padding: 16px 18px; color: #555; font-size: 16px;">
                  Cause breakdown unavailable.
                </div>
                """
            )
    return


if __name__ == "__main__":
    app.run()
