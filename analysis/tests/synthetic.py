"""Synthetic models for the tests: samples drawn from the listeners themselves (a perfect simulator) or with
planted differences, scored with the real pipeline."""
from __future__ import annotations

import numpy as np

import levels_core as lc


def uniform_shift_logits(K: np.ndarray, N: np.ndarray) -> np.ndarray:
    """(T,L,Q) fitted logits of the uniform-shift model logit p = question + version within each topic
    (binomial GLM, Newton), i.e. a truth with item x version variance exactly 0."""
    out = np.zeros((lc.NT, lc.NL, lc.NQ))
    for t in range(lc.NT):
        L, Q = np.meshgrid(np.arange(lc.NL), np.arange(lc.NQ), indexing="ij")
        X = np.zeros((lc.NL * lc.NQ, lc.NQ + lc.NL - 1))
        X[np.arange(len(X)), Q.ravel()] = 1.0
        for l in range(1, lc.NL):
            X[L.ravel() == l, lc.NQ + l - 1] = 1.0
        k, n = K[t].ravel(), np.repeat(N[t], lc.NQ)
        b = np.zeros(X.shape[1])
        for _ in range(50):
            mu = 1 / (1 + np.exp(-X @ b))
            step = np.linalg.solve(X.T @ (X * (n * mu * (1 - mu))[:, None]), X.T @ (k - n * mu))
            b += step
            if np.abs(step).max() < 1e-10:
                break
        out[t] = (X @ b).reshape(lc.NL, lc.NQ)
    return out

def synthetic(Hgen: lc.Pop, truth, kind: str, n: int, rng) -> lc.Pop:
    """n synthetic model samples per cell, built from the listeners in Hgen.

    Record-based kinds (perfect, acc_plus5, zero_cost, fe02) draw from a bootstrap pseudo-population of the
    listeners in each cell (the cell's records resampled with replacement once, then n draws from that). The
    extra resample stands in for the population sampling error a real simulator has relative to the 201
    listeners; drawing straight from the listener records would let the simulator share B's sample and pass too
    easily. zero_cost reuses SayOnce's pseudo-population for Interfere (true cost SayOnce - Interfere exactly 0).
    Parametric kinds (perfect_uniform, tau04) draw correctness from the uniform-shift fit to listeners (item x
    version SD exactly 0), plus N(0, 0.4) logit noise per (topic, version, question) for tau04; a wrong answer
    flips one non-NOTA option of the key. These test level 3b: the pseudo-population adds item x version noise."""
    ts, ls, corr, end = [], [], [], []
    K, N, _ = lc.counts(Hgen, np.ones((1, Hgen.U)))
    acc_rate = float(Hgen.corr.mean())
    eta = uniform_shift_logits(K[0], N[0]) if kind in ("perfect_uniform", "tau04") else None
    pseudo = {}
    for t in range(lc.NT):
        for l in range(lc.NL):
            ts += [t] * n
            ls += [l] * n
            if eta is not None:
                logit = eta[t, l] + (rng.normal(0, 0.4, lc.NQ) if kind == "tau04" else 0.0)
                c = (rng.random((n, lc.NQ)) < 1 / (1 + np.exp(-logit))).astype(float)
                e = np.broadcast_to(truth[t], (n, lc.NQ, lc.NO)).astype(float).copy()
                wrong = np.nonzero(c == 0)
                o = rng.integers(0, lc.NO - 1, len(wrong[0]))
                e[wrong[0], wrong[1], o] = 1 - e[wrong[0], wrong[1], o]
                corr.append(c)
                end.append(e)
                continue
            src = (t, 0 if (kind == "zero_cost" and l == 3) else l)     # Interfere copies SayOnce
            if src not in pseudo:
                pool = np.flatnonzero((Hgen.t == src[0]) & (Hgen.l == src[1]))
                pseudo[src] = pool[rng.integers(0, len(pool), len(pool))]
            pick = pseudo[src][rng.integers(0, len(pseudo[src]), n)]
            c, e = Hgen.corr[pick].copy(), Hgen.end[pick].copy()
            if kind == "acc_plus5":
                flip = (c == 0) & (rng.random(c.shape) < 0.05 / (1 - acc_rate))
                e[flip] = truth[t][np.nonzero(flip)[1]]
                c[flip] = 1.0
            elif kind == "fe02":
                false = ~truth[t][None].repeat(n, 0)
                false[:, :, lc.NOTA - 1] = False
                fe_rate = e[false].mean() if false.any() else 0
                drop = false & (e == 1) & (rng.random(e.shape) < max(0.0, 1 - 0.02 / max(fe_rate, 1e-9)))
                e[drop] = 0
                c = (e.astype(bool) == truth[t][None]).all(-1).astype(float)
            corr.append(c)
            end.append(e)
    t, l = np.array(ts), np.array(ls)
    return lc.Pop(f"synthetic:{kind}", t, l, np.concatenate(corr), np.concatenate(end), np.arange(len(t)), t * lc.NL + l)
