"""Paper Figures 3, 8 and 9: models compared with listeners at three levels (overall accuracy, condition level,
item agreement).

  Figure 3  every configuration, grouped by setup
  Figure 8  every configuration, one row per model family
  Figure 9  Qwen2.5 and Qwen3 size ladders (batch encoding, k = 4, default prompt)
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

import plotting as fp

# distinct colours for up to 7 models in a family (Okabe-Ito order, black last), smallest / first model first
MODEL_COLORS = ["#0072B2", "#E69F00", "#009E73", "#CC79A7", "#D55E00", "#56B4E9", "#000000"]

SETUP_LABELS = [v[0] for v in fp.SETUPS.values()]

SETUP_SHAPES = {v[0]: v[2] for v in fp.SETUPS.values()}
# Figure 8 rows: small families share a row
GROUPS = [("Qwen2.5", ["Qwen2.5"]), ("Qwen3", ["Qwen3"]), ("Google", ["Gemini", "Gemma"]),
          ("Anthropic + OpenAI", ["Claude", "GPT-6"]), ("DeepSeek + GLM", ["DeepSeek", "GLM"])]

def combined_figure(d: pd.DataFrame, R: dict, out: Path, row_h: float = 1.55, name: str = "figure8_three_levels_by_family",
                    pt: dict | None = None):
    pt = pt or dict(size=1.4, alpha=1.0)
    """All models: one row per group, shared axis ranges, per-row model legend on the right."""
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    from plotnine import (aes, annotate, coord_flip, element_blank, geom_hline, geom_point, ggplot, labs,
                          position_dodge, scale_color_manual, scale_fill_manual, scale_shape_manual,
                          scale_x_continuous, scale_x_discrete, scale_y_continuous, theme)
    pad = lambda lo, hi, f=0.06: (lo - f * (hi - lo), hi + f * (hi - lo))
    gx = pad(min(d.gain_pp.min(), R["gain_lo"]), max(d.gain_pp.max(), R["gain_hi"]))
    gy = pad(min(d.od_pp.min(), R["od_lo"]), max(d.od_pp.max(), R["od_hi"]))
    rlim = (min(np.nanmin(d.r), 0) - 0.05, 1.02)
    rows = ["Human"] + SETUP_LABELS
    n = len(GROUPS)
    plots, legends = [], []
    for i, (gname, fams) in enumerate(GROUPS):
        sub_ = d[d.family.isin(fams)]
        labels = sorted(sub_.model.map(fp.model_label).unique(),
                        key=lambda l: (fams.index(sub_[sub_.model.map(fp.model_label) == l].family.iloc[0]),
                                       fp._size_key(l)))
        col = dict(zip(labels, MODEL_COLORS))
        e = sub_.assign(Model=pd.Categorical(sub_.model.map(fp.model_label), labels),
                        Setup=pd.Categorical(sub_.Setup.astype(str), SETUP_LABELS),
                        row=pd.Categorical(sub_.Setup.astype(str), rows[::-1]))
        scales = [scale_color_manual(values=col), scale_fill_manual(values=col),
                  scale_shape_manual(values=SETUP_SHAPES)]
        top, bottom = i == 0, i == n - 1

        def strip(x, lo, hi, star, title, xlab, lim, show_y):
            p = (ggplot(e, aes("row", x, group="Model"))
                 + annotate("rect", ymin=lo, ymax=hi, xmin=-np.inf, xmax=np.inf, fill=fp.HUMAN_BAND,
                            alpha=fp.HUMAN_BAND_ALPHA)
                 + geom_hline(yintercept=0, color=fp.INK_SOFT, size=0.5)
                 + geom_hline(yintercept=star, color=fp.INK, linetype="dotted", size=0.5)
                 + geom_point(aes(fill="Model", shape="Setup"), color=fp.INK, size=pt["size"], alpha=pt["alpha"],
                              stroke=0.25, position=position_dodge(width=0.7))
                 + fp._human_pt("Human", star)
                 + scale_x_discrete(drop=False) + scale_y_continuous(limits=lim) + coord_flip()
                 + labs(title=title if top else "", y=xlab if bottom else "", x="") + fp._theme() + scales)
            return p if show_y else p + theme(axis_text_y=element_blank(), axis_ticks_major_y=element_blank())

        pa = strip("acc_pct", R["acc_lo"], R["acc_hi"], R["acc"], "(a) Overall accuracy", "Accuracy (%)",
                   (0, 100), True)
        pb = (ggplot(e, aes("gain_pp", "od_pp")) + fp._ref_layers_b(R, fp.HUMAN_BAND, fp.HUMAN_BAND_ALPHA, y="od")
              + fp._star_b(R, hollow=True, y="od")
              + geom_point(aes(fill="Model", shape="Setup"), color=fp.INK, size=pt["size"], alpha=pt["alpha"],
                           stroke=0.25)
              + scale_x_continuous(limits=gx) + scale_y_continuous(limits=gy)
              + labs(title="(b) Condition level" if top else "", x=fp.LAB_B["x"].replace(" (", "\n(") if bottom else "",
                     y=fp.LAB_B["y"].replace(" (", "\n(")) + fp._theme() + scales)
        pc = strip("r", R["r_lo"], 1.0, R["r"], "(c) Item level",
                   "Correlation on item difficulty (r)", rlim, False)
        pc = pc + theme(plot_margin_right=0.19)
        if bottom:
            pa, pb, pc = (q + theme(plot_margin_bottom=0.062) for q in (pa, pb, pc))
        plots.append(pa | pb | pc)
        legends.append((gname, labels, col))
    comp = plots[0]
    for q in plots[1:]:
        comp = comp / q
    fig = (comp & theme(figure_size=(fp.TWO_COL, row_h * n + 0.9))).draw()
    kw = dict(frameon=False, prop={"family": fp.FONT, "size": 6.5}, handletextpad=0.3, borderaxespad=0.0,
              labelspacing=0.35)
    item_axes = [a for k, a in enumerate(fig.axes) if k % 3 == 2]
    row_legends = []
    for (gname, labels, col), ax in zip(legends, item_axes):
        hm = [Line2D([], [], marker="o", markerfacecolor=col[l], markeredgecolor=fp.INK, markeredgewidth=0.5,
                     linestyle="none", markersize=4.5, label=l) for l in labels]
        leg = fig.legend(handles=hm, loc="center left", bbox_to_anchor=(0.82, 0.5), title=gname,
                         title_fontproperties={"family": fp.FONT, "size": 7, "weight": "bold"}, **kw)
        leg._legend_box.align = "left"
        row_legends.append((leg, ax))

    # plotnine positions the axes only when the figure is laid out (on save), so anchor each row legend to its
    # item-level panel after every layout pass
    engine = fig.get_layout_engine()
    layout = engine.execute

    def execute(f):
        layout(f)
        for leg, ax in row_legends:
            pos = ax.get_position()
            leg.set_bbox_to_anchor((pos.x1 + 0.012, (pos.y0 + pos.y1) / 2), transform=f.transFigure)
    engine.execute = execute
    hs = [Line2D([], [], marker=SETUP_SHAPES[s_], markerfacecolor="white", markeredgecolor=fp.INK,
                 markeredgewidth=0.6, linestyle="none", markersize=5, label=s_) for s_ in SETUP_LABELS]
    hr = [fp._human_handle(), Line2D([], [], color=fp.INK, linestyle=":", linewidth=1.0, label="Human value"),
          Patch(facecolor=fp.HUMAN_BAND, alpha=fp.HUMAN_BAND_ALPHA, edgecolor="none", label="Bootstrapped 95% Confidence Interval")]
    fig.legend(handles=hs, loc="lower center", bbox_to_anchor=(0.5, 0.017), ncol=len(hs),
               **{**kw, "columnspacing": 1.0})
    fig.legend(handles=hr, loc="lower center", bbox_to_anchor=(0.5, 0.0), ncol=len(hr),
               **{**kw, "columnspacing": 1.0})
    fp._save(fig, out, name)


LADDERS = {"Qwen2.5": r"^Qwen_Qwen2\.5-", "Qwen3": r"^Qwen_Qwen3-"}   # Qwen3.8 is a different release

def ladder_mask(df: pd.DataFrame):
    """Configurations in the size-ladder figure: Qwen2.5 / Qwen3 sizes, batch, k = 4 (prompted: default prompt),
    main sampling arm, both thinking modes."""
    pat = "|".join(LADDERS.values())
    return (df.model_slug.str.contains(pat, regex=True) & (df.k.isna() | (df.k == 4)) & (df.encode == "batch")
            & df.prompt_default)

SIZE_RANGE_B, SIZE_PT = (0.5, 72.0), (0.6, 2.8)   # (b) point size: parameters (B, log scale) -> plotnine size

SIZE_BREAKS_B = (0.5, 3, 14, 72)                    # sizes shown in the (b) point-size legend

def size_pt(b):
    """Point size in row (b) of the size figure: linear in log10(parameters) over SIZE_RANGE_B."""
    import numpy as np
    lo, hi = np.log10(SIZE_RANGE_B)
    t = np.clip((np.log10(b) - lo) / (hi - lo), 0, 1)
    return SIZE_PT[0] + t * (SIZE_PT[1] - SIZE_PT[0])

def plot_size_ladder(df: pd.DataFrame, out: Path, name: str):
    """Figure 9: model size (parameters, log scale) within a family against the three levels. Rows (a) overall
    accuracy and (c) item agreement (r) against size; (b) condition level as in Figure 3b, repetition gain (x)
    against interference, SayOnce - Interfere (y), with point size growing with parameters and a path per family x
    thinking mode joining the sizes in order. One panel per setup; colour = family, line type = thinking mode
    (Qwen3); human value (dotted line in (a), (c); star in (b)) and 95% range (shaded)."""
    import re
    import numpy as np
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    from plotnine import (aes, annotate, facet_wrap, geom_hline, geom_line, geom_path, geom_point, geom_rect,
                          ggplot, labs,
                          scale_color_manual, scale_fill_manual, scale_linetype_manual, scale_shape_manual,
                          scale_size_identity, scale_x_log10, theme)
    d = fp._prep(df[ladder_mask(df)])
    d["Family"] = [next(f for f, pat in LADDERS.items() if re.search(pat, m)) for m in d.model_slug]
    d["size_b"] = [float(re.search(r"([\d.]+)B", m).group(1)) for m in d.model_slug]
    d["Mode"] = np.where(d.thinking == "off", "thinking off", "thinking on / n/a")
    d["line"] = d.Family + " · " + d.Mode
    d["pt"] = size_pt(d.size_b)
    d = d.sort_values("size_b")
    R = fp._refs(df)
    col = {f: fp.FAMILY_HUE[f] for f in LADDERS}
    shp = {"Qwen2.5": fp.FAMILY_SHAPE["Qwen2.5"], "Qwen3": fp.FAMILY_SHAPE["Qwen3"]}
    lt = {"thinking on / n/a": "solid", "thinking off": "dashed"}
    style = [scale_color_manual(values=col), scale_fill_manual(values=col), scale_shape_manual(values=shp),
             scale_linetype_manual(values=lt)]
    breaks = [0.5, 1, 3, 7, 14, 32, 72]

    def by_size(y, title, ylab, ref, lo, hi):
        e = d[np.isfinite(d[y])]
        # finite x range: an infinite band does not survive the log10 scale transform
        band = pd.DataFrame({"xmin": [0.4], "xmax": [90.0], "ymin": [lo], "ymax": [hi]})
        return (ggplot(e, aes("size_b", y))
                + geom_rect(aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax"), data=band,
                            inherit_aes=False, fill=fp.HUMAN_BAND, alpha=fp.HUMAN_BAND_ALPHA)
                + geom_hline(yintercept=ref, color=fp.INK, linetype="dotted", size=0.5)
                + geom_line(aes(group="line", color="Family", linetype="Mode"), size=0.5, alpha=0.9)
                + geom_point(aes(fill="Family", shape="Family"), color=fp.INK, size=1.1, stroke=0.25)
                + facet_wrap("Setup", nrow=1)
                + scale_x_log10(breaks=breaks, labels=[f"{b:g}" for b in breaks], limits=(0.4, 90),
                                expand=(0, 0))
                + style + labs(title=title, x=("Parameters (B)" if y == "r" else ""), y=ylab) + fp._theme()
                + theme(axis_text_x=fp_text(6)))

    # (b) condition level, axes as in Figure 3b; the path follows increasing size, points are drawn largest first
    # so a small model under a large one stays visible; human value as a star over its 95% range (both effects)
    e = d[np.isfinite(d.gain_pp) & np.isfinite(d.od_pp)]
    mid = (ggplot(e, aes("gain_pp", "od_pp")) + fp._ref_layers_b(R, fp.HUMAN_BAND, fp.HUMAN_BAND_ALPHA, y="od")
           + geom_path(aes(group="line", color="Family", linetype="Mode"), size=0.4, alpha=0.6)
           + geom_point(aes(fill="Family", shape="Family", size="pt"), data=e.sort_values("size_b", ascending=False),
                        color=fp.INK, stroke=0.25)
           + annotate("point", x=R["gain"], y=R["od"], shape="*", size=3.2, color=fp.INK)
           + facet_wrap("Setup", nrow=1) + style + scale_size_identity()
           + labs(title="(b) Condition level", **fp.LAB_B) + fp._theme())
    top = by_size("acc_pct", "(a) Overall accuracy", "Accuracy (%)", R["acc"], R["acc_lo"], R["acc_hi"])
    bot = by_size("r", "(c) Item agreement", "Item agreement (r)", R["r"], R["r_lo"], 1.0)
    top = top + theme(plot_margin_bottom=0.005)
    mid = mid + theme(plot_margin_bottom=0.005)
    bot = bot + theme(plot_margin_bottom=0.095)
    fig = ((top / mid / bot) & theme(figure_size=(fp.TWO_COL, 6.3))).draw()
    mk = dict(markersize=4, markeredgecolor=fp.INK, markeredgewidth=0.5, linewidth=1)
    handles = [Line2D([], [], color=col["Qwen2.5"], markerfacecolor=col["Qwen2.5"], marker=shp["Qwen2.5"],
                      label="Qwen2.5", **mk),
               Line2D([], [], color=col["Qwen3"], markerfacecolor=col["Qwen3"], marker=shp["Qwen3"],
                      label="Qwen3, thinking on", **mk),
               Line2D([], [], color=col["Qwen3"], markerfacecolor=col["Qwen3"], marker=shp["Qwen3"], linestyle="--",
                      label="Qwen3, thinking off", **mk),
               Line2D([], [], color=fp.INK, linestyle=":", linewidth=1.0, marker="*", markersize=6,
                      label="Human value"),
               Patch(facecolor=fp.HUMAN_BAND, alpha=fp.HUMAN_BAND_ALPHA, edgecolor="none",
                     label="Bootstrapped 95% Confidence Interval")]
    prop = {"family": fp.FONT, "size": 7}
    leg = fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(0.5, 0.022), ncol=len(handles),
                     frameon=False, prop=prop, handletextpad=0.4, columnspacing=1.2)
    fig.add_artist(leg)
    # point size in (b): plotnine draws a point of size s with stroke w as a marker (s + w) * sqrt(pi) pt across
    sq = float(np.sqrt(np.pi))
    sizes = [Line2D([], [], linestyle="none", label="(b) point size:")]
    sizes += [Line2D([], [], linestyle="none", marker="o", markerfacecolor="#d9d4cc", markeredgecolor=fp.INK,
                     markeredgewidth=0.25 * sq, markersize=(float(size_pt(b)) + 0.25) * sq,
                     label=f"{b:g}B") for b in SIZE_BREAKS_B]
    fig.legend(handles=sizes, loc="lower center", bbox_to_anchor=(0.5, 0.0), ncol=len(sizes), frameon=False,
               prop=prop, handletextpad=0.3, columnspacing=1.0, handlelength=1.0)
    fp._save(fig, out, name)
    return d.groupby("Family").model_slug.nunique().to_dict()

def fp_text(size):
    from plotnine import element_text
    return element_text(size=size)


def figure3(df: pd.DataFrame, out: Path, name: str) -> int:
    """Every configuration; returns the number without an estimable item agreement."""
    return fp.plot_main(df, out, name)


def figure8(df: pd.DataFrame, out: Path, name: str) -> None:
    d = fp._prep(df)
    d.loc[d.L3a_verdict == "not estimable", "r"] = np.nan   # model's own item reliability < .5
    combined_figure(d, fp._refs(d), out, name=name, pt=dict(size=0.9, alpha=0.7))


def figure9(df: pd.DataFrame, out: Path, name: str) -> None:
    plot_size_ladder(df[df.prompt_default], out, name)
