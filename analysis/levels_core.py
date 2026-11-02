"""Shared listener/model code for the three-level comparison (paper Appendix D.1).

One estimand for listeners and models, computed by the same code from the same count tensors:

  K[T,L,Q]    exact-match correct count per (topic, version, question)
  N[T,L]      responses per (topic, version)
  E[T,L,Q,O]  endorsement count per option (five options; option 5 is "None of the above")

Topic mean = K.sum(Q) / (Q N); version mean = mean of the four topic means; overall = mean of the four version
means. A response unparsed for a question counts as wrong with no option endorsed.

Groups are weight vectors over *units*: a listener (four records, one per topic) or one model sample (one
record). A weight matrix W[S,U] gives S groups at once, so splits and bootstrap replicates are vectorised.

The two-group comparison: in each split, listeners are halved within each of the 24 Latin-square
groups (A, B); the model enters as a third group of the same size, M = a subsample of its samples matched per
cell to |A_cell|; d = S(M,B) - S(A,B) for gap statistics, and the same for within-group statistics (tau).
Point = mean of d over splits; CI = percentile bootstrap of the split-averaged d, each replicate resampling
listeners (stratified by Latin-square group) and model samples (within cell), questions for item statistics.
"""
from __future__ import annotations

import csv
import gzip
import json
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from design import HUMAN_TOPIC, LEVELS, TOPICS, load_bank  # noqa: F401  (load_bank re-exported)

NT, NL, NQ, NO = len(TOPICS), len(LEVELS), 5, 5
NOTA = 5
LEVEL_LABEL = {"control": "SayOnce", "repeat_short": "SayTwice", "repeat_long": "SayThrice", "distractor": "Interfere"}
TAU_MISFIT = 0.4        # "uniform" needs the model's tau upper CI below this
NOT_ESTIMABLE_REL = 0.5  # model item reliability below this -> "not estimable"


# ---------------------------------------------------------------- question bank
def truth_tensor(bank: dict) -> np.ndarray:
    """(T,Q,O) bool: option o+1 is in the key of question q."""
    tr = np.zeros((NT, NQ, NO), bool)
    for t, topic in enumerate(TOPICS):
        for q, ans in enumerate(bank[topic]["answers"]):
            for a in ans:
                tr[t, q, a - 1] = True
    return tr


# ---------------------------------------------------------------- populations
@dataclass
class Pop:
    """Response records. t, l: (R,) topic/version index; corr: (R,Q); end: (R,Q,O); unit: (R,) unit index;
    strata: (U,) stratum per unit (Latin-square group for listeners, cell t*NL+l for model samples)."""
    name: str
    t: np.ndarray
    l: np.ndarray
    corr: np.ndarray
    end: np.ndarray
    unit: np.ndarray
    strata: np.ndarray
    meta: dict = field(default_factory=dict)

    @property
    def U(self) -> int:
        return len(self.strata)

    @property
    def cell(self) -> np.ndarray:
        return self.t * NL + self.l

    def subset_units(self, keep: np.ndarray, name: str | None = None) -> "Pop":
        """Population restricted to units with keep[u] True (re-indexed)."""
        new_id = -np.ones(self.U, int)
        new_id[keep] = np.arange(keep.sum())
        r = keep[self.unit]
        return Pop(name or self.name, self.t[r], self.l[r], self.corr[r], self.end[r], new_id[self.unit[r]],
                   self.strata[keep], dict(self.meta))


