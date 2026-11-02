# Mirelons

Data and analysis code for *Analyzing Repetition and Interference Effects in Memory-Constrained User Simulators*
(Leong, Tomlin and Linzen, 2026; [arXiv:2610.24232](https://arxiv.org/abs/2610.24232)).

```
data/        passages and their audio, questions, survey, listener responses, model runs   (see data/SCHEMA.md)
analysis/    code
results/     levels/  model-vs-listener scores for every configuration
             figures/ paper Figures 2-9
             tables/  paper Tables 1-3
```

## Setup

Requires [uv](https://docs.astral.sh/uv/). From repo root:

```bash
uv sync
```
## Reproducing the paper

**1. Listener table**. Builds `data/human/longdata_strict.csv` from the raw export and checks the
listener statistics (accuracy, condition effects, hit and false-endorsement rates, split-half reliability) against their reported values.

```bash
uv run python analysis/build_longdata.py
uv run python analysis/levels_analysis.py check
```

**2. Score every model configuration against humans** → `results/levels/levels.csv`. About 20–30 s per
configuration (578 configurations, ~4 h on one core). `levels_qc.csv` records the inclusion checks for every run.

```bash
uv run python analysis/levels_analysis.py qc
uv run python analysis/levels_analysis.py run
```

To spread it over a SLURM cluster: `uv run python analysis/levels_analysis.py plan` writes `todo.json`,
`analysis/slurm/submit_levels.sh` scores it in shards, and `uv run python analysis/levels_analysis.py merge` combines them.

**3. All figures and tables** → `results/figures/`, `results/tables/`.

```bash
uv run python analysis/paper.py
```

| Output | Paper |
|---|---|
| `figure2_human_accuracy.pdf` | Figure 2: human accuracy by version and by question |
| `figure3_three_levels.pdf` | Figure 3: every configuration at the three levels, by setup |
| `figure4_endorsement.pdf` | Figure 4: statement endorsement, humans vs two configurations |
| `figure5_human_version_pairs.pdf` | Figure 5: question accuracy in every pair of versions |
| `figure6_human_topics.pdf` | Figure 6: human accuracy by topic |
| `figure7_item_agreement_by_model.pdf` | Figure 7: item agreement by model and setup |
| `figure8_three_levels_by_family.pdf` | Figure 8: the three levels by model family |
| `figure9_model_size.pdf` | Figure 9: the three levels against Qwen model size |
| `table1_passage_length.csv` | Table 1: passage length in words and seconds of audio |
| `table2_human_by_true_statements.csv` | Table 2: human accuracy by number of true statements |
| `table3_sampling.csv` | Table 3: sampling settings per model and thinking mode |

## Code

| File | What |
|---|---|
| `analysis/paths.py`, `design.py` | data locations; topics, versions and answer keys |
| `analysis/build_longdata.py`, `data_prep.py` | human data (`longdata_strict.csv`) from the Qualtrics export |
| `analysis/human_ingest.py` | option-level human responses from the Qualtrics export |
| `analysis/levels_core.py` | loaders, counts, statistics, split-half and bootstrap machinery |
| `analysis/levels_analysis.py` | `check`, `qc`, `run` / `plan` / `merge`: scoring every configuration |
| `analysis/figure_data.py` | `levels.csv` → setups, hyperparameters and human reference values |
| `analysis/fig_*.py`, `tables.py`, `plotting.py` | figures, tables and shared style |
| `analysis/paper.py` | builds every figure and table |
| `analysis/tests/` | `uv run pytest` |

## Licenses

Code: MIT (`LICENSE`). Data: CC BY 4.0 (`DATA_LICENSE`). Fonts in `analysis/fonts/`: SIL Open Font License.
