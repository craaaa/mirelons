"""Shared figure style and the three-level panels (paper Figures 3 and 8): colours, markers and labels per setup and
model family, the plotnine theme, human reference layers, and the PDF writer."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

SETUPS = {  # key -> (label, kind, matplotlib marker)
    "prompted": ("Prompted", "prompted", "o"),
    "compactor": ("Compactor", "model-chosen memory", "s"),
    "summary": ("Summary", "model-chosen memory", "D"),
    "chosen-propositions": ("CBUS", "model-chosen memory", "^"),
    "random-dropout": ("CBUS + Dropout", "random dropout", "p"),
}

# One colour per setup: IBM Design Library colour-blind-safe palette (all five). Validator: CVD separation
# dE >= 18; gold is too light on white (1.8:1, outside the lightness band) and blue/orange are just under 3:1 ->
# the per-setup marker shape is the secondary cue. (Previously tried: Okabe & Ito; a user palette.)
SETUP_COLOR = {"prompted": "#648FFF", "compactor": "#FE6100", "summary": "#785EF0",
               "chosen-propositions": "#DC267F", "random-dropout": "#009E73"}

INK, INK_SOFT, PANEL, GRID, TEXT = "#5b4f41", "#6c6154", "#ffffff", "#ede9e3", "#000000"

# Model families: display order, and colour / marker in Figure 9
FAMILY_ORDER = ["Qwen2.5", "Qwen3", "Gemini", "Gemma", "GPT-6", "Claude", "DeepSeek", "GLM"]

FAMILY_HUE = {"Qwen2.5": "#2a78d6", "Qwen3": "#eb6834", "Gemini": "#1baf7a", "Gemma": "#eda100",
              "GPT-6": "#e87ba4", "Claude": "#008300", "DeepSeek": "#4a3aa7", "GLM": "#e34948"}

FAMILY_SHAPE = {"Qwen2.5": "o", "Qwen3": "s", "Gemini": "D", "Gemma": "<", "GPT-6": "^", "Claude": "v",
                "DeepSeek": "p", "GLM": "h"}

MODEL_LABEL = {
    "gemini-3.1-pro-preview": "Gemini 3.1 Pro", "gemini-3.5-flash-lite": "Gemini 3.5 Flash-Lite",
    "gemini-3.6-flash": "Gemini 3.6 Flash", "gemini-3.8-flash": "Gemini 3.8 Flash",
    "google_gemma-4-31B-it": "Gemma 4 31B", "gpt-6-luna": "GPT-6 Luna", "gpt-6-sol": "GPT-6 Sol",
    "claude-haiku-5-5": "Claude Haiku 5.5", "claude-sonnet-5": "Claude Sonnet 5",
    "deepseek_deepseek-v4-pro-0813": "DeepSeek V4-Pro", "deepseek_deepseek-v4.1-flash": "DeepSeek V4.1-Flash",
    "z-ai_glm-5.2": "GLM-5.2", "z-ai_glm-5.3-flash": "GLM-5.3-Flash",
}

def model_label(slug: str) -> str:
    """Short display name: Qwen_Qwen2.5-7B-Instruct -> 'Qwen2.5 7B', Qwen_Qwen3-0.6B -> 'Qwen3 0.6B', etc."""
    import re
    if slug in MODEL_LABEL:
        return MODEL_LABEL[slug]
    m = re.fullmatch(r"Qwen_Qwen([\d.]+)-([\d.]+B)(-Instruct)?", slug)
    return f"Qwen{m.group(1)} {m.group(2)}" if m else slug

def _size_key(label: str):
    import re
    m = re.search(r"([\d.]+)B\b", label)
    return (0, float(m.group(1)), label) if m else (1, 0.0, label)

ONE_COL, TWO_COL = 3.0, 6.3
FONT = "DejaVu Sans"   # replaced by Source Sans Pro when _register_fonts finds it

# Figure 3: human-like region (human 95% range) in light yellow; where the x and y ranges cross, the overlap is
# a little darker.
HUMAN_BAND, HUMAN_BAND_ALPHA = "#FFE066", 0.4

def _human_pt(x, y):
    """Human marker (bold +, open centre so a point on the human value stays visible), as an annotate layer."""
    from plotnine import annotate
    return annotate("point", x=x, y=y, shape="+", size=5, color=INK, stroke=1.1)


def _human_handle():
    """Legend handle matching _human_pt."""
    from matplotlib.lines import Line2D
    return Line2D([], [], marker="+", color=INK, markeredgewidth=1.6, linestyle="none", markersize=8,
                  label="Human")


def _register_fonts(font_dir: str | None):
    global FONT
    if not font_dir:
        return
    from matplotlib import font_manager
    fs = sorted(Path(font_dir).glob("*.ttf"))
    for f in fs:
        font_manager.fontManager.addfont(str(f))
    if fs:
        FONT = "Source Sans Pro"

def _theme(base_size=8):
    from plotnine import element_blank, element_line, element_rect, element_text, theme, theme_bw
    return theme_bw(base_size=base_size) + theme(
        text=element_text(family=FONT, color=TEXT),
        axis_text=element_text(color=TEXT, size=base_size - 1),
        axis_text_y=element_text(va="center"),
        axis_title=element_text(color=TEXT, size=base_size),
        axis_title_x=element_text(margin={"t": 0, "units": "pt"}),
        axis_text_x=element_text(margin={"t": 0.5, "units": "pt"}),
        axis_title_y=element_text(margin={"r": 1.5, "units": "pt"}),
        plot_title=element_text(color=TEXT, size=base_size, ha="left", weight="bold", margin={"b": 1.5, "units": "pt"}),
        panel_background=element_rect(fill=PANEL),
        panel_border=element_rect(color=INK_SOFT, size=0.6),
        panel_grid_major=element_line(color=GRID, linetype="dashdot", size=0.45),
        panel_grid_minor=element_blank(),
        axis_ticks=element_line(color=INK_SOFT, size=0.4),
        strip_background=element_rect(fill="#000000", color="#000000"),
        strip_text=element_text(color="white", size=base_size - 0.5, va="center",   # centre on glyphs, not baseline
                                margin={"t": 1.6, "b": 3.4, "units": "pt"}),
        legend_position="none",
        plot_background=element_rect(fill="white", color="white"),
        plot_margin=0.01,
    )

def _scales():
    from plotnine import scale_color_manual, scale_fill_manual, scale_shape_manual
    return [scale_shape_manual(values={v[0]: v[2] for v in SETUPS.values()}),
            scale_color_manual(values={SETUPS[k][0]: c for k, c in SETUP_COLOR.items()}),
            scale_fill_manual(values={SETUPS[k][0]: c for k, c in SETUP_COLOR.items()})]

def _prep(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["Setup"] = pd.Categorical(df.setup.map(lambda s: SETUPS[s][0]), categories=[v[0] for v in SETUPS.values()])
    df["acc_pct"] = 100 * df.L1_model_acc
    df["r"] = df.L3a_model_r_with_half
    df["gain_pp"], df["cost_pp"] = 100 * df.L2_gain_model, 100 * df.L2_cost_model
    df["od_pp"] = 100 * df.L2_cost_model   # SayOnce - Interfere (Figure 3b y axis)
    return df

def _refs(df: pd.DataFrame) -> dict:
    h = df.iloc[0]
    return dict(acc=100 * h.human_acc, acc_lo=100 * h.human_acc_lo, acc_hi=100 * h.human_acc_hi,
                r=df.L3a_ref_median.median(), r_lo=df.L3a_ref_p05.median(),
                gain=100 * h.human_gain, gain_lo=100 * h.human_gain_lo, gain_hi=100 * h.human_gain_hi,
                cost=100 * h.human_cost, cost_lo=100 * h.human_cost_lo, cost_hi=100 * h.human_cost_hi,
                od=100 * h.get("human_od", np.nan), od_lo=100 * h.get("human_od_lo", np.nan),
                od_hi=100 * h.get("human_od_hi", np.nan))

def _star_b(R, hollow=False, y="cost"):
    """Listener star for gain x cost, drawn on top of the points; hollow in Figure 3 so a setup point under it
    stays visible."""
    from plotnine import annotate
    if hollow:
        return _human_pt(R["gain"], R[y])
    return annotate("point", x=R["gain"], y=R[y], shape="*", size=5, color=INK)

def _ref_layers_b(R, band=INK, alpha=0.12, y="cost"):
    from plotnine import annotate, geom_hline, geom_vline
    return [geom_hline(yintercept=0, color=INK_SOFT, size=0.5),
            geom_vline(xintercept=0, color=INK_SOFT, size=0.5),
            annotate("rect", xmin=R["gain_lo"], xmax=R["gain_hi"], ymin=R[f"{y}_lo"], ymax=R[f"{y}_hi"],
                     fill=band, alpha=alpha)]

LAB_B = dict(x="Effect of Repetition (Δ%)", y="Effect of Interference (Δ%)")

def _legend(fig, setups, gap: float = 0.06):
    """Shared legend under the whole figure: row 1 = setups, row 2 = human references."""
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    kw = dict(frameon=False, prop={"family": FONT, "size": 7}, handletextpad=0.4, columnspacing=1.4)
    h1 = [Line2D([], [], marker=SETUPS[s][2], markerfacecolor=SETUP_COLOR[s], markeredgecolor=INK,
                 markeredgewidth=0.5, linestyle="none",
                 markersize=5.5, label=SETUPS[s][0]) for s in setups]
    h2 = [_human_handle(),
          Line2D([], [], color=INK, linestyle=":", linewidth=1.0, label="Human value"),
          Patch(facecolor=HUMAN_BAND, alpha=HUMAN_BAND_ALPHA, edgecolor="none", label="Bootstrapped 95% Confidence Interval")]
    fig.legend(handles=h1, loc="lower center", bbox_to_anchor=(0.5, gap), ncol=len(h1), **kw)
    fig.legend(handles=h2, loc="lower center", bbox_to_anchor=(0.5, 0.0), ncol=len(h2), **kw)


def _snap_ytitles(fig, renderer, pad_pt: float = 3.0, min_gap_pt: float = 8.0):
    """Move a vertical axis title that sits far from its own panel's tick labels back next to them (stacked
    compositions align panel edges across rows, which can strand a title under a panel with long row labels).
    Only the x position changes; runs right after plotnine's layout engine (see _save)."""
    px = fig.dpi / 72
    width = fig.bbox.width
    boxes = [(a, a.get_window_extent(renderer)) for a in fig.axes if a.get_visible()]
    for t in fig.texts:
        if abs(t.get_rotation() - 90) > 1 or not t.get_text().strip():
            continue
        tb = t.get_window_extent(renderer)
        ty = (tb.y0 + tb.y1) / 2
        right = [(a, bb) for a, bb in boxes if bb.y0 <= ty <= bb.y1 and bb.x0 >= tb.x1 - 1]
        if not right:
            continue
        ax, bb = min(right, key=lambda x: x[1].x0 - tb.x1)
        labels = [l.get_window_extent(renderer).x0 for l in ax.get_yticklabels() if l.get_text()]
        target = min(labels + [bb.x0]) - pad_pt * px
        gap = target - tb.x1
        if gap > min_gap_pt * px:
            x, y = t.get_position()
            t.set_position((x + gap / width, y))