def load_humans(csv_path: Path, bank: dict) -> Pop:
    """Listeners: exact-match correctness and Latin-square group from longdata_strict; option endorsements from
    the raw Qualtrics TSV via human_ingest. Asserts the two agree on every question."""
    rows = list(csv.DictReader(csv_path.open()))
    pids = sorted({r["pid"] for r in rows})
    pi = {p: i for i, p in enumerate(pids)}
    P = len(pids)
    corr = np.full((P, NT, NQ), np.nan)
    lev = np.full((P, NT), -1)
    group = np.zeros(P, int)
    for r in rows:
        topic = HUMAN_TOPIC[r["topic"]]
        t = TOPICS.index(topic)
        p = pi[r["pid"]]
        corr[p, t, bank[topic]["q_ids"].index(r["question_id"])] = float(r["correct"])
        lev[p, t] = LEVELS.index(r["condition"])
        group[p] = int(r["group"])
    assert not np.isnan(corr).any() and (lev >= 0).all(), "incomplete human grid"

    import human_ingest as ing
    end = np.full((P, NT, NQ, NO), np.nan)
    for r in ing.ingest_humans(ing.load_question_bank()):
        if r["respondent_id"] not in pi or not r["attn_pass_all"]:
            continue
        t = TOPICS.index(r["topic"])
        q = bank[r["topic"]]["q_ids"].index(r["question_id"])
        end[pi[r["respondent_id"]], t, q, r["option_n"] - 1] = float(r["endorsed"])
    assert not np.isnan(end).any(), "option table does not cover every listener x question"
    tr = truth_tensor(bank)
    exact = (end.astype(bool) == tr[None]).all(-1).astype(float)
    assert (exact == corr).all(), "option-level endorsements disagree with longdata_strict correctness"

    t_idx = np.tile(np.arange(NT), P)
    unit = np.repeat(np.arange(P), NT)
    return Pop("human", t_idx, lev.ravel(), corr.reshape(-1, NQ), end.reshape(-1, NQ, NO), unit, group,
               {"pids": pids})


def run_files(tasks_dir: Path) -> list[Path]:
    """Run files in one tasks/ directory: *_full_grid.jsonl, or *_full_grid.jsonl.gz for files committed gzipped
    (EXPANSION_RUNS.md: JSONL over 50 MB). A plain file wins over a gzipped copy of the same run."""
    plain = sorted(tasks_dir.glob("*_full_grid.jsonl"))
    gz = [p for p in sorted(tasks_dir.glob("*_full_grid.jsonl.gz")) if p.with_suffix("") not in plain]
    return plain + gz


def open_run(path: Path, mode: str = "t"):
    """Open a run file for reading, gunzipping *.jsonl.gz transparently. mode "t" (text) or "b" (bytes)."""
    if path.suffix == ".gz":
        return gzip.open(path, "r" + mode)
    return path.open("r" + mode)


def load_model_jsonl(path: Path, bank: dict, condition: str, name: str | None = None) -> Pop:
    """Model samples for one condition_id. Correctness rebuilt from parsed_answers (keys "1".."5" = content
    questions in bank order); asserted against metrics.exact_match_accuracy."""
    tr = truth_tensor(bank)
    ts, ls, corr, end = [], [], [], []
    mismatch = 0
    for line in open_run(path):
        if not line.strip():
            continue
        r = json.loads(line)
        if r.get("condition_id") != condition or r.get("topic_id") not in TOPICS or r.get("level") not in LEVELS:
            continue
        t = TOPICS.index(r["topic_id"])
        pa = r.get("parsed_answers") or {}
        e = np.zeros((NQ, NO))
        bad = np.zeros(NQ, bool)   # an option number outside 1..5 makes the question wrong (as the run's scorer does)
        for q in range(NQ):
            for a in pa.get(str(q + 1)) or []:
                if 1 <= int(a) <= NO:
                    e[q, int(a) - 1] = 1.0
                else:
                    bad[q] = True
        c = np.array([float(str(q + 1) in pa and not bad[q] and (e[q].astype(bool) == tr[t, q]).all())
                      for q in range(NQ)])
        m = (r.get("metrics") or {}).get("exact_match_accuracy")
        if m is not None and abs(c.mean() - m) > 1e-9:
            mismatch += 1
        ts.append(t)
        ls.append(LEVELS.index(r["level"]))
        corr.append(c)
        end.append(e)
    if not ts:
        raise ValueError(f"{path}: no rows for condition {condition}")
    t, l = np.array(ts), np.array(ls)
    R = len(ts)
    return Pop(name or f"{path.parent.parent.name}:{condition}", t, l, np.array(corr), np.array(end),
               np.arange(R), t * NL + l, {"path": str(path), "condition": condition, "metric_mismatch": mismatch})


