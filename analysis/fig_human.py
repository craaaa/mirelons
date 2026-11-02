#!/usr/bin/env python3
"""Paper Figures 2, 5 and 6: listener accuracy.

  Figure 2  (a) accuracy by passage version (mean of the four topic means), 95% CIs from a bootstrap over
            listeners stratified by Latin-square group, with paired-bootstrap significance stars; (b) each
            question's SayOnce accuracy against its SayTwice accuracy, Spearman rho.
  Figure 5  question accuracy in every pair of passage versions.
  Figure 6  accuracy by passage version within each topic.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

import levels_analysis as la
import levels_core as lc
import plotting as fp

VERSIONS = ["SayOnce", "SayTwice", "SayThrice", "Interfere"]          # = lc.LEVELS order
# one accent colour (versions are named on the axis, no colour coding); amber echoes the human band in Figure 3
BAR_FILL = "#E8A93A"
ONE_COL_W, ONE_COL_H = 3.02, 1.3


def question_table(H: lc.Pop) -> tuple[np.ndarray, np.ndarray]:
    """(Q20, L) correct counts and (Q20, L) response counts per question x version."""
    K, N, _ = lc.counts(H, np.ones((1, H.U)))
    k = K[0].transpose(0, 2, 1).reshape(lc.NT * lc.NQ, lc.NL)                     # (t,q) x l
    n = np.repeat(N[0][:, None, :], lc.NQ, axis=1).reshape(lc.NT * lc.NQ, lc.NL)
    return k, n


# planned version contrasts marked in (a): repetition gain and the two distractor contrasts
CONTRASTS = [("SayOnce", "SayTwice"), ("SayThrice", "Interfere"), ("SayOnce", "Interfere")]


def contrast_p(H: lc.Pop, truth, n_boot: int, seed: int) -> dict:
    """Two-sided paired bootstrap p (listeners resampled within Latin-square group, as own_bootstrap) for each
    contrast's version-mean difference, Holm-adjusted over CONTRASTS."""
    key = dict(zip(VERSIONS, (f"vm_{l}" for l in lc.LEVELS)))
    rng, v = np.random.default_rng(seed), {c: [] for c in CONTRASTS}
    for b0 in range(0, n_boot, 500):
        st = lc.summary_stats(*lc.counts(H, lc.stratified_counts(H.strata, min(500, n_boot - b0), rng)), truth)
        for a, b in CONTRASTS:
            v[(a, b)].append(st[key[a]] - st[key[b]])
    p = {}
    for c, x in v.items():
        x = np.concatenate(x)
        p[c] = max(min(1.0, 2 * min((x <= 0).mean(), (x >= 0).mean())), 1 / len(x))
    return lc.holm(p)


def _stars(p: float) -> str:
    return "***" if p < .001 else "**" if p < .01 else "*" if p < .05 else "n.s."


def _pct_labels(vals):
    return [f"{100 * v:.0f}" for v in vals]


