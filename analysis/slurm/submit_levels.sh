#!/bin/bash
# Submit the three-level scoring as a SLURM CPU array, plus a merge job that runs after it.
# Run on the cluster login node with a todo.json from `levels_analysis plan` already in OUT_DIR, and:
#   SLURM_ACCOUNTS="acct_a acct_b"   accounts to choose from (space-separated)
#   VENV      the repo's .venv from `uv sync`      REPO      code checkout used by the jobs
#   RUNS_ROOT copy of data/models that todo.json paths are relative to
#   OUT_DIR   folder with todo.json (parts/ and levels.csv are written there)
#   LOG_DIR   SLURM logs
#   PER_SHARD configurations per array task (default 10)      EXTRA_ARGS extra levels_analysis run args
#
#   ./analysis/slurm/submit_levels.sh            # validate only (--test-only)
#   SUBMIT=1 ./analysis/slurm/submit_levels.sh   # submit
#
# Account = whichever of SLURM_ACCOUNTS has the earliest `sbatch --test-only` start estimate.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
: "${SLURM_ACCOUNTS:?SLURM_ACCOUNTS not set}" "${VENV:?VENV not set}" "${REPO:?REPO not set}"
: "${RUNS_ROOT:?RUNS_ROOT not set}" "${OUT_DIR:?OUT_DIR not set}" "${LOG_DIR:?LOG_DIR not set}"
SUBMIT="${SUBMIT:-0}"
PER_SHARD="${PER_SHARD:-10}"
mkdir -p "$LOG_DIR" "$OUT_DIR/parts"

N_ITEMS=$("$VENV/bin/python" -c "import json,sys; print(json.load(open(sys.argv[1]))['n_items'])" "$OUT_DIR/todo.json")
if [ "$N_ITEMS" -eq 0 ]; then echo "todo.json has no items"; exit 0; fi
N_SHARDS=$(( (N_ITEMS + PER_SHARD - 1) / PER_SHARD ))
export VENV REPO RUNS_ROOT OUT_DIR N_SHARDS EXTRA_ARGS="${EXTRA_ARGS:-}"
echo "$N_ITEMS configurations -> $N_SHARDS shards of <= $PER_SHARD"

read -r -a ACCOUNTS <<<"$SLURM_ACCOUNTS"
best="" best_t=""
for a in "${ACCOUNTS[@]}"; do
    t=$(sbatch --test-only --account="$a" --array="0-$((N_SHARDS - 1))" --export=ALL \
        --output=/dev/null "$HERE/levels_array.sbatch" 2>&1 | grep -oE 'start at [0-9T:-]+' | awk '{print $3}' || true)
    echo "  $a: est. start ${t:-unknown}"
    if [ -n "$t" ] && { [ -z "$best_t" ] || [[ "$t" < "$best_t" ]]; }; then best="$a" best_t="$t"; fi
done
ACCOUNT="${best:-${ACCOUNTS[0]}}"
echo "account: $ACCOUNT"

[ "$SUBMIT" = 1 ] || { echo "validate only; SUBMIT=1 to submit"; exit 0; }
ARRAY=$(sbatch --parsable --account="$ACCOUNT" --array="0-$((N_SHARDS - 1))" --export=ALL \
    --output="$LOG_DIR/%x_%A_%a.out" --error="$LOG_DIR/%x_%A_%a.err" "$HERE/levels_array.sbatch")
MERGE=$(sbatch --parsable --account="$ACCOUNT" --dependency="afterany:$ARRAY" --job-name=levels-merge \
    --cpus-per-task=1 --mem=4G --time=00:20:00 --export=ALL \
    --output="$LOG_DIR/%x_%j.out" --error="$LOG_DIR/%x_%j.err" \
    --wrap="cd '$REPO' && PYTHONDONTWRITEBYTECODE=1 '$VENV/bin/python' analysis/levels_analysis.py merge --out-dir '$OUT_DIR'")
echo "array $ARRAY ($N_SHARDS tasks), merge $MERGE (after array)"