def _save(fig, out: Path, name: str, tight: bool = False):
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    if not hasattr(fig.canvas, "get_renderer"):
        FigureCanvasAgg(fig)
    engine = fig.get_layout_engine()
    if engine is not None and not getattr(engine, "_snaps_ytitles", False):
        layout = engine.execute

        def execute(f):   # plotnine lays the figure out on every draw; adjust y titles right after it
            layout(f)
            _snap_ytitles(f, f._get_renderer())
        engine.execute = execute
        engine._snaps_ytitles = True
    # tight = crop the page to its content
    fig.savefig(out / f"{name}.pdf", **({"bbox_inches": "tight", "pad_inches": 0.01} if tight else {}))

def _strip(d: pd.DataFrame, x: str, R: dict, kind: str, title: str, xlab: str, show_y: bool):
    """One row per setup (+ a Human row on top): a horizontal boxplot of the models (Tukey whiskers) with the
    individual models as small faint points; human star, value line and 95% range; zero line."""
    from plotnine import (aes, annotate, coord_flip, element_blank, geom_boxplot, geom_hline, geom_point, ggplot,
                          labs, position_jitter, scale_x_discrete, theme)
    rows = ["Human"] + [v[0] for v in SETUPS.values()]
    d = d.assign(row=pd.Categorical(d["Setup"].astype(str), categories=rows[::-1]))
    star, lo, hi = (R["acc"], R["acc_lo"], R["acc_hi"]) if kind == "acc" else (R["r"], R["r_lo"], 1.0)
    # vertical boxes + coord_flip (plotnine draws boxplots along x); the value axis is y before flipping
    p = (ggplot(d, aes("row", x))
         + annotate("rect", ymin=lo, ymax=hi, xmin=-np.inf, xmax=np.inf, fill=HUMAN_BAND, alpha=HUMAN_BAND_ALPHA)
         + geom_hline(yintercept=0, color=INK_SOFT, size=0.5)            # zero line, as the axes at 0 in (b)
         + geom_hline(yintercept=star, color=INK, linetype="dotted", size=0.5)
         + geom_boxplot(aes(fill="Setup"), color=INK, width=0.62, size=0.35, alpha=0.75, outlier_shape="")
         + geom_point(aes(shape="Setup"), fill="white", color=INK, size=0.7, stroke=0.2, alpha=0.7,
                      position=position_jitter(width=0.14, height=0, random_state=1))
         + _human_pt("Human", star)
         + scale_x_discrete(drop=False) + _scales() + coord_flip()
         + labs(title=title, y=xlab, x="") + _theme())
    if kind == "r":   # label the human dotted line, written along it just to its left, below the star
        p = p + annotate("text", x=3.05, y=star - 0.035, label="Human split-half reliability", angle=90,
                         family=FONT, size=5, color=INK, va="center", ha="center")
    if not show_y:
        p = p + theme(axis_text_y=element_blank(), axis_ticks_major_y=element_blank())
    return p