# ---------------------------------------------------------------- counts and statistics
def _design(pop: Pop) -> np.ndarray:
    """(U, C*(1+Q+Q*O)) per-unit sums of [cell indicator, cell x correct, cell x endorsed], cached on the Pop."""
    if "_design" not in pop.meta:
        R, C = len(pop.t), NT * NL
        cell = np.zeros((R, C))
        cell[np.arange(R), pop.cell] = 1.0
        rec = np.hstack([cell, (cell[:, :, None] * pop.corr[:, None, :]).reshape(R, -1),
                         (cell[:, :, None] * pop.end.reshape(R, 1, -1)).reshape(R, -1)])
        D = np.zeros((pop.U, rec.shape[1]))
        np.add.at(D, pop.unit, rec)
        pop.meta["_design"] = D
    return pop.meta["_design"]


def counts(pop: Pop, W: np.ndarray):
    """W: (S,U) unit weights -> K (S,T,L,Q), N (S,T,L), E (S,T,L,Q,O)."""
    W = np.atleast_2d(W)
    C = NT * NL
    X = W @ _design(pop)
    N = X[:, :C].reshape(-1, NT, NL)
    K = X[:, C:C + C * NQ].reshape(-1, NT, NL, NQ)
    E = X[:, C + C * NQ:].reshape(-1, NT, NL, NQ, NO)
    return K, N, E


def version_means(K, N) -> np.ndarray:
    """(S,L): mean over topics of the topic x version accuracy."""
    with np.errstate(invalid="ignore", divide="ignore"):
        tl = K.sum(-1) / (NQ * N)
    return np.nanmean(tl, axis=1)


def contrasts(vm: np.ndarray) -> dict:
    """gain (repetition) G = SayTwice - SayOnce; cost (interference) C = SayOnce - Interfere;
    plateau P = SayThrice - SayTwice."""
    return {"gain": vm[:, 1] - vm[:, 0], "cost": vm[:, 0] - vm[:, 3], "plateau": vm[:, 2] - vm[:, 1]}


def option_rates(E, N, truth: np.ndarray, include_nota: bool = False):
    """(S,L) hit rate (endorsed true options / true options) and false-endorsement rate (endorsed false options /
    false options), each a mean over topics of the topic x version rate. Option 5 ("None of the above") is
    dropped by default: that reproduces the documented listener hit rates (64% -> 73-75%)."""
    tr = truth.copy()
    mask = np.ones((NT, NQ, NO), bool)
    if not include_nota:
        mask[:, :, NOTA - 1] = False
    tm, fm = tr & mask, (~tr) & mask
    with np.errstate(invalid="ignore", divide="ignore"):
        hit = np.einsum("stlqo,tqo->stl", E, tm) / (N * tm.sum((1, 2))[None, :, None])
        fe = np.einsum("stlqo,tqo->stl", E, fm) / (N * fm.sum((1, 2))[None, :, None])
    return np.nanmean(hit, 1), np.nanmean(fe, 1)


def item_target(K, N) -> np.ndarray:
    """(S,T,Q): empirical logits log((k+.5)/(n-k+.5)) per (topic, version, question), centred within topic x
    version, averaged over versions (20 values)."""
    Nq = N[..., None]
    y = np.log((K + 0.5) / (Nq - K + 0.5))
    yc = y - y.mean(-1, keepdims=True)
    return yc.mean(2)


def tau_moment(K, N) -> np.ndarray:
    """(S,) moment estimate of tau = SD of question x version effects (logits), within topic: double-centre the
    (version, question) table of empirical logits in each topic and subtract the expected sampling variance.
    Fast stand-in for the GLMM's (1|question:version) SD; cross-checked with glmm_tau_laplace."""
    Nq = N[..., None]
    y = np.log((K + 0.5) / (Nq - K + 0.5))                      # S,T,L,Q
    v = 1 / (K + 0.5) + 1 / (Nq - K + 0.5)
    r = y - y.mean(-1, keepdims=True) - y.mean(-2, keepdims=True) + y.mean((-1, -2), keepdims=True)
    df = NT * (NL - 1) * (NQ - 1)
    noise = ((NL - 1) * (NQ - 1) / (NL * NQ)) * v.sum((1, 2, 3))
    t2 = ((r ** 2).sum((1, 2, 3)) - noise) / df
    return np.sqrt(np.clip(t2, 0, None))


def pearson_rows(X: np.ndarray, Y: np.ndarray) -> np.ndarray:
    X = X - X.mean(-1, keepdims=True)
    Y = Y - Y.mean(-1, keepdims=True)
    den = np.sqrt((X ** 2).sum(-1) * (Y ** 2).sum(-1))
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(den > 0, (X * Y).sum(-1) / den, np.nan)


