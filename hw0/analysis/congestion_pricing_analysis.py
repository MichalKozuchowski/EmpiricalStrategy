"""
HW0 — NYC Transit & Congestion Pricing
Assess the impact of congestion pricing (and other MTA price/policy changes) on
subway, bridge/tunnel, and Metro-North ridership, using the MTA Daily Ridership
and Traffic dataset (data.ny.gov, sayj-mze2).

Outputs (written to hw0/analysis/output/):
  - timeseries_<mode>.png     7-day rolling average with event lines
  - event_study_<mode>.png    average ridership in the weeks before/after congestion pricing
  - summary.csv               pre/post % change for each mode around each event
"""

import os
import pandas as pd
import matplotlib.pyplot as plt

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data", "MTA_Daily_Ridership_and_Traffic__Beginning_2020.csv")
OUT = os.path.join(HERE, "output")
os.makedirs(OUT, exist_ok=True)

# --- Key policy/price events (from MTA_Key_Dates.pdf) ---
EVENTS = {
    "2023-08-06": "Toll increase (bridges/tunnels)",
    "2023-08-20": "Fare increase (subway/bus/rail)",
    "2025-01-05": "Congestion pricing begins",
    "2025-09-01": "CT-only fare increase (New Haven Line)",
    "2026-01-04": "Fares & tolls increase",
}
CONGESTION_PRICING_DATE = pd.Timestamp("2025-01-05")

# Modes most relevant to the prof's question: subway, bridges, Metro-North.
# BT = Bridges & Tunnels (vehicle crossings), CBD/CRZ Entries = vehicles into the
# congestion relief zone (only populated from Jan 2025 on), MNR = Metro-North.
FOCUS_MODES = {
    "Subway": "Subway ridership",
    "BT": "Bridge & Tunnel crossings",
    "MNR": "Metro-North ridership",
    "CRZ Entries": "Congestion Relief Zone vehicle entries",
}

def load_data():
    df = pd.read_csv(DATA, parse_dates=["Date"], date_format="%m/%d/%Y")
    df = df.rename(columns={"Count": "count"})
    return df

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
                ax.axvline(d, color="#d62728" if "Congestion" in desc else "#999999",
                           linestyle="--", linewidth=1)
        ax.set_title(f"{label} — 7-day rolling average")
        ax.set_ylabel("Daily count (7-day avg)")
        ax.set_xlabel("Date")
        fig.tight_layout()
        fname = os.path.join(OUT, f"timeseries_{mode.replace(' ', '_')}.png")
        fig.savefig(fname, dpi=150)
        plt.close(fig)
        print(f"saved {fname}")

def event_study(df, window_days=28):
    """Compare average daily ridership in the `window_days` before vs after
    congestion pricing began. Raw pre/post is confounded by the New Year's
    holiday dip that shows up every year in this data, so we also compute a
    year-over-year 'difference-in-differences' version: the same calendar
    window one year earlier (Jan 2024, no congestion pricing) is used as a
    control for normal seasonal + trend growth across the Dec->Jan boundary."""
    rows = []
    for mode, label in FOCUS_MODES.items():
        sub = df[df["Mode"] == mode].sort_values("Date").copy()
        if sub.empty:
            continue

        pre = sub[(sub["Date"] >= CONGESTION_PRICING_DATE - pd.Timedelta(days=window_days)) &
                  (sub["Date"] < CONGESTION_PRICING_DATE)]
        post = sub[(sub["Date"] >= CONGESTION_PRICING_DATE) &
                   (sub["Date"] < CONGESTION_PRICING_DATE + pd.Timedelta(days=window_days))]
        if pre.empty or post.empty:
            continue

        pre_mean, post_mean = pre["count"].mean(), post["count"].mean()
        pct_change = (post_mean - pre_mean) / pre_mean * 100

        row = {
            "mode": mode,
            "label": label,
            f"pre_{window_days}d_avg": round(pre_mean, 0),
            f"post_{window_days}d_avg": round(post_mean, 0),
            "pct_change_raw": round(pct_change, 2),
        }

        # Year-over-year control: same calendar window, one year earlier
        control_date = CONGESTION_PRICING_DATE - pd.DateOffset(years=1)
        pre_ctrl = sub[(sub["Date"] >= control_date - pd.Timedelta(days=window_days)) &
                       (sub["Date"] < control_date)]
        post_ctrl = sub[(sub["Date"] >= control_date) &
                        (sub["Date"] < control_date + pd.Timedelta(days=window_days))]
        if not pre_ctrl.empty and not post_ctrl.empty:
            pct_change_ctrl = (post_ctrl["count"].mean() - pre_ctrl["count"].mean()) / pre_ctrl["count"].mean() * 100
            row["pct_change_control_yoy"] = round(pct_change_ctrl, 2)
            row["pct_change_did"] = round(pct_change - pct_change_ctrl, 2)
        else:
            row["pct_change_control_yoy"] = None
            row["pct_change_did"] = None

        rows.append(row)

        fig, axes = plt.subplots(1, 2, figsize=(10, 4))
        axes[0].bar(["Pre (28d)", "Post (28d)"], [pre_mean, post_mean], color=["#7f7f7f", "#1f77b4"])
        axes[0].set_title(f"{label}: raw before/after\n(Jan 5, 2025)")
        axes[0].set_ylabel("Average daily count")
        for i, v in enumerate([pre_mean, post_mean]):
            axes[0].text(i, v, f"{v:,.0f}", ha="center", va="bottom")

        if row["pct_change_did"] is not None:
            axes[1].bar(["2025\n(actual)", "2024\n(YoY control)"],
                        [row["pct_change_raw"], row["pct_change_control_yoy"]],
                        color=["#d62728", "#7f7f7f"])
            axes[1].axhline(0, color="black", linewidth=0.8)
            axes[1].set_title(f"% change, pre->post\nDiD estimate: {row['pct_change_did']:+.1f} pp")
            axes[1].set_ylabel("% change")
            for i, v in enumerate([row["pct_change_raw"], row["pct_change_control_yoy"]]):
                axes[1].text(i, v, f"{v:+.1f}%", ha="center",
                             va="bottom" if v >= 0 else "top")
        fig.tight_layout()
        fname = os.path.join(OUT, f"event_study_{mode.replace(' ', '_')}.png")
        fig.savefig(fname, dpi=150)
        plt.close(fig)
        print(f"saved {fname}")

    result = pd.DataFrame(rows)
    result.to_csv(os.path.join(OUT, "summary.csv"), index=False)
    print(result.to_string(index=False))
    return result

if __name__ == "__main__":
    df = load_data()
    plot_timeseries(df)
    event_study(df)
