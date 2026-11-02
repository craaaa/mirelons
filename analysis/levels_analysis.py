#!/usr/bin/env python3
"""Score every model configuration against the listeners at three levels: overall accuracy, condition effects
(repetition = SayTwice - SayOnce, interference = SayOnce - Interfere) and item agreement (Pearson r with the
listeners' question difficulty). Each statistic is compared with the gap between two random halves of the
listeners (paper Appendix D.1). Shared estimands live in levels_core.py.

    python analysis/levels_analysis.py check     # reproduce the listener numbers reported in the paper
    python analysis/levels_analysis.py qc        # inclusion checks for every run -> results/levels/levels_qc.csv
    python analysis/levels_analysis.py run       # score every configuration locally -> results/levels/levels.csv
    # on a cluster: `plan` -> todo.json, analysis/slurm/submit_levels.sh (`run --todo ... --shard i/N`), `merge`

Implementation choices:
- Listener halves are drawn within each of the 24 Latin-square groups (record halves within group x topic);
  the model is subsampled per cell to the size of half A in that cell.
- CI = percentiles over --n-boot replicates of the mean d over --n-inner splits; a bootstrap replicate keeps a
  resampled listener's copies on one side of the split.
- Question resample (within topic) is applied to the item correlation only.
- Hits / false endorsements exclude the "None of the above" option.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import numpy as np

import levels_core as lc

from paths import HUMAN_CSV, LEVELS as OUT_DIR, RUNS, STIMULI as DATA_DIR

# Listener numbers from the human-results write-up, tolerance in the same units.
DOCUMENTED = [
    ("acc", 0.467, 0.0015), ("gain", 0.106, 0.0015), ("cost", 0.052, 0.0015), ("plateau", 0.009, 0.0015),
    ("vm_control", 0.4249, 1e-4), ("vm_repeat_short", 0.5308, 1e-4), ("vm_repeat_long", 0.5400, 1e-4),
    ("vm_distractor", 0.3726, 1e-4),
    ("hit_control", 0.64, 0.01), ("hit_repeat_short", 0.73, 0.01), ("hit_repeat_long", 0.75, 0.01),
    ("fe_control", 0.109, 0.01), ("fe_distractor", 0.144, 0.01),
    ("half_gap_acc_median", 0.019, 0.003), ("half_gap_plateau_median", 0.030, 0.003),
    ("item_split_half", 0.94, 0.006), ("item_split_half_p05", 0.90, 0.01),
]


def load_ref():
    bank = lc.load_bank(DATA_DIR)
    return bank, lc.truth_tensor(bank), lc.load_humans(HUMAN_CSV, bank)


# ---------------------------------------------------------------- check
def human_reference(H: lc.Pop, truth, n_splits: int, seed: int) -> dict:
    rng = np.random.default_rng([seed, 1])
    pt = lc.summary_stats(*lc.counts(H, np.ones((1, H.U))), truth)
    out = {k: float(v[0]) for k, v in pt.items()}
    WA, WB = lc.halve(H.strata, np.ones((n_splits, H.U)), rng)
    sA = lc.summary_stats(*lc.counts(H, WA), truth)
    sB = lc.summary_stats(*lc.counts(H, WB), truth)
    for k in ("acc", "gain", "cost", "plateau"):
        g = np.abs(sA[k] - sB[k])
        out[f"half_gap_{k}_median"] = float(np.median(g))
        out[f"half_gap_{k}_p95"] = float(np.percentile(g, 95))
    out["gain_sign_replicates"] = float(np.mean((sA["gain"] > 0) & (sB["gain"] > 0)))
    out["cost_sign_replicates"] = float(np.mean((sA["cost"] > 0) & (sB["cost"] > 0)))
    rel = lc.item_reliability(H, n_splits, seed)
    out["item_split_half"], out["item_split_half_p05"], out["item_sb"] = rel["split_half"], rel["p05"], rel["sb"]
    out["tau_half_median"] = float(np.median(sA["tau"]))
    out["tau_half_p95"] = float(np.percentile(sA["tau"], 95))
    return out


def cmd_check(args) -> int:
    bank, truth, H = load_ref()
    ref = human_reference(H, truth, args.n_splits, args.seed)
    boot = lc.own_bootstrap(H, truth, args.n_boot, args.seed)
    ok = True
    print(f"listeners {H.U}, Latin-square groups {len(np.unique(H.strata))}")
    for k, want, tol in DOCUMENTED:
        got = ref[k]
        flag = abs(got - want) <= tol
        ok &= flag
        print(f"  {'ok ' if flag else 'BAD'} {k:28s} {got:8.4f}  documented {want:.4f} (tol {tol})")
    print(f"  acc 95% CI (stratified, B={args.n_boot}) [{boot['acc']['lo']:.4f}, {boot['acc']['hi']:.4f}]"
          "  documented [0.441, 0.492] with B=4000 unstratified")
    print(f"  half-gap median / 95th pct: gain {ref['half_gap_gain_median']:.4f} / {ref['half_gap_gain_p95']:.4f}, "
          f"cost {ref['half_gap_cost_median']:.4f} / {ref['half_gap_cost_p95']:.4f} (gain SayTwice - SayOnce, cost SayOnce - Interfere; "
          "no documented values)")
    print(f"  sign replicates across halves: gain {ref['gain_sign_replicates']:.3f}, cost {ref['cost_sign_replicates']:.3f}")
    print(f"  tau (moment) full {ref['tau']:.3f}; listener halves median {ref['tau_half_median']:.3f}, "
          f"95th pct {ref['tau_half_p95']:.3f}")
    K, N, _ = lc.counts(H, np.ones((1, H.U)))
    g = lc.glmm_tau_laplace(K[0], N[0])
    print(f"  tau (GLMM, Laplace) full {g['tau']:.3f}; question SD {g['sd_question']:.3f}  (documented: item x version"
          " variance estimated at 0)")
    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


# ---------------------------------------------------------------- run discovery and QC
def discover(runs_root: Path) -> list[dict]:
    """runs_root/<model_slug>/<profile>/<task>/tasks/*_full_grid.jsonl[.gz] (EXPANSION_RUNS.md layout)."""
    out = []
    for f in [f for d in sorted(runs_root.glob("*/*/*/tasks")) for f in lc.run_files(d)]:
        task_dir = f.parent.parent
        out.append({"model_slug": task_dir.parent.parent.name, "profile": task_dir.parent.name,
                    "task": task_dir.name, "jsonl": f, "snapshot": f.parent / "config_snapshot.json"})
    return out


def sampling_of(snapshot: Path) -> dict:
    """Effective sampling settings: the profile's (the snapshot's top-level `temperature` is a CLI default)."""
    if not snapshot.exists():
        return {"has_snapshot": False}
    c = json.loads(snapshot.read_text())
    s = (c.get("profile") or {}).get("sampling") or {}
    return {"has_snapshot": True, "profile_name": (c.get("profile") or {}).get("name"),
            "temperature": s.get("temperature"), "omit_sampling": bool(s.get("omit_sampling")),
            "top_p": s.get("top_p"), "top_k": s.get("top_k")}


def qc_rows(run: dict) -> list[dict]:
    """Inclusion checks per (run, condition). No accuracy-derived quantities (freeze boundary)."""
    rows_by_cond: dict[str, list] = {}
    for line in lc.open_run(run["jsonl"]):
        if line.strip():
            r = json.loads(line)
            rows_by_cond.setdefault(r.get("condition_id"), []).append(r)
    samp = sampling_of(run["snapshot"])
    out = []
    for cond, rows in sorted(rows_by_cond.items()):
        cells: dict = {}
        for r in rows:
            cells.setdefault((r.get("topic_id"), r.get("level")), []).append(r)
        n_cell = [len(v) for v in cells.values()]
        n_unparsed = sum(sum(1 for q in range(lc.NQ) if str(q + 1) not in (r.get("parsed_answers") or {})) for r in rows)
        patterns = [len({json.dumps(r.get("parsed_answers") or {}, sort_keys=True) for r in v}) for v in cells.values()]
        trunc = sum(1 for r in rows if r.get("finish_reason") == "length")
        rec = {**{k: run[k] for k in ("model_slug", "profile", "task")}, "condition": cond, **samp,
               "n_rows": len(rows), "n_cells": len(cells), "n_cell_min": min(n_cell), "n_cell_max": max(n_cell),
               "unparsed_rate": n_unparsed / (lc.NQ * len(rows)),
               "empty_response_rate": sum(1 for r in rows if r.get("empty_response")) / len(rows),
               "truncated_rate": trunc / len(rows),
               "identical_cell_share": float(np.mean([p == 1 for p in patterns])),
               "distinct_patterns_median": float(np.median(patterns))}
        kv = [r for r in rows if r.get("final_kv") is not None]
        if kv:
            k_slots = int(run["task"].split("_k")[-1]) if "_k" in run["task"] else 4
            rec["zero_write_share"] = sum(1 for r in kv if len(r["final_kv"]) == 0) / len(kv)
            rec["slot_util_mean"] = float(np.mean([r["metrics"].get("slot_utilization", np.nan) for r in kv]))
            rec["slot_overflow_share"] = sum(1 for r in kv if len(r["final_kv"]) > k_slots) / len(kv)
            rec["rejected_long_writes_mean"] = float(np.mean([r["metrics"].get("rejected_long_writes", 0) or 0 for r in kv]))
        if any("budget" in r for r in rows):
            rec["budget_truncation_share"] = sum(1 for r in rows if (r.get("budget_truncations") or 0) > 0) / len(rows)
            rec["budget_fallback_share"] = sum(1 for r in rows if (r.get("budget_fallbacks") or 0) > 0) / len(rows)
            props = [r for r in rows if r.get("final_propositions") is not None]
            if props:
                rec["memory_over_cap_share"] = sum(1 for r in props if len(r["final_propositions"]) > r["budget"]) / len(props)
            else:
                rec["memory_over_cap_share"] = sum(1 for r in rows if (r.get("memory_words") or 0) > r["budget"]) / len(rows)
        flags = []
        if not samp["has_snapshot"]:
            flags.append("no_config_snapshot")
        elif samp.get("temperature") == 0 and not samp.get("omit_sampling"):
            flags.append("temperature_0")
        if min(n_cell) < 50 or len(cells) < lc.NT * lc.NL:
            flags.append("incomplete_n50")
        if rec["unparsed_rate"] > 0.02:
            flags.append("parse_failures")
        if rec["identical_cell_share"] >= 0.75:
            flags.append("low_answer_variability")
        if rec.get("slot_overflow_share", 0) > 0 or rec.get("memory_over_cap_share", 0) > 0:
            flags.append("memory_over_limit")
        if rec.get("zero_write_share", 0) > 0.10:
            flags.append("zero_write")
        if rec.get("budget_truncation_share", 0) > 0.10:
            flags.append("summary_cut_heavy")
        rec["flags"] = ";".join(flags)
        rec["included"] = not any(f in flags for f in ("no_config_snapshot", "temperature_0", "incomplete_n50"))
        out.append(rec)
    return out


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    keys: list[str] = []
    for r in rows:
        keys += [k for k in r if k not in keys]
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)


def cmd_qc(args) -> int:
    runs = discover(Path(args.runs_root))
    rows = [r for run in runs for r in qc_rows(run)]
    out = Path(args.out_dir) / "levels_qc.csv"
    write_csv(out, rows)
    n_inc = sum(r["included"] for r in rows)
    print(f"{len(runs)} runs, {len(rows)} (run, condition) rows, {n_inc} included -> {out}")
    for r in rows:
        if r["flags"]:
            print(f"  {r['model_slug']}/{r['profile']}/{r['task']}:{r['condition']}  {r['flags']}")
    return 0


# ---------------------------------------------------------------- per-configuration levels
HUMAN_SIGN = {"gain": +1, "cost": +1, "plateau": 0}


def level_rows(H: lc.Pop, M: lc.Pop, truth, href: dict, hboot: dict, args) -> dict:
    """All four levels for one model configuration -> flat dict (one CSV row)."""
    cmp_ = lc.compare(H, M, truth, n_splits=args.n_splits, n_boot=args.n_boot, n_inner=args.n_inner, seed=args.seed)
    own = lc.own_bootstrap(M, truth, args.n_boot, args.seed + 1)
    rec = {"n_cell_min": int(np.bincount(M.strata).min()), "matched_size_shortfall": cmp_["_meta"]["matched_size_shortfall"]}

    # Level 1
    c = cmp_["acc"]
    rec.update(L1_model_acc=own["acc"]["est"], L1_model_acc_lo=own["acc"]["lo"], L1_model_acc_hi=own["acc"]["hi"],
               L1_human_acc=hboot["acc"]["est"], L1_signed_gap=cmp_["acc_signed"]["model_mean"],
               L1_d=c["d"], L1_d_lo=c["d_lo"], L1_d_hi=c["d_hi"], L1_ref_median=c["ref_median"], L1_ref_p95=c["ref_p95"])
    if c["verdict"] == "further":
        rec["L1_verdict"] = "further: over-remembers" if rec["L1_signed_gap"] > 0 else "further: under-remembers"
    else:
        rec["L1_verdict"] = c["verdict"]

    # Level 2
    # Holm over gain and cost; plateau is the negative control
    holm = lc.holm({k: cmp_[k]["p_boot"] for k in ("gain", "cost")})
    holm["plateau"] = cmp_["plateau"]["p_boot"]
    # headroom rule: precluded when the model has no room for a listener-sized effect
    once, twice, thrice = (own[f"vm_{l}"]["est"] for l in ("control", "repeat_short", "repeat_long"))
    precluded = {"gain": "ceiling-precluded" if 1 - once < hboot["gain"]["est"] else None,
                 "cost": "floor-precluded" if once < hboot["cost"]["est"] else None,   # cost = SayOnce - Interfere (item 13)
                 "plateau": "ceiling-precluded" if 1 - twice < hboot["plateau"]["hi"] else None}
    rec["L2_sayonce_model"], rec["L2_saytwice_model"] = once, twice
    for k in ("gain", "cost", "plateau"):
        c = cmp_[k]
        e = own[k]
        rec.update({f"L2_{k}_model": e["est"], f"L2_{k}_model_lo": e["lo"], f"L2_{k}_model_hi": e["hi"],
                    f"L2_{k}_human": hboot[k]["est"], f"L2_{k}_d": c["d"], f"L2_{k}_d_lo": c["d_lo"],
                    f"L2_{k}_d_hi": c["d_hi"], f"L2_{k}_ref_median": c["ref_median"], f"L2_{k}_ref_p95": c["ref_p95"],
                    f"L2_{k}_signed_gap": cmp_[f"{k}_signed"]["model_mean"],
                    f"L2_{k}_p" + ("" if k == "plateau" else "_holm"): holm[k]})
        if k == "plateau":
            if precluded[k]:
                rec["L2_plateau_verdict"] = precluded[k]
            else:
                keeps = e["lo"] > 0 and c["d_lo"] > 0
                rec["L2_plateau_verdict"] = "unlike listeners, keeps gaining" if keeps else f"plateau {c['verdict']}"
            continue
        dirn = lc.direction(e, HUMAN_SIGN[k])
        rec[f"L2_{k}_direction"] = dirn
        if precluded[k]:
            v = precluded[k]
        elif dirn == "reversed":
            v = "reverses"
        elif dirn == "null":
            v = "no detectable effect"
        elif c["verdict"] == "further":
            v = "same direction, further: " + ("larger" if rec[f"L2_{k}_signed_gap"] > 0 else "smaller")
        else:
            v = "as close"
        rec[f"L2_{k}_verdict"] = v
    # why-check (option level): gain via hits, cost via false endorsements, as in listeners
    for k in ("d_hit_gain", "d_fe_gain", "d_hit_cost", "d_fe_cost"):
        rec[f"L2why_{k}_model"], rec[f"L2why_{k}_model_lo"], rec[f"L2why_{k}_model_hi"] = own[k]["est"], own[k]["lo"], own[k]["hi"]
        rec[f"L2why_{k}_human"] = hboot[k]["est"]
    rec["L2why_gain_route"] = route(own["d_hit_gain"], own["d_fe_gain"], "hits")
    rec["L2why_cost_route"] = route(own["d_fe_cost"], own["d_hit_cost"], "false endorsements")
    rec["fe_control_model"], rec["fe_control_human"] = own["fe_control"]["est"], hboot["fe_control"]["est"]

    # Level 3a
    c = cmp_["item_r"]
    relM = lc.item_reliability(M, args.n_splits, args.seed + 2)
    r_full = float(lc.pearson_rows(lc.item_target(*lc.counts(M, np.ones((1, M.U)))[:2]).reshape(1, -1),
                                   lc.item_target(*lc.counts(H, np.ones((1, H.U)))[:2]).reshape(1, -1))[0])
    rec.update(L3a_r_full=r_full, L3a_rel_model_sb=relM["sb"], L3a_rel_human_sb=href["item_sb"],
               L3a_r_star=r_full / np.sqrt(relM["sb"] * href["item_sb"]) if relM["sb"] > 0 else float("nan"),
               L3a_model_r_with_half=c["model_mean"], L3a_ref_median=c["ref_median"], L3a_ref_p05=c["ref_p05"],
               L3a_d=c["d"], L3a_d_lo=c["d_lo"], L3a_d_hi=c["d_hi"])
    if not np.isfinite(relM["sb"]) or relM["sb"] < lc.NOT_ESTIMABLE_REL:
        rec["L3a_verdict"] = "not estimable"
    else:
        rec["L3a_verdict"] = c["verdict"]

    # Level 3b, average to average
    c = cmp_["tau"]
    rec.update(L3b_tau_model=c["model_mean"], L3b_tau_model_lo=c["model_lo"], L3b_tau_model_hi=c["model_hi"],
               L3b_tau_half_median=c["ref_median"], L3b_tau_half_p95=c["ref_p95"],
               L3b_d=c["d"], L3b_d_lo=c["d_lo"], L3b_d_hi=c["d_hi"])
    if c["verdict"] == "further":
        rec["L3b_verdict"] = "question-specific shifts listeners lack"
    elif c["model_hi"] < lc.TAU_MISFIT:
        rec["L3b_verdict"] = "uniform like listener groups"
    else:
        rec["L3b_verdict"] = "can't tell"
    return rec


def route(main: dict, other: dict, expected: str) -> str:
    """'same route' when the listeners' route carries the effect (CI > 0); 'different route' when only the other
    one does; 'both' / 'neither' otherwise."""
    m, o = main["lo"] > 0, other["lo"] > 0
    if m and not o:
        return f"same route ({expected})"
    if o and not m:
        return "different route"
    return "both routes" if m else "neither"


KEY = ("model_slug", "profile", "task", "condition", "bar")


def _sha1(path: Path) -> str:
    import hashlib
    h = hashlib.sha1()
    with lc.open_run(path, "b") as f:  # gzipped runs: sha1 of the decompressed JSONL
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def plan_items(runs_root: Path, bar: str, only=(), include_flagged=False, done: set | None = None):
    """(items to score, QC rows). An item = one included (run, condition); `rel` is the JSONL path relative to
    runs_root, so the plan can be resolved against a copy of the runs on another machine. `done` = keys
    (KEY + sha1) already scored -> skipped."""
    items, qc_all = [], []
    for run in discover(runs_root):
        if only and not any(x in f"{run['model_slug']}/{run['profile']}/{run['task']}" for x in only):
            continue
        rows = qc_rows(run)
        qc_all += rows
        sha = None
        for q in rows:
            if not q["included"] and not include_flagged:
                continue
            sha = sha or _sha1(run["jsonl"])
            item = {k: q[k] for k in ("model_slug", "profile", "task", "condition", "flags")}
            item.update(bar=bar, jsonl_sha1=sha, rel=str(run["jsonl"].relative_to(runs_root)))
            if done and tuple(item[k] for k in KEY) + (sha,) in done:
                continue
            items.append(item)
    return items, qc_all


def _done_keys(path: Path) -> set:
    if not path.exists():
        return set()
    with path.open() as f:
        return {tuple(r[k] for k in KEY) + (r["jsonl_sha1"],) for r in csv.DictReader(f)}


def cmd_plan(args) -> int:
    out = Path(args.out_dir)
    done = _done_keys(out / "levels.csv") if args.skip_existing else None
    items, qc_all = plan_items(Path(args.runs_root), args.bar, args.only, args.include_flagged, done)
    write_csv(out / "levels_qc.csv", qc_all)
    (out / "todo.json").write_text(json.dumps({"bar": args.bar, "n_items": len(items), "items": items}, indent=1))
    print(f"{len(items)} configurations to score ({len(qc_all)} run x condition rows checked"
          + (f", {len(done)} already scored" if done is not None else "") + f") -> {out / 'todo.json'}")
    return 0


def _score(items, runs_root: Path, args, out_csv: Path) -> int:
    bank, truth, H = load_ref()
    href = human_reference(H, truth, args.n_splits, args.seed)
    hboot = lc.own_bootstrap(H, truth, args.n_boot, args.seed)
    rows = []
    for it in items:
        Hbar = lc.record_halves_pop(H) if it["bar"] == "record" else H
        M = lc.load_model_jsonl(runs_root / it["rel"], bank, it["condition"])
        rec = {k: it[k] for k in ("model_slug", "profile", "task", "condition", "flags", "bar", "jsonl_sha1")}
        rec["n_boot"], rec["n_splits"], rec["seed"] = args.n_boot, args.n_splits, args.seed
        rec.update(level_rows(Hbar, M, truth, href, hboot, args))
        rows.append(rec)
        print(f"  {rec['model_slug']}/{rec['profile']}/{rec['task']}:{rec['condition']}  L1 {rec['L1_verdict']} | "
              f"G {rec['L2_gain_verdict']} | C {rec['L2_cost_verdict']} | 3a {rec['L3a_verdict']} | "
              f"3b {rec['L3b_verdict']}", flush=True)
    write_csv(out_csv, rows)
    print(f"{len(rows)} configurations -> {out_csv}")
    return len(rows)


def _todo_tag(items) -> str:
    """Short hash of a todo list (configuration keys + JSONL hashes)."""
    import hashlib
    keys = sorted("|".join(str(it[k]) for k in KEY) + "|" + it["jsonl_sha1"] for it in items)
    return hashlib.sha1("\n".join(keys).encode()).hexdigest()[:8]


def cmd_run(args) -> int:
    out = Path(args.out_dir)
    runs_root = Path(args.runs_root)
    if args.todo:
        plan = json.loads(Path(args.todo).read_text())
        i, n = (int(x) for x in args.shard.split("/"))
        items = plan["items"][i::n]
        # the todo hash keeps part files of different scoring rounds from overwriting each other
        _score(items, runs_root, args, out / "parts" / f"levels_part_{_todo_tag(plan['items'])}_{i:04d}_of_{n:04d}.csv")
    else:   # local, all at once
        items, _ = plan_items(runs_root, args.bar, args.only, args.include_flagged)
        _score(items, runs_root, args, out / "parts" / f"levels_part_{_todo_tag(items)}_local.csv")
        cmd_merge(args)
    return 0


def cmd_merge(args) -> int:
    """levels.csv = previous levels.csv + every part (later rows win per configuration key)."""
    import pandas as pd
    out = Path(args.out_dir)
    frames = [pd.read_csv(out / "levels.csv")] if (out / "levels.csv").exists() else []
    parts = sorted((out / "parts").glob("levels_part_*.csv"))
    frames += [pd.read_csv(f) for f in parts if f.stat().st_size > 0]
    if not frames:
        print("nothing to merge")
        return 1
    df = pd.concat(frames, ignore_index=True).drop_duplicates(list(KEY), keep="last")
    df = df.sort_values(list(KEY)).reset_index(drop=True)
    df.to_csv(out / "levels.csv", index=False)
    bank, truth, H = load_ref()
    ref = {"reference": human_reference(H, truth, args.n_splits, args.seed),
           "bootstrap": lc.own_bootstrap(H, truth, args.n_boot, args.seed)}
    (out / "levels_human_reference.json").write_text(json.dumps(ref, indent=1))
    print(f"{len(parts)} parts -> {len(df)} configurations in {out / 'levels.csv'}")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("check", "qc", "plan", "run", "merge"):
        p = sub.add_parser(name)
        p.add_argument("--seed", type=int, default=20261010)
        p.add_argument("--n-splits", type=int, default=2000)
        p.add_argument("--n-boot", type=int, default=10000 if name in ("run", "merge") else 1000)
        p.add_argument("--n-inner", type=int, default=20)
        p.add_argument("--out-dir", default=str(OUT_DIR))
        if name in ("plan", "run"):
            p.add_argument("--bar", choices=["listener", "record"], default="record",
                           help="record halves within (group, topic) (paper) or whole-listener halves")
        if name in ("qc", "plan", "run"):
            p.add_argument("--runs-root", default=str(RUNS))
        if name in ("plan", "run"):
            p.add_argument("--include-flagged", action="store_true")
            p.add_argument("--only", nargs="*", default=[])
        if name == "plan":
            p.add_argument("--skip-existing", action="store_true",
                           help="skip configurations already in <out-dir>/levels.csv with the same JSONL sha1")
        if name == "run":
            p.add_argument("--todo", default=None, help="todo.json from `plan` (cluster array jobs)")
            p.add_argument("--shard", default="0/1", help="i/N: score items i, i+N, i+2N, ... of the todo list")
    args = ap.parse_args(argv)
    return {"check": cmd_check, "qc": cmd_qc, "plan": cmd_plan, "run": cmd_run, "merge": cmd_merge}[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())
