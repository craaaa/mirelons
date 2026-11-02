"""Make every figure and table in the paper from data/ and results/levels/.

    python analysis/paper.py            # -> results/figures/figure{2..9}_*.pdf, results/tables/table{1..3}_*.csv

Needs results/levels/levels.csv (python analysis/levels_analysis.py run). Figure 1 is a hand-made diagram and is
not generated here. Takes under a minute.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib

import fig_endorsement
import fig_human
import fig_item_agreement
import fig_levels
import figure_data
import plotting
import tables
from paths import FIGURES, FONTS, RESULTS


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out-dir", default=str(RESULTS))
    args = ap.parse_args(argv)
    figs, tabs = Path(args.out_dir) / FIGURES.name, Path(args.out_dir) / "tables"
    figs.mkdir(parents=True, exist_ok=True)
    matplotlib.rcParams["pdf.fonttype"] = 42
    plotting._register_fonts(str(FONTS))

    fig_human.figure2(figs, "figure2_human_accuracy")
    fig_human.figures5_6(figs, ("figure5_human_version_pairs", "figure6_human_topics"))
    print("Figures 2, 5, 6 (listeners)")

    df = figure_data.load_all()
    n_drop = fig_levels.figure3(df, figs, "figure3_three_levels")
    print(f"Figure 3: {len(df)} configurations ({n_drop} without an estimable item agreement)")
    fig_endorsement.figure4(figs, "figure4_endorsement")
    print("Figure 4")
    fig_item_agreement.figure7(df, figs, "figure7_item_agreement_by_model")
    print("Figure 7")
    fig_levels.figure8(df, figs, "figure8_three_levels_by_family")
    print("Figure 8")
    fig_levels.figure9(df, figs, "figure9_model_size")
    print("Figure 9")

    tables.write_tables(tabs)
    print(f"Tables 1-3 -> {tabs}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
