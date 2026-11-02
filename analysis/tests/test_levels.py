"""Tests for the three-level model-vs-listener comparison. No network."""
import json
from types import SimpleNamespace

import numpy as np
import pytest

import levels_analysis as la
import levels_core as lc
from synthetic import synthetic


@pytest.fixture(scope="module")
def ref():
    return la.load_ref()   # bank, truth, listeners


def test_contrast_definitions():
    vm = np.array([[0.40, 0.50, 0.60, 0.30]])   # SayOnce, SayTwice, SayThrice, Distract
    c = lc.contrasts(vm)
    # gain = SayTwice - SayOnce, cost = SayOnce - Interfere, plateau = SayThrice - SayTwice
    assert np.isclose(c["gain"][0], 0.10) and np.isclose(c["cost"][0], 0.10) and np.isclose(c["plateau"][0], 0.10)


def test_listener_estimands_match_documented_numbers(ref):
    _, truth, H = ref
    assert H.U == 201 and len(np.unique(H.strata)) == 24
    s = lc.summary_stats(*lc.counts(H, np.ones((1, H.U))), truth)
    assert np.isclose(s["acc"][0], 0.4671, atol=1e-4)
    assert np.allclose([s[f"vm_{l}"][0] for l in lc.LEVELS], [0.4249, 0.5308, 0.5400, 0.3726], atol=1e-4)
    assert np.isclose(s["gain"][0], 0.5308 - 0.4249, atol=2e-4) and np.isclose(s["cost"][0], 0.4249 - 0.3726, atol=2e-4)


def test_counts_equal_direct_sums(ref):
    _, _, H = ref
    w = np.random.default_rng(0).integers(0, 3, H.U).astype(float)
    K, N, E = lc.counts(H, w[None])
    wr = w[H.unit]
    for t, l in [(0, 0), (2, 3)]:
        m = (H.t == t) & (H.l == l)
        assert np.isclose(N[0, t, l], wr[m].sum())
        assert np.allclose(K[0, t, l], (wr[m, None] * H.corr[m]).sum(0))
        assert np.allclose(E[0, t, l], (wr[m, None, None] * H.end[m]).sum(0))