def figure2(out: Path, name: str, n_boot: int = 10000, seed: int = 20261010):
    from plotnine import (aes, annotate, coord_flip, element_text, geom_col, geom_errorbar,
                          geom_point, ggplot, labs,
                          scale_x_continuous, scale_x_discrete, scale_y_continuous, theme)
    bank, truth, H = la.load_ref()
    boot = lc.own_bootstrap(H, truth, n_boot, seed)
    vm = pd.DataFrame({"version": VERSIONS,
                       "acc": [boot[f"vm_{l}"]["est"] for l in lc.LEVELS],
                       "lo": [boot[f"vm_{l}"]["lo"] for l in lc.LEVELS],
                       "hi": [boot[f"vm_{l}"]["hi"] for l in lc.LEVELS]})
    vm["version"] = pd.Categorical(vm.version, categories=VERSIONS[::-1])
    ov, ov_lo, ov_hi = boot["acc"]["est"], boot["acc"]["lo"], boot["acc"]["hi"]
    pc = contrast_p(H, truth, n_boot, seed)
    from scipy.stats import spearmanr

    k, n = question_table(H)
    p = k / n
    rho = spearmanr(p[:, 0], p[:, 1]).statistic          # question difficulty order, SayOnce vs SayTwice
    pts = pd.DataFrame([{"once": p[q, 0], "other": p[q, v], "version": VERSIONS[v]}
                        for q in range(p.shape[0]) for v in (1,)])
    pts["version"] = pd.Categorical(pts.version, categories=VERSIONS[1:])

    small = theme(axis_text=element_text(size=6.5), axis_title=element_text(size=7.5),
                  plot_title=element_text(margin={"b": 0.5, "units": "pt"}))
    # vertical bars + coord_flip (plotnine has no horizontal geom_col); in flipped coordinates the accuracy axis is y
    a = (ggplot(vm, aes("version", "acc"))
         + geom_col(fill=BAR_FILL, width=0.68, color=fp.INK, size=0.3)
         + geom_errorbar(aes(ymin="lo", ymax="hi"), width=0.28, color=fp.INK, size=0.45)
         + scale_y_continuous(limits=(0, 1), breaks=[0, .25, .5, .75, 1], labels=_pct_labels, expand=(0, 0))
         + scale_x_discrete(expand=(0, 0.35, 0, 0.75))   # extra room above the top bar for the "(a)" letter
         + coord_flip() + labs(y="Accuracy (%)", x="") + fp._theme() + small)
    # significance brackets to the right of the bars (flipped: x = version position, y = accuracy)
    pos = {v: i + 1 for i, v in enumerate(VERSIONS[::-1])}
    for (u, w), yb in zip(CONTRASTS, (0.64, 0.64, 0.84)):
        i, j = pos[u], pos[w]
        a = (a + annotate("segment", x=i, xend=j, y=yb, yend=yb, color=fp.INK, size=0.35)
             + annotate("segment", x=i, xend=i, y=yb - 0.02, yend=yb, color=fp.INK, size=0.35)
             + annotate("segment", x=j, xend=j, y=yb - 0.02, yend=yb, color=fp.INK, size=0.35)
             # rotated along the bracket, just to its right (the asterisk sits high in its line box, so after the
             # 90-degree turn its ink hugs the box's left edge: a small offset keeps it off the bracket)
             + annotate("text", x=(i + j) / 2, y=yb + 0.012, label=_stars(pc[(u, w)]), angle=90, va="center",
                        ha="left", size=8, color=fp.INK, family=fp.FONT))
    bb = (ggplot(pts, aes("once", "other"))
          + annotate("segment", x=0, xend=1, y=0, yend=1, color=fp.INK_SOFT, linetype="dotted", size=0.5)
          + geom_point(fill=BAR_FILL, color=fp.INK, size=1.2, stroke=0.25)
          + annotate("text", x=0.97, y=0.03, label=f"Spearman ρ = {rho:.2f}", ha="right", va="bottom", size=6.5,
                     color=fp.INK_SOFT, family=fp.FONT)
          + scale_x_continuous(limits=(0, 1), breaks=[0, .5, 1], labels=_pct_labels)
          + scale_y_continuous(limits=(0, 1), breaks=[0, .5, 1], labels=_pct_labels)
          + labs(x="SayOnce Accuracy (%)", y="SayTwice\nAccuracy (%)") + fp._theme() + small
          + theme(axis_title_y=element_text(margin={"r": 3.5, "units": "pt"}),
                  axis_title_x=element_text(margin={"t": 0, "units": "pt"})))
    fig = (((a | bb) & theme(figure_size=(ONE_COL_W, ONE_COL_H)))).draw()
    # panel letters in the free top-left corner beside each panel (no title row): placed after plotnine's layout,
    # which runs on save, at the panel's top edge and the left edge of its column
    letters = [fig.text(0, 0, t, ha="left", va="top", fontsize=8, fontweight="bold", family=fp.FONT, color=fp.TEXT)
               for t in ("(a)", "(b)")]
    engine, layout = fig.get_layout_engine(), fig.get_layout_engine().execute

    def execute(f):
        layout(f)
        for txt, ax, x in zip(letters, f.axes[:2], (0.004, 0.505)):
            txt.set_position((x, ax.get_position().y1))
    engine.execute = execute
    out.mkdir(parents=True, exist_ok=True)
    fp._save(fig, out, name, tight=True)
    print(f"versions {vm.set_index('version').acc.round(4).to_dict()}; overall {ov:.4f} [{ov_lo:.4f}, {ov_hi:.4f}]; "
          f"Holm p {({f'{u}-{w}': round(x, 4) for (u, w), x in pc.items()})}")