def summary_stats(K, N, E, truth) -> dict:
    """Per-group (S,) statistics used at every level."""
    vm = version_means(K, N)
    out = {"acc": vm.mean(1), **contrasts(vm)}
    for l, lev in enumerate(LEVELS):
        out[f"vm_{lev}"] = vm[:, l]
    hit, fe = option_rates(E, N, truth)
    out["d_hit_gain"] = hit[:, 1] - hit[:, 0]          # SayTwice - SayOnce
    out["d_fe_gain"] = fe[:, 1] - fe[:, 0]
    out["d_hit_cost"] = hit[:, 0] - hit[:, 3]          # SayOnce - Interfere: positive = hits lost under Interfere
    out["d_fe_cost"] = fe[:, 3] - fe[:, 0]             # Interfere - SayOnce: positive = more false endorsements
    for l, lev in enumerate(LEVELS):
        out[f"hit_{lev}"] = hit[:, l]
        out[f"fe_{lev}"] = fe[:, l]
    out["tau"] = tau_moment(K, N)
    return out


# Two-group statistics: name -> (kind, worse direction). "gap" = |X - B| of a per-group statistic, "corr" =
# Pearson of the 20-question target with B, "within" = within-group statistic compared X vs A (no B).
TWO_GROUP = {
    "acc": ("gap", +1),
    "gain": ("gap", +1),
    "cost": ("gap", +1),
    "plateau": ("gap", +1),
    "item_r": ("corr", -1),
    "tau": ("within", +1),
}


def two_group_stats(sX: dict, sB: dict, tX: np.ndarray, tB: np.ndarray) -> dict:
    out = {k: np.abs(sX[k] - sB[k]) for k in ("acc", "gain", "cost", "plateau")}
    out["acc_signed"] = sX["acc"] - sB["acc"]
    for k in ("gain", "cost", "plateau"):
        out[f"{k}_signed"] = sX[k] - sB[k]
    out["item_r"] = pearson_rows(tX.reshape(len(tX), -1), tB.reshape(len(tB), -1))
    out["tau"] = sX["tau"]
    return out


# ---------------------------------------------------------------- resampling
def _accumulate(S: int, U: int, rows: np.ndarray, cols: np.ndarray) -> np.ndarray:
    """(S,U) counts of (row, col) pairs (fast replacement for np.add.at)."""
    return np.bincount((rows * U + cols).ravel(), minlength=S * U).reshape(S, U).astype(float)


def _halve_draws(draw: np.ndarray, rng):
    """draw: (S,n) unit indices (one row per split). Random half of each row's entries -> (A, B) index arrays of
    (row, unit). Odd n gives the extra draw to A or B at random."""
    S, n = draw.shape
    perm = rng.random((S, n)).argsort(1)
    d = np.take_along_axis(draw, perm, 1)
    cut = n // 2 + ((n % 2) * (rng.random(S) < 0.5))
    inA = np.arange(n)[None, :] < cut[:, None]
    rows = np.broadcast_to(np.arange(S)[:, None], (S, n))
    return (rows[inA], d[inA]), (rows[~inA], d[~inA])


def stratified_counts(strata: np.ndarray, S: int, rng) -> np.ndarray:
    """(S,U) multiplicities: units resampled with replacement within each stratum (bootstrap)."""
    rows, cols = [], []
    for g in np.unique(strata):
        idx = np.flatnonzero(strata == g)
        draw = idx[rng.integers(0, len(idx), size=(S, len(idx)))]
        rows.append(np.broadcast_to(np.arange(S)[:, None], draw.shape).ravel())
        cols.append(draw.ravel())
    return _accumulate(S, len(strata), np.concatenate(rows), np.concatenate(cols))


def halve(strata: np.ndarray, mult: np.ndarray, rng):
    """Split units present (mult > 0) into halves within each stratum; a unit keeps its multiplicity on one side.
    Odd strata give the extra unit to A or B at random. Returns (WA, WB) (S,U)."""
    S, U = mult.shape
    inA = np.zeros((S, U), bool)
    for g in np.unique(strata):
        idx = np.flatnonzero(strata == g)
        present = mult[:, idx] > 0
        keys = np.where(present, rng.random(present.shape), np.inf)
        perm = keys.argsort(1)
        n = present.sum(1)
        cut = n // 2 + ((n % 2) * (rng.random(S) < 0.5))
        first = np.arange(len(idx))[None, :] < cut[:, None]
        rows = np.broadcast_to(np.arange(S)[:, None], perm.shape)
        inA[rows[first], idx[perm[first]]] = True
    WA = np.where(inA, mult, 0.0)
    return WA, np.where(~inA, mult, 0.0)


