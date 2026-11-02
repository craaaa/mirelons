"""Repository paths. Every script reads inputs from data/ and writes outputs to results/ through these names."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DATA = ROOT / "data"
STIMULI = DATA / "stimuli"                      # <topic>/questions.yaml, <topic>/texts/*.md, option_labels.yaml
HUMAN_TSV = DATA / "human" / "results.tsv"      # raw Qualtrics export (UTF-16, pseudonymized)
HUMAN_CSV = DATA / "human" / "longdata_strict.csv"   # built from HUMAN_TSV by analysis/build_longdata.py
RUNS = DATA / "models"                          # <model_slug>/<profile>/<task>/tasks/*_full_grid.jsonl[.gz]

RESULTS = ROOT / "results"
LEVELS = RESULTS / "levels"                     # levels.csv, levels_human_reference.json, levels_qc.csv
FIGURES = RESULTS / "figures"

FONTS = Path(__file__).resolve().parent / "fonts"    # Source Sans Pro (paper font)