PAIRS = [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)]   # (x version, y version) indices into VERSIONS


def version_pair_panels(fs=(6.5, 7, 6.5)):
    """Figure 5 panels: each question's accuracy in one version (x) against another (y), for all six version pairs,
    styled like Figure 2(b) (dotted diagonal = no change; Spearman rho = agreement in question difficulty order).
    Returns the six plotnine panels."""
    from plotnine import aes, annotate, element_text, geom_point, ggplot, labs, scale_x_continuous, \
        scale_y_continuous, theme
    from scipy.stats import spearmanr
    bank, truth, H = la.load_ref()
    k, n = question_table(H)
    p = k / n
    small = theme(axis_text=element_text(size=fs[0]), axis_title=element_text(size=fs[1]), aspect_ratio=1,
                  axis_title_y=element_text(margin={"r": 1, "units": "pt"}),
                  axis_title_x=element_text(margin={"t": 0, "units": "pt"}))
    panels, rhos = [], {}
    for a, b in PAIRS:
        rho = spearmanr(p[:, a], p[:, b]).statistic
        rhos[f"{VERSIONS[a]}-{VERSIONS[b]}"] = round(float(rho), 3)
        d = pd.DataFrame({"x": p[:, a], "y": p[:, b]})
        panels.append(
            ggplot(d, aes("x", "y"))
            + annotate("segment", x=0, xend=1, y=0, yend=1, color=fp.INK_SOFT, linetype="dotted", size=0.5)
            + geom_point(fill=BAR_FILL, color=fp.INK, size=1.2, stroke=0.25)      # as Figure 2(b)
            + annotate("text", x=0.97, y=0.03, label=f"ρ = {rho:.2f}", ha="right", va="bottom", size=fs[2],
                       color=fp.INK_SOFT, family=fp.FONT)
            + scale_x_continuous(limits=(0, 1), breaks=[0, .5, 1], labels=_pct_labels)
            + scale_y_continuous(limits=(0, 1), breaks=[0, .5, 1], labels=_pct_labels)
            + labs(x=f"{VERSIONS[a]} (%)", y=f"{VERSIONS[b]} (%)") + fp._theme() + small)
    print(f"version-pair Spearman rho {rhos}")
    return panels


TOPIC_LABEL = {"astronomy": "Astronomy", "fabrics": "Fabric", "fruits": "Fruit",
               "martial_arts": "Martial Art"}                 # paper's order; names per user


