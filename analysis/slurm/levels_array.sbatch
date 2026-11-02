#!/bin/bash
# One shard of the three-level scoring (levels_analysis.py run --todo ... --shard i/N). CPU only.
# Submitted as an array by submit_levels.sh, which sets --account / --array / --output and exports:
#   VENV (the repo's .venv from `uv sync`), REPO (code checkout), RUNS_ROOT (data/models copy),
#   OUT_DIR (holds todo.json; parts/ is written there), N_SHARDS, EXTRA_ARGS (optional, e.g. --n-boot 2000)
#SBATCH --job-name=levels
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --mem=6G
#SBATCH --time=01:30:00
set -euo pipefail
: "${VENV:?VENV not set}" "${REPO:?REPO not set}" "${RUNS_ROOT:?RUNS_ROOT not set}" "${OUT_DIR:?OUT_DIR not set}"
: "${N_SHARDS:?N_SHARDS not set}"

export OMP_NUM_THREADS="${SLURM_CPUS_PER_TASK:-1}" OPENBLAS_NUM_THREADS="${SLURM_CPUS_PER_TASK:-1}"
export MKL_NUM_THREADS="${SLURM_CPUS_PER_TASK:-1}" PYTHONNOUSERSITE=True PYTHONDONTWRITEBYTECODE=1

cd "$REPO"
echo "shard ${SLURM_ARRAY_TASK_ID}/${N_SHARDS} on $(hostname) at $(date -Is)"
"$VENV/bin/python" analysis/levels_analysis.py run \
    --todo "$OUT_DIR/todo.json" --shard "${SLURM_ARRAY_TASK_ID}/${N_SHARDS}" \
    --runs-root "$RUNS_ROOT" --out-dir "$OUT_DIR" ${EXTRA_ARGS:-}
echo "JOB_DONE $(date -Is)"