def test_halves_are_disjoint_and_stratified(ref):
    _, _, H = ref
    WA, WB = lc.halve(H.strata, np.ones((50, H.U)), np.random.default_rng(1))
    assert ((WA > 0) & (WB > 0)).sum() == 0 and np.all(WA + WB == 1)
    for g in np.unique(H.strata):
        n = (H.strata == g).sum()
        a = WA[:, H.strata == g].sum(1)
        assert np.all((a == n // 2) | (a == n - n // 2))


def test_boot_halves_share_resample_within_block(ref):
    _, _, H = ref
    WA, WB = lc.boot_halves(H.strata, n_rep=3, n_inner=4, rng=np.random.default_rng(2))
    tot = (WA + WB).reshape(3, 4, -1)
    assert np.all(tot == tot[:, :1])                         # same resample for the 4 splits of a replicate
    assert not np.all(tot[0] == tot[1])                     # different resample across replicates
    assert np.all((WA + WB).sum(1) == H.U)


def test_matched_subsample_follows_half_sizes(ref):
    _, truth, H = ref
    M = synthetic(H, truth, "perfect", 50, np.random.default_rng(3))
    rng = np.random.default_rng(4)
    WA, _ = lc.halve(H.strata, np.ones((5, H.U)), rng)
    nA = lc.counts(H, WA)[1].reshape(5, -1)
    WM, short = lc.matched_subsample(M, lc.model_pool(M, 1, 5, rng, resample=False), nA, rng)
    assert short == 0 and WM.max() == 1
    assert np.array_equal(lc.counts(M, WM)[1].reshape(5, -1), nA)


def test_item_target_is_centred_and_twenty_long(ref):
    _, _, H = ref
    K, N, _ = lc.counts(H, np.ones((1, H.U)))
    t = lc.item_target(K, N)
    assert t.shape == (1, lc.NT, lc.NQ) and np.allclose(t.sum(-1), 0)


def test_model_loader_round_trip_and_unparsed_counts_wrong(ref, tmp_path):
    bank, truth, _ = ref
    rows = []
    for t in lc.TOPICS:
        for l in lc.LEVELS:
            key = {str(i + 1): sorted(a) for i, a in enumerate(bank[t]["answers"])}
            pa = dict(key)
            if (t, l) == ("fabrics", "distractor"):
                del pa["2"]                                       # unparsed question -> wrong, no endorsement
            n_ok = sum(1 for k in pa if pa[k] == key[k])
            rows.append({"condition_id": "C2", "topic_id": t, "level": l, "parsed_answers": pa,
                         "metrics": {"exact_match_accuracy": n_ok / lc.NQ}})
    f = tmp_path / "x_full_grid.jsonl"
    f.write_text("\n".join(json.dumps(r) for r in rows))
    M = lc.load_model_jsonl(f, bank, "C2")
    assert M.meta["metric_mismatch"] == 0 and M.U == 16
    s = lc.summary_stats(*lc.counts(M, np.ones((1, M.U))), truth)
    assert np.isclose(s["vm_distractor"][0], 1 - 0.2 / 4)
    i = np.flatnonzero((M.t == lc.TOPICS.index("fabrics")) & (M.l == 3))[0]
    assert M.end[i, 1].sum() == 0 and M.corr[i, 1] == 0
    with pytest.raises(ValueError):
        lc.load_model_jsonl(f, bank, "V1")


def test_verdict_never_says_closer():
    assert lc._verdict(0.01, 0.03, +1) == "further"
    assert lc._verdict(-0.03, -0.01, +1) == "as close"    # better than listener halves -> still "as close"
    assert lc._verdict(-0.03, -0.01, -1) == "further"     # correlation lower than listener halves
    assert lc._verdict(-0.01, 0.02, +1) == "as close"


def test_holm():
    out = lc.holm({"gain": 0.01, "cost": 0.04, "plateau": 0.5})
    assert np.isclose(out["gain"], 0.03) and np.isclose(out["cost"], 0.08) and np.isclose(out["plateau"], 0.5)


def test_qc_reads_profile_temperature_not_cli_default(tmp_path):
    snap = tmp_path / "config_snapshot.json"
    snap.write_text(json.dumps({"temperature": 0.0, "profile": {"name": "p", "sampling": {"temperature": 0.6}}}))
    s = la.sampling_of(snap)
    assert s["temperature"] == 0.6 and s["has_snapshot"]
    assert la.sampling_of(tmp_path / "missing.json") == {"has_snapshot": False}


def test_record_bar_halves_per_topic_and_resamples_whole_listeners(ref):
    _, _, H = ref
    Hr = lc.record_halves_pop(H)
    WA, WB = lc.halve(Hr.strata, np.ones((20, Hr.U)), np.random.default_rng(5))
    split_listener = ((WA.reshape(20, H.U, lc.NT) > 0).any(2) & (WB.reshape(20, H.U, lc.NT) > 0).any(2)).any()
    assert split_listener                                           # a listener's records can fall in both halves
    WA, WB = lc.boot_halves_records(Hr, n_rep=2, n_inner=3, rng=np.random.default_rng(6))
    tot = (WA + WB).reshape(2, 3, H.U, lc.NT)
    assert np.all(tot == tot[:, :1])                                # resample shared within a replicate
    assert np.all(tot == tot[..., :1])                              # whole listeners: same count in every topic
    assert np.all(tot.sum((2, 3)) == H.U * lc.NT)


def test_headroom_rule_precludes_gain_and_plateau_for_a_ceiling_model(ref):
    _, truth, H = ref
    M = synthetic(H, truth, "perfect", 50, np.random.default_rng(8))
    M.corr[:] = 1.0
    M.end[:] = truth[M.t]
    M.meta.pop("_design", None)
    args = SimpleNamespace(n_splits=100, n_boot=100, n_inner=5, seed=3)
    rec = la.level_rows(lc.record_halves_pop(H), M, truth, la.human_reference(H, truth, 100, 3),
                        lc.own_bootstrap(H, truth, 100, 3), args)
    assert rec["L2_gain_verdict"] == "ceiling-precluded" and rec["L2_plateau_verdict"] == "ceiling-precluded"
    assert rec["L2_cost_verdict"] == "no detectable effect"          # no floor problem at 100%
    assert "L2_plateau_p" in rec and "L2_plateau_p_holm" not in rec


def test_plan_shard_merge_round_trip(ref, tmp_path):
    """plan -> two shards -> merge gives one row per configuration; plan --skip-existing then finds nothing."""
    bank, _, _ = ref
    rng = np.random.default_rng(0)
    task = tmp_path / "runs" / "model-x" / "prof" / "prompted" / "tasks"
    task.mkdir(parents=True)
    rows = []
    for cond in ("C1", "C2"):
        for t in lc.TOPICS:
            for l in lc.LEVELS:
                for rep in range(50):
                    key = {str(i + 1): sorted(a) for i, a in enumerate(bank[t]["answers"])}
                    pa = {q: (v if rng.random() < 0.6 else [v[0] % 4 + 1]) for q, v in key.items()}
                    n_ok = sum(pa[q] == key[q] for q in key)
                    rows.append({"condition_id": cond, "topic_id": t, "level": l, "repeat_index": rep,
                                 "parsed_answers": pa, "metrics": {"exact_match_accuracy": n_ok / lc.NQ}})
    (task / "application_listening_qa_full_grid.jsonl").write_text("\n".join(json.dumps(r) for r in rows))
    (task / "config_snapshot.json").write_text(
        json.dumps({"profile": {"name": "prof", "sampling": {"temperature": 0.7}}}))
    out = tmp_path / "out"
    common = ["--out-dir", str(out), "--n-boot", "40", "--n-splits", "40", "--n-inner", "4"]
    assert la.main(["plan", "--runs-root", str(tmp_path / "runs"), *common]) == 0
    assert json.loads((out / "todo.json").read_text())["n_items"] == 2
    for shard in ("0/2", "1/2"):
        assert la.main(["run", "--todo", str(out / "todo.json"), "--shard", shard,
                        "--runs-root", str(tmp_path / "runs"), *common]) == 0
    assert la.main(["merge", *common]) == 0
    import pandas as pd
    df = pd.read_csv(out / "levels.csv")
    assert sorted(df.condition) == ["C1", "C2"] and (df.bar == "record").all()
    assert la.main(["plan", "--runs-root", str(tmp_path / "runs"), "--skip-existing", *common]) == 0
    assert json.loads((out / "todo.json").read_text())["n_items"] == 0
