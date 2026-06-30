#!/usr/bin/env python3
"""
Illiquidity tilt: T4 − (T1 + T2 + T3) vs saving and vs rates
============================================================

Companion to the yield-tilt plots (F4/F5). Instead of "locked-for-yield minus
instant-access", this measures how far each year's saving is tilted into the most
ILLIQUID tier of the liquidity ladder:

    illiquidity tilt = net flow into T4  −  net flow into (T1 + T2 + T3)

where (from the liquidity ladder, ESA instruments):
    T1 instant   = F21 + F22            (cash, overnight)
    T2 near-money= F29 + F521 + F31     (term/notice, MMF, short bonds)
    T3 marketable= F32 + F511 + F522    (long bonds, listed shares, funds)
    T4 illiquid  = F512 + F519 + F6     (unlisted equity, insurance/pension)

Positive = households moved that year's saving INTO illiquid, contractual claims
(pensions, life insurance, unlisted equity); negative = toward liquid tiers.

Reads data/G_liquidity_ladder_flows.csv (run liquidity_ladder.py first), plus the
saving rate and ECB rate from data/. Produces F4b (vs saving) and F5b (vs rates).
    python tilt_illiquidity.py
"""

import os
import glob

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.ticker import FuncFormatter

import _common as cm

# --- run from the flattened repo layout ---
cm.ROOT = os.path.dirname(os.path.dirname(cm.HERE))
cm.ROOT_DATA = os.path.join(cm.ROOT, "data")
cm.DATA = os.path.join(cm.ROOT, "data")
cm.FIG = os.path.join(cm.ROOT, "figures")
_orig_root_csv = cm.root_csv
def _tagged_root_csv(name, required=True):
    if not os.path.exists(os.path.join(cm.ROOT_DATA, name)):
        hits = glob.glob(os.path.join(cm.ROOT_DATA, "?_" + name))
        if hits:
            return pd.read_csv(hits[0])
    return _orig_root_csv(name, required)
cm.root_csv = _tagged_root_csv

START_YEAR = 2002


def load_tilt():
    path = os.path.join(cm.DATA, "G_liquidity_ladder_flows.csv")
    if not os.path.exists(path):
        raise SystemExit("Missing data/G_liquidity_ladder_flows.csv — run liquidity_ladder.py first.")
    d = pd.read_csv(path)
    d["illiq_tilt"] = (d["T4"] - (d["T1"] + d["T2"] + d["T3"])) / 1000.0   # EUR bn
    return d[d["year"] >= START_YEAR][["year", "illiq_tilt"]].sort_values("year")


def _annual(name, col):
    q = cm.load_quarterly(name, col)
    a = q.groupby(q.index.year).mean().rename(col)
    a.index.name = "year"
    return a


def _tilt_bars(ax, df, ylabel):
    colors = ["#117a65" if v >= 0 else cm.C_RED for v in df["illiq_tilt"]]
    ax.bar(df["year"], df["illiq_tilt"], color=colors, width=0.8, zorder=2)
    ax.axhline(0, color="black", lw=0.9)
    ax.axvline(2021.5, color="grey", ls="--", lw=1)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:,.0f}"))
    ax.set_ylabel(ylabel)
    ax.set_xlabel("year")


def plot_vs_saving(df):
    sav = _annual("ea_saving_rate_quarterly.csv", "saving")
    d = df.merge(sav.reset_index(), on="year", how="inner")
    fig, ax1 = plt.subplots(figsize=(11, 6))
    ax2 = ax1.twinx(); ax2.grid(False)
    _tilt_bars(ax1, d, "illiquidity tilt: T4 − (T1+T2+T3)  (EUR bn / yr)")
    ax2.plot(d["year"], d["saving"], color=cm.C_NAVY, lw=3.0, ls=(0, (1, 1)), zorder=5)
    ax2.set_ylim(0, 22); ax2.set_yticks([0, 5, 10, 15, 20])
    ax2.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:.0f}%"))
    ax2.set_ylabel("household saving rate (% of disposable income)", color=cm.C_NAVY)
    ax2.tick_params(axis="y", colors=cm.C_NAVY)
    ax1.legend(handles=[mpatches.Patch(color="#117a65", label="into illiquid (T4 > liquid)"),
                        mpatches.Patch(color=cm.C_RED, label="into liquid (T1–T3 > T4)"),
                        plt.Line2D([], [], color=cm.C_NAVY, ls=(0, (1, 1)), lw=3,
                                   label="saving rate (right)")],
               loc="upper left", frameon=True, framealpha=0.9, edgecolor="none", fontsize=9)
    ax1.set_title("Illiquidity tilt of household saving vs the saving rate\n"
                  "net flow into illiquid (T4) minus liquid tiers (T1–T3), euro area",
                  fontweight="bold")
    fig.tight_layout()
    cm.savefig(fig, "F4b_tilt_illiquidity_vs_saving.png")


def plot_vs_rates(df):
    rate = _annual("ecb_rate.csv", "rate")
    d = df.merge(rate.reset_index(), on="year", how="inner")
    corr = d["illiq_tilt"].corr(d["rate"])
    fig, ax1 = plt.subplots(figsize=(11, 6))
    ax2 = ax1.twinx(); ax2.grid(False)
    _tilt_bars(ax1, d, "illiquidity tilt: T4 − (T1+T2+T3)  (EUR bn / yr)")
    ax2.plot(d["year"], d["rate"], color=cm.C_PURPLE, lw=2.6, marker="o", ms=3, zorder=5)
    ax2.yaxis.set_major_formatter(FuncFormatter(lambda x, _: f"{x:.0f}%"))
    ax2.set_ylabel("ECB policy / short rate (%)", color=cm.C_PURPLE)
    ax2.tick_params(axis="y", colors=cm.C_PURPLE)
    ax1.legend(handles=[mpatches.Patch(color="#117a65", label="into illiquid (T4)"),
                        mpatches.Patch(color=cm.C_RED, label="into liquid (T1–T3)"),
                        plt.Line2D([], [], color=cm.C_PURPLE, lw=2.6, marker="o",
                                   label="ECB rate (right)")],
               loc="upper left", frameon=True, framealpha=0.9, edgecolor="none", fontsize=9)
    ax1.set_title(f"Illiquidity tilt vs the ECB rate  (corr = {corr:+.2f})\n"
                  "as rates rose, did saving move toward illiquid contractual claims?",
                  fontweight="bold")
    fig.tight_layout()
    cm.savefig(fig, "F5b_tilt_illiquidity_vs_rates.png")
    return corr


def main():
    df = load_tilt()
    print("Illiquidity tilt T4 − (T1+T2+T3), EUR bn/yr (recent):")
    for _, r in df[df["year"] >= 2019].iterrows():
        print(f"  {int(r['year'])}: {r['illiq_tilt']:+.0f}")
    plot_vs_saving(df)
    corr = plot_vs_rates(df)
    print(f"\ncorr(illiquidity tilt, ECB rate) = {corr:+.2f}")
    df.to_csv(os.path.join(cm.DATA, "F_tilt_illiquidity.csv"), index=False)
    print("Wrote data/F_tilt_illiquidity.csv")


if __name__ == "__main__":
    main()
