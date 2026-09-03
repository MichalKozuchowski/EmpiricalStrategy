"""
HW0 — NYC Transit & Congestion Pricing
Assess the impact of every MTA fare/toll/policy change in the sample window
(MTA_Key_Dates.pdf) on subway, bridge/tunnel, and Metro-North ridership, using
the MTA Daily Ridership and Traffic dataset (data.ny.gov, sayj-mze2).

Outputs (written to hw0/analysis/output/):
  - timeseries_<mode>.png        full history, 7-day rolling avg, all events marked
  - event_study_<date>.png       per-event before/after + YoY-control bars, one panel per mode
  - heatmap_did.png              all events x all modes, diff-in-differences estimate (pp)
  - summary_all_events.csv       full numeric results
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data", "MTA_Daily_Ridership_and_Traffic__Beginning_2020.csv")
OUT = os.path.join(HERE, "output")
os.makedirs(OUT, exist_ok=True)

# --- Every policy/price change in MTA_Key_Dates.pdf, inside the sample window ---
EVENTS = {
    "2023-08-06": "Toll increase, all bridges & tunnels",
    "2023-08-20": "Fare increase, subway/bus/rail",
    "2023-08-21": "CityTicket extended to peak trains (narrow/targeted)",
    "2025-01-05": "Congestion pricing begins",
    "2025-09-01": "CT-only fare increase, New Haven Line (narrow/targeted)",
    "2026-01-04": "Fares & tolls increase, systemwide",
}
CONGESTION_PRICING_DATE = pd.Timestamp("2025-01-05")

# Modes the professor's question asks about, plus the zone-specific congestion metric.
FOCUS_MODES = {
    "Subway": "Subway ridership",
    "BT": "Bridge & Tunnel crossings",
    "MNR": "Metro-North ridership",
    "CRZ Entries": "Congestion Relief Zone vehicle entries",
}


def load_data():
    df = pd.read_csv(DATA, parse_dates=["Date"], date_format="%m/%d/%Y")
    return df.rename(columns={"Count": "count"})


def plot_timeseries(df):
    for mode, label in FOCUS_MODES.items():
        sub = df[df["Mode"] == mode].sort_values("Date").copy()
        if sub.empty:
            continue
        sub["roll7"] = sub["count"].rolling(7, min_periods=1).mean()

        fig, ax = plt.subplots(figsize=(11, 5))
        ax.plot(sub["Date"], sub["roll7"], color="#1f77b4", linewidth=1.5)
        for date_str, desc in EVENTS.items():
            d = pd.Timestamp(date_str)
            if sub["Date"].min() <= d <= sub["Date"].max():
                ax.axvline(d, color="#d62728" if "Congestion pricing" in desc else "#999999",
                           linestyle="--", linewidth=1)
        ax.set_title(f"{label} — 7-day rolling average, all policy dates marked")
        ax.set_ylabel("Daily count (7-day avg)")
        ax.set_xlabel("Date")
        fig.tight_layout()
        fname = os.path.join(OUT, f"timeseries_{mode.replace(' ', '_')}.png")
        fig.savefig(fname, dpi=150)
        plt.close(fig)
        print(f"saved {fname}")


def window_avg(sub, center, window_days, direction):
    """direction='pre' -> [center-window, center); 'post' -> [center, center+window)"""
    if direction == "pre":
        w = sub[(sub["Date"] >= center - pd.Timedelta(days=window_days)) & (sub["Date"] < center)]
    else:
        w = sub[(sub["Date"] >= center) & (sub["Date"] < center + pd.Timedelta(days=window_days))]
    return w["count"].mean() if not w.empty else np.nan


def event_rows_for_date(df, event_date, event_label, window_days=28):
    """Raw pre/post change for one event, plus a year-over-year diff-in-differences
    control (same calendar window one year earlier) to net out normal seasonality
    and the underlying multi-year ridership trend."""
    rows = []
    for mode, label in FOCUS_MODES.items():
        sub = df[df["Mode"] == mode].sort_values("Date").copy()
        if sub.empty:
            continue

        pre_mean = window_avg(sub, event_date, window_days, "pre")
        post_mean = window_avg(sub, event_date, window_days, "post")
        if np.isnan(pre_mean) or np.isnan(post_mean):
            continue
        raw_pct = (post_mean - pre_mean) / pre_mean * 100

        control_date = event_date - pd.DateOffset(years=1)
        pre_ctrl = window_avg(sub, control_date, window_days, "pre")
        post_ctrl = window_avg(sub, control_date, window_days, "post")
        if not np.isnan(pre_ctrl) and not np.isnan(post_ctrl) and pre_ctrl != 0:
            ctrl_pct = (post_ctrl - pre_ctrl) / pre_ctrl * 100
            did = raw_pct - ctrl_pct
        else:
            ctrl_pct, did = np.nan, np.nan

        rows.append({
            "event_date": event_date.date().isoformat(),
            "event_label": event_label,
            "mode": mode,
            "mode_label": label,
            f"pre_{window_days}d_avg": round(pre_mean, 0),
            f"post_{window_days}d_avg": round(post_mean, 0),
            "pct_change_raw": round(raw_pct, 2),
            "pct_change_control_yoy": round(ctrl_pct, 2) if not np.isnan(ctrl_pct) else None,
            "pct_change_did": round(did, 2) if not np.isnan(did) else None,
        })
    return rows


def plot_event(rows, event_date, event_label):
    modes = [r for r in rows]
    n = len(modes)
    if n == 0:
        return
    fig, axes = plt.subplots(1, n, figsize=(4 * n, 4))
    if n == 1:
        axes = [axes]
    for ax, r in zip(axes, modes):
        raw, ctrl, did = r["pct_change_raw"], r["pct_change_control_yoy"], r["pct_change_did"]
        if ctrl is None:
            ax.bar(["2025/26\n(actual)"], [raw], color="#d62728")
            title = f"{r['mode_label']}\nno prior-year baseline"
        else:
            ax.bar(["actual", "YoY\ncontrol"], [raw, ctrl], color=["#d62728", "#7f7f7f"])
            title = f"{r['mode_label']}\nDiD: {did:+.1f} pp"
        ax.axhline(0, color="black", linewidth=0.8)
        ax.set_title(title, fontsize=10)
        ax.set_ylabel("% change, pre->post")
    fig.suptitle(f"{event_date.date()} — {event_label}")
    fig.tight_layout()
    fname = os.path.join(OUT, f"event_study_{event_date.date()}.png")
    fig.savefig(fname, dpi=150)
    plt.close(fig)
    print(f"saved {fname}")


def plot_heatmap(summary):
    pivot = summary.pivot_table(index="event_label", columns="mode", values="pct_change_did")
    # keep a readable, chronological event order
    order = [EVENTS[d] for d in EVENTS]
    pivot = pivot.reindex(order)
    modes = list(FOCUS_MODES.keys())
    pivot = pivot.reindex(columns=modes)

    fig, ax = plt.subplots(figsize=(8, 5))
    data = pivot.to_numpy(dtype=float)
    im = ax.imshow(data, cmap="RdBu_r", vmin=-8, vmax=8, aspect="auto")
    ax.set_xticks(range(len(modes)))
    ax.set_xticklabels(modes)
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index, fontsize=8)
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            v = data[i, j]
            txt = "n/a" if np.isnan(v) else f"{v:+.1f}"
            ax.text(j, i, txt, ha="center", va="center", fontsize=8,
                    color="white" if not np.isnan(v) and abs(v) > 5 else "black")
    ax.set_title("Diff-in-differences estimate (pp), all events x modes")
    fig.colorbar(im, ax=ax, label="pp vs. year-ago seasonal norm")
    fig.tight_layout()
    fname = os.path.join(OUT, "heatmap_did.png")
    fig.savefig(fname, dpi=150)
    plt.close(fig)
    print(f"saved {fname}")


if __name__ == "__main__":
    df = load_data()
    plot_timeseries(df)

    all_rows = []
    for date_str, label in EVENTS.items():
        d = pd.Timestamp(date_str)
        rows = event_rows_for_date(df, d, label)
        plot_event(rows, d, label)
        all_rows.extend(rows)

    summary = pd.DataFrame(all_rows)
    summary.to_csv(os.path.join(OUT, "summary_all_events.csv"), index=False)
    plot_heatmap(summary)
    print(summary.to_string(index=False))