def model_pool(model: Pop, n_rep: int, n_inner: int, rng, resample: bool) -> list[np.ndarray]:
    """Per cell: (n_rep*n_inner, n_cell) unit indices — identity (point) or drawn with replacement within cell
    once per replicate and shared by its n_inner splits (bootstrap)."""
    pools = []
    for c in range(NT * NL):
        idx = np.flatnonzero(model.strata == c)
        if resample:
            pools.append(np.repeat(idx[rng.integers(0, len(idx), size=(n_rep, len(idx)))], n_inner, axis=0))
        else:
            pools.append(np.broadcast_to(idx, (n_rep * n_inner, len(idx))))
    return pools


def matched_subsample(model: Pop, pools: list[np.ndarray], size: np.ndarray, rng):
    """(S,U) weights: per cell, size[s,c] samples drawn without replacement from the pool (with replacement
    when the pool is smaller; counted in the returned shortfall)."""
    S = size.shape[0]
    short = 0
    rows_all, cols_all = [], []
    for c, pool in enumerate(pools):
        n = pool.shape[1]
        k = size[:, c].astype(int)
        perm = rng.random(pool.shape).argsort(1)
        pp = np.take_along_axis(pool, perm, 1)
        take = np.arange(n)[None, :] < np.minimum(k, n)[:, None]
        rows_all.append(np.broadcast_to(np.arange(S)[:, None], pool.shape)[take])
        cols_all.append(pp[take])
        extra = np.clip(k - n, 0, None)
        if extra.any():
            short += int((extra > 0).sum())
            for s_ in np.flatnonzero(extra):
                rows_all.append(np.full(extra[s_], s_))
                cols_all.append(pool[s_, rng.integers(0, n, extra[s_])])
    return _accumulate(S, model.U, np.concatenate(rows_all), np.concatenate(cols_all)), short


def boot_halves(strata: np.ndarray, n_rep: int, n_inner: int, rng):
    """n_rep bootstrap replicates x n_inner splits each (rows ordered replicate-major). Within each stratum the
    replicate draws n_g units with replacement (shared by its n_inner splits); each split halves the n_g
    *draws* (a listener drawn twice may land in both halves). By the bootstrap principle the draws are the
    replicate's units; keeping a listener's copies together would double the half-to-half variance
    (sum m^2 / (sum m)^2 ~ 2/n) and bias d. Returns (WA, WB) (n_rep*n_inner, U) multiplicities."""
    U, S = len(strata), n_rep * n_inner
    A, B = ([], []), ([], [])
    for g in np.unique(strata):
        idx = np.flatnonzero(strata == g)
        n = len(idx)
        draw = np.repeat(idx[rng.integers(0, n, size=(n_rep, n))], n_inner, axis=0)
        (ra, ca), (rb, cb) = _halve_draws(draw, rng)
        A[0].append(ra); A[1].append(ca); B[0].append(rb); B[1].append(cb)
    return (_accumulate(S, U, np.concatenate(A[0]), np.concatenate(A[1])),
            _accumulate(S, U, np.concatenate(B[0]), np.concatenate(B[1])))


def record_halves_pop(H: Pop) -> Pop:
    """Listener records as units, stratified by (Latin-square group, topic), for a record-level bar: halves are
    drawn per topic independently, so a listener's four records can fall in different halves. Removes the
    person-level correlation across a listener's records that independent model samples lack. The bootstrap
    still resamples whole listeners (boot_halves_records)."""
    R = len(H.t)
    assert np.array_equal(H.unit, np.repeat(np.arange(H.U), NT)) and np.array_equal(H.t, np.tile(np.arange(NT), H.U))
    meta = {k: v for k, v in H.meta.items() if not k.startswith("_")}
    meta.update(record_halves=True, listener_strata=H.strata)
    return Pop(H.name + ":records", H.t, H.l, H.corr, H.end, np.arange(R), H.strata[H.unit] * NT + H.t, meta)


