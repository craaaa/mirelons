"""Paper Figure 7: item agreement with listeners by model (rows, sorted by mean over setups) and setup (columns).

Each cell is the median item agreement r (L3a_model_r_with_half: Pearson r between a listener-half-sized model
sample and a random listener half on the 20 questions' difficulty) over every configuration of that model and
setup (capacity, encoding, thinking mode, prompt), leaving out the configurations whose own split-half
reliability is undefined or below .5.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

import plotting as fp

SETUP_KEYS = list(fp.SETUPS)                      # prompted, compactor, summary, chosen-propositions, random-dropout


def table(df: pd.DataFrame) -> pd.DataFrame:
    """Models x setups, median r over estimable configurations, rows sorted by mean."""
    est = df[df.L3a_verdict != "not estimable"]
    R = est.pivot_table(index="model_slug", columns="setup", values="L3a_model_r_with_half", aggfunc="median")
    R = R.reindex(columns=SETUP_KEYS)
    return R.loc[R.mean(axis=1).sort_values(ascending=False).index]


def plot(R: pd.DataFrame, out: Path, name: str, fs: float = 7):
    import matplotlib.pyplot as plt
    from matplotlib.colors import LinearSegmentedColormap
    font = {"family": fp.FONT}
    cmap = LinearSegmentedColormap.from_list("r", ["#ffffff", "#9cb8ff", "#1f3f99"])
    lo, hi = -0.2, 0.7
    fig, ax = plt.subplots(figsize=(fp.ONE_COL, 3.9))
    fig.subplots_adjust(left=0.3, right=0.995, top=0.915, bottom=0.005)
    M = R.values
    fp.cell_rects(ax, np.clip(M, lo, hi), cmap, lo, hi)
    ax.set_aspect("auto")
    for (a, b), val in np.ndenumerate(M):
        if not np.isfinite(val):
            continue
        val = round(float(val), 2) + 0.0            # -0.004 -> 0.0, so no "−.00"
        ax.text(b, a, f"{val:.2f}".replace("0.", ".").replace("-.", "−."), ha="center", va="center", fontsize=5.5,
                fontdict=font, color="white" if val > 0.45 else fp.TEXT)
    ax.set_xticks(range(len(SETUP_KEYS)))
    ax.set_xticklabels([fp.SETUPS[s][0].replace(" + ", "\n+ ") for s in SETUP_KEYS], fontsize=6, fontdict=font)
    ax.xaxis.tick_top()
    ax.set_yticks(range(len(R)))
    ax.set_yticklabels([fp.model_label(m) for m in R.index], fontsize=6, fontdict=font)
    ax.tick_params(length=0, pad=2)
    for sp in ax.spines.values():
        sp.set_visible(False)
    out.mkdir(parents=True, exist_ok=True)
    fig.savefig(out / f"{name}.pdf")
    plt.close(fig)


def figure7(df: pd.DataFrame, out: Path, name: str) -> pd.DataFrame:
    R = table(df)
    plot(R, out, name=name)
    return R
