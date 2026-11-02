"""Paper Figure 4: statement endorsement rates in listeners and two representative configurations.

Each matrix: rows = endorsed / not endorsed, columns = true / false statement (content options 1-4; "None of the
above" left out), cells = % of the column. Columns of the figure: Overall (mean of the four versions), SayOnce,
Interfere. Model rows: Gemini 3.1 Pro (Compactor, k = 4; the median model) and Qwen3-4B (Compactor, k = 5,
thinking off; among the most human-like at the item level).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

import levels_analysis as la
import levels_core as lc
import plotting as fp
from paths import RUNS

VERSIONS = [lc.LEVEL_LABEL[l] for l in lc.LEVELS]
COLS = ["Overall", "SayOnce", "Interfere"]
CELLS = [["true hit", "missed"], ["false endorsement", "true abstention"]]
# (model_slug, profile, task, condition) -> row label
CONFIGS = {("gemini-3.1-pro-preview", "gemini-3.1-pro", "compactor-batch_k4", "C2"): "Gemini 3.1 Pro\n(Compactor, k = 4)",
           ("Qwen_Qwen3-4B", "qwen3-off", "compactor-batch_k5", "C2"): "Qwen3-4B\n(Compactor, k = 5)"}


def cells(pop: lc.Pop, truth) -> pd.DataFrame:
    """Rows = versions, columns = the four cells (proportions)."""
    _, N, E = lc.counts(pop, np.ones((1, pop.U)))
    hit, fe = lc.option_rates(E, N, truth)
    return pd.DataFrame({"true hit": hit[0], "missed": 1 - hit[0], "false endorsement": fe[0],
                         "true abstention": 1 - fe[0]}, index=VERSIONS)


def rates(runs: Path = RUNS) -> dict:
    """{row label: {column: 2x2 array in %}} for listeners and each configuration in CONFIGS."""
    bank, truth, H = la.load_ref()

    def mats(c: pd.DataFrame) -> dict:
        return {col: 100 * np.array([[(c[x].mean() if col == "Overall" else c.loc[col, x]) for x in row]
                                     for row in CELLS]) for col in COLS}

    out = {"Humans": mats(cells(H, truth))}
    for (slug, profile, task, cond), label in CONFIGS.items():
        path = lc.run_files(runs / slug / profile / task / "tasks")[0]
        out[label] = mats(cells(lc.load_model_jsonl(path, bank, cond), truth))
    return out


def figure4(out: Path, name: str, fs: float = 7):
    """Matrices drawn transposed (rows = endorsed / not endorsed, columns = true / false statement) so every label
    fits on one line at one font size; row titles horizontal at one x, centred on their row."""
    import matplotlib.pyplot as plt
    from matplotlib.colors import LinearSegmentedColormap
    M = rates()
    cmap = LinearSegmentedColormap.from_list("abs", ["#ffffff", "#9cb8ff", "#1f3f99"])
    font, bold = {"family": fp.FONT}, {"family": fp.FONT, "weight": "bold"}
    groups = list(M)
    # empty spacer column after "Overall" so it reads as separate from the per-version columns
    # height derived from the (square) matrix width, so rows carry no vertical slack: top / bottom / gap in inches
    left, right, wspace, ratios = 0.485, 0.995, 0.06, [1, 0.18] + [1] * (len(COLS) - 1)
    units = sum(ratios) + wspace * (sum(ratios) / len(ratios)) * (len(ratios) - 1)
    w = fp.ONE_COL * (right - left) / units             # matrix side, inches
    top_in, bottom_in, gap_in = 0.15, 0.14, 0.05
    height = top_in + bottom_in + len(groups) * w + (len(groups) - 1) * gap_in
    fig = plt.figure(figsize=(fp.ONE_COL, height))
    gs = fig.add_gridspec(len(groups), len(COLS) + 1, width_ratios=ratios, left=left, right=right,
                          top=1 - top_in / height, bottom=bottom_in / height, wspace=wspace, hspace=gap_in / w)
    axes = np.array([[fig.add_subplot(gs[i, j if j == 0 else j + 1]) for j in range(len(COLS))]
                     for i in range(len(groups))])
    for i, g in enumerate(groups):
        for j, col in enumerate(COLS):
            ax, m = axes[i, j], M[g][col].T                  # rows: endorsed / not endorsed; cols: true / false
            fp.cell_rects(ax, m, cmap, 0, 100)
            for (a, b), val in np.ndenumerate(m):
                txt = f"{val:.1f}" if (val < 10 or val > 99) and round(val, 1) not in (0, 100) else f"{val:.0f}"
                ax.text(b, a, txt, ha="center", va="center", fontsize=fs, fontdict=font,
                        color="white" if val > 55 else fp.TEXT)
            ax.set_xticks([0, 1])
            ax.set_yticks([0, 1])
            ax.set_xticklabels(["True", "False"] if i == len(groups) - 1 else [], fontsize=fs, fontdict=font)
            ax.set_yticklabels(["Endorsed", "Not endorsed"] if j == 0 else [], fontsize=fs, fontdict=font)
            ax.tick_params(length=0, pad=1.5)
            for sp in ax.spines.values():
                sp.set_color(fp.INK_SOFT)
                sp.set_linewidth(0.5)
            if i == 0:
                ax.set_title(col, fontsize=fs, fontdict=bold, pad=2.5)
        # row title: horizontal, left-aligned at a fixed x for every row, centred on the row
        box = axes[i, 0].get_position()
        fig.text(0.008, (box.y0 + box.y1) / 2, g, ha="left", va="center", fontsize=fs, fontdict=bold,
                 multialignment="left")
    out.mkdir(parents=True, exist_ok=True)
    fig.savefig(out / f"{name}.pdf", bbox_inches="tight", pad_inches=0.01)
    plt.close(fig)