def boot_halves_records(Hrec: Pop, n_rep: int, n_inner: int, rng):
    """Like boot_halves for a record_halves_pop: each replicate draws whole listeners within Latin-square group
    (shared by its n_inner splits); each split halves the drawn listeners' records per topic independently."""
    ls = Hrec.meta["listener_strata"]
    S, R = n_rep * n_inner, len(Hrec.t)
    A, B = ([], []), ([], [])
    for g in np.unique(ls):
        idx = np.flatnonzero(ls == g)
        n = len(idx)
        draw = np.repeat(idx[rng.integers(0, n, size=(n_rep, n))], n_inner, axis=0)
        for t in range(NT):
            (ra, ca), (rb, cb) = _halve_draws(draw * NT + t, rng)
            A[0].append(ra); A[1].append(ca); B[0].append(rb); B[1].append(cb)
    return (_accumulate(S, R, np.concatenate(A[0]), np.concatenate(A[1])),
            _accumulate(S, R, np.concatenate(B[0]), np.concatenate(B[1])))


def split_batch(H: Pop, M: Pop, truth, n_rep: int, n_inner: int, rng, boot: bool, qidx: np.ndarray | None = None):
    """n_rep x n_inner splits (rows replicate-major); with boot, each replicate's resample of listeners and
    model samples is shared by its n_inner splits. Returns per-statistic arrays for A-vs-B and M-vs-B, plus the
    matched-size shortfall count."""
    S = n_rep * n_inner
    if not boot:
        WA, WB = halve(H.strata, np.ones((S, H.U)), rng)
    elif H.meta.get("record_halves"):
        WA, WB = boot_halves_records(H, n_rep, n_inner, rng)
    else:
        WA, WB = boot_halves(H.strata, n_rep, n_inner, rng)
    KA, NA, EA = counts(H, WA)
    KB, NB, EB = counts(H, WB)
    pools = model_pool(M, n_rep, n_inner, rng, resample=boot)
    WM, short = matched_subsample(M, pools, NA.reshape(S, -1), rng)
    KM, NM, EM = counts(M, WM)
    sA, sB, sM = (summary_stats(k, n, e, truth) for k, n, e in ((KA, NA, EA), (KB, NB, EB), (KM, NM, EM)))
    tA, tB, tM = item_target(KA, NA), item_target(KB, NB), item_target(KM, NM)
    if qidx is not None:   # question resample within topic (item statistics)
        ar = np.arange(NT)[None, :, None]
        tA, tB, tM = (x[np.arange(S)[:, None, None], ar, qidx] for x in (tA, tB, tM))
    return two_group_stats(sA, sB, tA, tB), two_group_stats(sM, sB, tM, tB), short


def _verdict(d_lo: float, d_hi: float, worse: int) -> str:
    """Average-to-average decision: CI of d excludes 0 in the worse direction -> 'further';
    otherwise 'as close' (an exclusion in the better direction is still 'as close', never 'closer')."""
    if np.isnan(d_lo) or np.isnan(d_hi):
        return "not estimable"
    if (worse > 0 and d_lo > 0) or (worse < 0 and d_hi < 0):
        return "further"
    return "as close"


