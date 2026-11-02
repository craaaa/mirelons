"""Load results/levels/levels.csv for the figures: map run folders to setups and hyperparameters, and attach the
listener reference values.

Run folder -> setup: prompted -> Prompted (all four prompts; condition C2 = HumPr is the default prompt);
compactor-batch_k<k> / compactor-stream_k4 -> Compactor; sum-batch_<15k> / sum-stream_60 -> Summary;
prop-batch_<k> -> CBUS; prop-dropout_<k> -> CBUS + Dropout. Thinking from the profile name: *-think / qwen3-think
-> on, *-off / qwen3-off -> off; a model with only one mode is "n/a".
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

import levels_analysis as la
from paths import LEVELS

DEFAULT_PROMPT = "C2"   # HumPr, the prompt the memory-constrained setups use

FAMILY_RULES = [("qwen2.5", "Qwen2.5"), ("qwen3", "Qwen3"), ("gemini", "Gemini"), ("gpt-6", "GPT-6"),
                ("claude", "Claude"), ("deepseek", "DeepSeek"), ("glm", "GLM"), ("gemma", "Gemma")]

def family(slug: str) -> str:
    s = slug.lower()
    return next((f for k, f in FAMILY_RULES if k in s), slug)

def parse_task(task: str):
    """task folder -> (setup, k, encode) or None for tasks not in the figures."""
    if task == "prompted":
        return "prompted", float("nan"), "batch"
    m = re.fullmatch(r"compactor-(batch|stream)_k(\d+)", task)
    if m:
        return "compactor", int(m.group(2)), m.group(1)
    m = re.fullmatch(r"sum-(batch|stream)_(\d+)", task)
    if m:
        return "summary", int(m.group(2)) // 15, m.group(1)
    m = re.fullmatch(r"prop-(batch|dropout)_(\d+)", task)
    if m:
        return ("chosen-propositions" if m.group(1) == "batch" else "random-dropout"), int(m.group(2)), "batch"
    return None

def thinking_of(profile: str) -> str:
    p = profile.lower()
    if p.endswith("-think") or "think" in p.split("-")[-1]:
        return "on"
    if p.endswith("-off"):
        return "off"
    return "n/a"

def load(levels_csv: Path, ref_json: Path, prompted_condition: str) -> pd.DataFrame:
    df = pd.read_csv(levels_csv)
    parsed = df.task.map(parse_task)
    df = df[parsed.notna()].copy()
    df[["setup", "k", "encode"]] = pd.DataFrame(parsed[parsed.notna()].tolist(), index=df.index)
    # all four prompts are kept; prompt_default marks the default one
    df["prompt_default"] = (df.setup != "prompted") | (df.condition == prompted_condition)
    df["thinking"] = df.profile.map(thinking_of)
    # a model with only one thinking mode -> "n/a" (its only mode is the main one)
    modes = df.groupby("model_slug").thinking.agg(lambda x: set(x) - {"n/a"})
    single = modes[modes.map(len) < 2].index
    df.loc[df.model_slug.isin(single), "thinking"] = "n/a"
    df["model"] = df.model_slug
    df["family"] = df.model_slug.map(family)
    ref = json.loads(ref_json.read_text())["bootstrap"]
    for k in ("acc", "gain", "cost"):
        df[f"human_{k}"], df[f"human_{k}_lo"], df[f"human_{k}_hi"] = ref[k]["est"], ref[k]["lo"], ref[k]["hi"]
    return df.reset_index(drop=True)

def human_once_distract(n_boot: int = 10000, seed: int = 20261010) -> tuple[float, float, float]:
    """Listeners' SayOnce - Distract accuracy difference with its 95% CI, from the same stratified listener
    bootstrap (draws, seed, chunking) as levels_human_reference.json, which reproduces its cost CI exactly."""
    import numpy as np
    import levels_core as lc
    bank, truth, H = la.load_ref()
    est = lc.summary_stats(*lc.counts(H, np.ones((1, H.U))), truth)
    est = float(est["vm_control"][0] - est["vm_distractor"][0])
    rng, v = np.random.default_rng(seed), []
    for b0 in range(0, n_boot, 500):
        st = lc.summary_stats(*lc.counts(H, lc.stratified_counts(H.strata, min(500, n_boot - b0), rng)), truth)
        v.append(st["vm_control"] - st["vm_distractor"])
    lo, hi = np.nanpercentile(np.concatenate(v), [2.5, 97.5])
    return est, float(lo), float(hi)


def load_all(levels_dir: Path = LEVELS) -> pd.DataFrame:
    """Every configuration in levels.csv with its setup, k, encoding, thinking mode and the listener references
    (accuracy, repetition and interference with 95% CIs)."""
    df = load(levels_dir / "levels.csv", levels_dir / "levels_human_reference.json", DEFAULT_PROMPT)
    df["human_od"], df["human_od_lo"], df["human_od_hi"] = human_once_distract()
    return df