def topics_plot(n_boot: int, seed: int, fs=(6.5, 7.5, 7), nrow: int = 2):
    """Figure 6: accuracy by version within each topic (vertical bars, shared y axis; otherwise styled like Figure 2a). CIs: listeners resampled within
    Latin-square group (same bootstrap as Figure 2a). Prints each topic's accuracy pooled over versions."""
    from plotnine import (aes, element_text, facet_wrap, geom_col, geom_errorbar, ggplot, labs,
                          scale_y_continuous, theme)
    bank, truth, H = la.load_ref()
    K, N, _ = lc.counts(H, np.ones((1, H.U)))
    acc = K[0].sum(-1) / (lc.NQ * N[0])                                        # (T, L)
    pooled = K[0].sum((-1, -2)) / (lc.NQ * N[0].sum(-1))                        # (T,)
    rng, boots = np.random.default_rng(seed), []
    for b0 in range(0, n_boot, 500):
        Kb, Nb, _ = lc.counts(H, lc.stratified_counts(H.strata, min(500, n_boot - b0), rng))
        boots.append(Kb.sum(-1) / (lc.NQ * Nb))
    lo, hi = np.nanpercentile(np.concatenate(boots), [2.5, 97.5], axis=0)      # (T, L) each
    order = [t for t in TOPIC_LABEL if t in lc.TOPICS]
    strip = {t: TOPIC_LABEL[t] for t in order}
    d = pd.DataFrame([{"topic": strip[t], "version": VERSIONS[l], "acc": acc[i, l], "lo": lo[i, l], "hi": hi[i, l]}
                      for t in order for i in [lc.TOPICS.index(t)] for l in range(lc.NL)])
    d["topic"] = pd.Categorical(d.topic, categories=[strip[t] for t in order])
    d["version"] = pd.Categorical(d.version, categories=VERSIONS)
    # vertical bars on a shared accuracy axis, so heights compare directly across topics
    g = (ggplot(d, aes("version", "acc"))
         + geom_col(fill=BAR_FILL, width=0.68, color=fp.INK, size=0.3)
         + geom_errorbar(aes(ymin="lo", ymax="hi"), width=0.28, color=fp.INK, size=0.45)
         + facet_wrap("~topic", nrow=nrow)
         + scale_y_continuous(limits=(0, 1), breaks=[0, .25, .5, .75, 1], labels=_pct_labels, expand=(0, 0))
         + labs(y="Accuracy (%)", x="") + fp._theme()
         + theme(axis_text=element_text(size=fs[0]), axis_title=element_text(size=fs[1]),
                 strip_text=element_text(size=fs[2]),
                 axis_text_x=element_text(rotation=45, ha="right", va="top"),
                 axis_title_y=element_text(margin={"r": 3, "units": "pt"}), panel_spacing_x=0.012))
    print("topic accuracy pooled over versions:",
          {TOPIC_LABEL[t]: round(float(pooled[lc.TOPICS.index(t)]), 3) for t in order})
    print("topic x version accuracy:", {strip[t]: dict(zip(VERSIONS, np.round(acc[lc.TOPICS.index(t)], 3)))
                                        for t in order})
    return g


def figures5_6(out: Path, names: tuple[str, str], n_boot: int = 10000, seed: int = 20261010):
    """Figures 5 and 6, one column each, with Figure 2's type sizes (6.5 pt ticks, 7.5 pt axis titles):
    Figure 5 (six square panels, 2 columns x 3 rows: right column Interfere (y) against
    SayOnce / SayTwice / SayThrice (x, one per row); left column the repetition pair with the same x version --
    SayTwice vs SayOnce, SayThrice vs SayTwice -- and, in the last row, SayThrice vs SayOnce) and Figure 6
    (accuracy by version within each topic, 2 x 2 facets)."""
    from plotnine import theme
    p = dict(zip(PAIRS, version_pair_panels((6.5, 7.5, 6.5))))
    rows = [((0, 1), (0, 3)), ((1, 2), (1, 3)), ((0, 2), (2, 3))]    # (left, right) per row; right = Interfere on y
    fig = ((p[rows[0][0]] | p[rows[0][1]]) / (p[rows[1][0]] | p[rows[1][1]]) / (p[rows[2][0]] | p[rows[2][1]])
           & theme(figure_size=(ONE_COL_W, 4.5))).draw()
    out.mkdir(parents=True, exist_ok=True)
    fp._save(fig, out, names[0], tight=True)
    fig = (topics_plot(n_boot, seed, (6.5, 7.5, 7), nrow=1) + theme(figure_size=(ONE_COL_W, 1.95))).draw()
    fp._save(fig, out, names[1], tight=True)