def _setup_summary_layers(d: pd.DataFrame, y: str = "cost_pp"):
    """Panel (b): one point per setup (median gain and cost over its models) with interquartile error bars in both
    directions, over the individual models as faint small points (matches the boxplots in (a) and (c))."""
    from plotnine import aes, geom_point, geom_segment
    q = d.groupby("Setup", observed=True).agg(
        gain=("gain_pp", "median"), g25=("gain_pp", lambda v: v.quantile(.25)), g75=("gain_pp", lambda v: v.quantile(.75)),
        cost=(y, "median"), c25=(y, lambda v: v.quantile(.25)), c75=(y, lambda v: v.quantile(.75)),
    ).reset_index()
    return [geom_point(aes(shape="Setup", fill="Setup"), color="none", size=0.8, alpha=0.3),
            geom_segment(aes(x="g25", xend="g75", y="cost", yend="cost", color="Setup"), data=q, size=0.7),
            geom_segment(aes(x="gain", xend="gain", y="c25", yend="c75", color="Setup"), data=q, size=0.7),
            geom_point(aes("gain", "cost", shape="Setup", fill="Setup"), data=q, color=INK, size=2.0, stroke=0.4)]

def _panels(df: pd.DataFrame):
    """Figure 3 panels for every row of df: (a) overall accuracy, (b) condition level, (c) item level. Rows whose
    item agreement is not estimable are left out of (c); returns (panels, number left out)."""
    from plotnine import aes, ggplot, labs
    d = _prep(df)
    R = _refs(df)
    est = d[np.isfinite(d.r)]
    pa = _strip(d, "acc_pct", R, "acc", "(a) Overall accuracy", "Accuracy (%)", show_y=True)
    pb = (ggplot(d, aes("gain_pp", "od_pp")) + _ref_layers_b(R, HUMAN_BAND, HUMAN_BAND_ALPHA, y="od")
          + [_star_b(R, hollow=True, y="od")] + _setup_summary_layers(d, y="od_pp")
          + _scales() + labs(title="(b) Condition level", **LAB_B) + _theme())
    pc = _strip(est, "r", R, "r", "(c) Item level", "Correlation on item difficulty (r)", show_y=False)
    return (pa, pb, pc), len(d) - len(est)


def plot_main(df: pd.DataFrame, out: Path, name: str):
    """Figure 3: one panel per level, one point per configuration in df."""
    from plotnine import theme
    (a, b, c), n_drop = _panels(df)
    fig = ((a | b | c) & theme(figure_size=(TWO_COL, 2.3), plot_margin_bottom=0.06)).draw()
    _legend(fig, list(SETUPS))
    _save(fig, out, name, tight=True)
    return n_drop


def cell_rects(ax, m: np.ndarray, cmap, vmin: float, vmax: float):
    """Draw a matrix as vector rectangles (imshow embeds a tiny raster that PDF viewers blur when scaling), laid out
    like imshow: cell (a, b) centred at x = b, y = a, first row on top, square cells."""
    from matplotlib.patches import Rectangle
    for (a, b), val in np.ndenumerate(m):
        ax.add_patch(Rectangle((b - 0.5, a - 0.5), 1, 1, facecolor=cmap((val - vmin) / (vmax - vmin)), edgecolor="none",
                               linewidth=0))
    ax.set_xlim(-0.5, m.shape[1] - 0.5)
    ax.set_ylim(m.shape[0] - 0.5, -0.5)
    ax.set_aspect("equal")