def compare(H: Pop, M: Pop, truth, n_splits: int = 2000, n_boot: int = 1000, n_inner: int = 20, seed: int = 0,
            batch: int = 500) -> dict:
    """Two-group comparison for every statistic in TWO_GROUP. Point: mean d over n_splits splits of the observed
    data. CI: 2.5/97.5 percentiles over n_boot replicates of the mean d over n_inner splits. Also returns the
    listener-half reference distribution (A vs B) for each statistic."""
    rng = np.random.default_rng(seed)
    ab, mb = {}, {}
    short = 0
    done = 0
    while done < n_splits:
        s = min(batch, n_splits - done)
        a, m, sh = split_batch(H, M, truth, 1, s, rng, boot=False)
        for k in a:
            ab.setdefault(k, []).append(a[k])
            mb.setdefault(k, []).append(m[k])
        short += sh
        done += s
    ab = {k: np.concatenate(v) for k, v in ab.items()}
    mb = {k: np.concatenate(v) for k, v in mb.items()}

    boot_d = {k: np.zeros(n_boot) for k in TWO_GROUP}
    boot_d.update({f"{k}_signed": np.zeros(n_boot) for k in ("acc", "gain", "cost", "plateau")})
    boot_m = {k: np.zeros(n_boot) for k in boot_d}   # model-side statistic per replicate (CI of e.g. tau(M))
    per = max(1, batch // n_inner)
    b = 0
    while b < n_boot:
        nb = min(per, n_boot - b)
        S = nb * n_inner
        qidx = np.repeat(rng.integers(0, NQ, size=(nb, NT, NQ)), n_inner, axis=0)
        a, m, sh = split_batch(H, M, truth, nb, n_inner, rng, boot=True, qidx=qidx)
        short += sh
        for k in boot_d:
            d = (m[k] - a[k]).reshape(nb, n_inner)
            boot_d[k][b:b + nb] = np.nanmean(d, 1)
            boot_m[k][b:b + nb] = np.nanmean(m[k].reshape(nb, n_inner), 1)
        b += nb

    res = {}
    for k in boot_d:
        d = mb[k] - ab[k]
        lo, hi = np.nanpercentile(boot_d[k], [2.5, 97.5])
        row = {"d": float(np.nanmean(d)), "d_lo": float(lo), "d_hi": float(hi),
               "ref_mean": float(np.nanmean(ab[k])), "ref_median": float(np.nanmedian(ab[k])),
               "ref_p05": float(np.nanpercentile(ab[k], 5)), "ref_p95": float(np.nanpercentile(ab[k], 95)),
               "model_mean": float(np.nanmean(mb[k])),
               "model_lo": float(np.nanpercentile(boot_m[k], 2.5)), "model_hi": float(np.nanpercentile(boot_m[k], 97.5)),
               "p_boot": float(min(1.0, 2 * min(np.mean(boot_d[k] <= 0), np.mean(boot_d[k] >= 0))))}
        if k in TWO_GROUP:
            row["verdict"] = _verdict(lo, hi, TWO_GROUP[k][1])
        res[k] = row
    res["_meta"] = {"n_splits": n_splits, "n_boot": n_boot, "n_inner": n_inner, "seed": seed,
                    "matched_size_shortfall": short}
    return res


# ---------------------------------------------------------------- one population on its own
def own_bootstrap(pop: Pop, truth, n_boot: int, seed: int) -> dict:
    """Full-sample point estimates and percentile CIs of every summary statistic (listeners: stratified by
    Latin-square group; model: within cell)."""
    rng = np.random.default_rng(seed)
    point = summary_stats(*counts(pop, np.ones((1, pop.U))), truth)
    boots = []
    for b0 in range(0, n_boot, 500):
        nb = min(500, n_boot - b0)
        boots.append(summary_stats(*counts(pop, stratified_counts(pop.strata, nb, rng)), truth))
    out = {}
    for k in point:
        v = np.concatenate([x[k] for x in boots])
        lo, hi = np.nanpercentile(v, [2.5, 97.5])
        out[k] = {"est": float(point[k][0]), "lo": float(lo), "hi": float(hi)}
    return out


def direction(est: dict, human_sign: int) -> str:
    """Model's own effect vs listeners' sign: 'same' / 'reversed' (CI excludes 0) or 'null'."""
    if est["lo"] > 0:
        return "same" if human_sign > 0 else "reversed"
    if est["hi"] < 0:
        return "same" if human_sign < 0 else "reversed"
    return "null"


def item_reliability(pop: Pop, n_splits: int, seed: int) -> dict:
    """Split-half Pearson of the 20-question target within one population (stratified halves), its median and
    5th pct, and the Spearman-Brown full-sample value."""
    rng = np.random.default_rng(seed)
    WA, WB = halve(pop.strata, np.ones((n_splits, pop.U)), rng)
    r = pearson_rows(item_target(*counts(pop, WA)[:2]).reshape(n_splits, -1),
                     item_target(*counts(pop, WB)[:2]).reshape(n_splits, -1))
    med = float(np.nanmedian(r)) if np.isfinite(r).any() else float("nan")
    return {"split_half": med, "p05": float(np.nanpercentile(r, 5)) if np.isfinite(r).any() else float("nan"),
            "sb": 2 * med / (1 + med) if np.isfinite(med) else float("nan")}


def holm(p: dict) -> dict:
    """Holm-adjusted p-values."""
    ks = sorted(p, key=p.get)
    out, run = {}, 0.0
    for i, k in enumerate(ks):
        run = max(run, min(1.0, (len(ks) - i) * p[k]))
        out[k] = run
    return out


# ---------------------------------------------------------------- GLMM cross-check for tau
def glmm_tau_laplace(K: np.ndarray, N: np.ndarray) -> dict:
    """Aggregated-binomial GLMM cbind(k, n-k) ~ topic*version + (1|question) + (1|question:version), fitted by
    a Laplace approximation with fixed and random effects optimised jointly given the variance parameters
    (lme4's nAGQ = 0 scheme). K: (T,L,Q), N: (T,L). Used to check tau_moment on the full data; too slow for
    the split/bootstrap loops."""
    from scipy.optimize import minimize

    k = K.ravel()
    n = np.repeat(N.ravel(), NQ)
    T, L, Q = np.meshgrid(np.arange(NT), np.arange(NL), np.arange(NQ), indexing="ij")
    T, L, Q = T.ravel(), L.ravel(), Q.ravel()
    nobs = len(k)
    X = np.zeros((nobs, NT * NL))
    X[np.arange(nobs), T * NL + L] = 1.0                          # saturated topic*version
    qid = T * NQ + Q                                              # 20 questions
    Zq = np.zeros((nobs, NT * NQ)); Zq[np.arange(nobs), qid] = 1.0
    Zqv = np.zeros((nobs, nobs)); Zqv[np.arange(nobs), np.arange(nobs)] = 1.0   # question:version = one per obs
    Z = np.hstack([Zq, Zqv])
    nq = Zq.shape[1]

    def inner(theta):
        sq, sv = np.exp(theta)
        lam = np.concatenate([np.full(nq, sq), np.full(nobs, sv)])
        A = np.hstack([X, Z * lam])                               # spherical random effects u = b / lam
        coef = np.zeros(A.shape[1])
        pen = np.concatenate([np.zeros(X.shape[1]), np.ones(Z.shape[1])])
        for _ in range(100):
            eta = A @ coef
            mu = 1 / (1 + np.exp(-eta))
            w = n * mu * (1 - mu) + 1e-12
            grad = A.T @ (k - n * mu) - pen * coef
            H = A.T @ (A * w[:, None]) + np.diag(pen)
            step = np.linalg.solve(H, grad)
            coef = coef + step
            if np.abs(step).max() < 1e-9:
                break
        eta = A @ coef
        mu = 1 / (1 + np.exp(-eta))
        u = coef[X.shape[1]:]
        ll = np.sum(k * eta - n * np.log1p(np.exp(eta)))
        w = n * mu * (1 - mu)
        Zl = Z * lam
        _, logdet = np.linalg.slogdet(np.eye(Z.shape[1]) + Zl.T @ (Zl * w[:, None]))
        return -2 * ll + u @ u + logdet

    best = min((minimize(inner, x0, method="Nelder-Mead", options={"xatol": 1e-4, "fatol": 1e-6})
                for x0 in ([np.log(0.8), np.log(0.2)], [np.log(0.8), np.log(0.02)])), key=lambda r: r.fun)
    sq, sv = np.exp(best.x)
    return {"sd_question": float(sq), "tau": float(sv), "deviance_laplace": float(best.fun)}


# ---------------------------------------------------------------- distribution-level humanlikeness (1 - W1)
SCORES = np.arange(NQ + 1) / NQ   # per-passage exact-match share: 0, .2, ..., 1


def version_score_hist(pop: Pop, w: np.ndarray | None = None) -> np.ndarray:
    """(L, 6) distribution of per-passage scores in each version, pooled over topics (record weights w)."""
    w = np.ones(len(pop.t)) if w is None else w
    k = pop.corr.sum(1).astype(int)
    h = np.zeros((NL, NQ + 1))
    np.add.at(h, (pop.l, k), w)
    return h / h.sum(1, keepdims=True)


def humanlikeness_w1(hm: np.ndarray, hh: np.ndarray) -> float:
    """1 - mean over versions of the Wasserstein-1 distance between two (L, 6) score distributions (score units)."""
    w1 = np.abs(np.cumsum(hm, 1) - np.cumsum(hh, 1))[:, :-1].sum(1) * (1 / NQ)
    return float(1 - w1.mean())
