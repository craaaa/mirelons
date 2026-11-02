"""Paper Tables 1-3, written as CSV.

  Table 1  passage length by version: words and audio duration (s), mean (range) over the four topics.
  Table 2  listener accuracy by number of true statements in the answer key (0 = "None of the above" is correct).
  Table 3  sampling settings per model and thinking mode, read from each run's config_snapshot.json.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

import human_ingest
from design import LEVELS, TOPICS
from levels_core import LEVEL_LABEL
from plotting import model_label
from paths import RUNS, STIMULI


def table1(stimuli: Path = STIMULI) -> pd.DataFrame:
    from mutagen.mp3 import MP3
    rows = []
    for level in LEVELS:
        words = [len((stimuli / t / "texts" / f"{level}.md").read_text().split()) for t in TOPICS]
        secs = [MP3(stimuli / t / "audio" / f"{level}.mp3").info.length for t in TOPICS]
        rows.append({"version": LEVEL_LABEL[level], "words_mean": round(float(np.mean(words))),
                     "words_min": min(words), "words_max": max(words),
                     "audio_s_mean": round(float(np.mean(secs))), "audio_s_min": round(min(secs)),
                     "audio_s_max": round(max(secs))})
    return pd.DataFrame(rows)


def table2() -> pd.DataFrame:
    """Per number of true content statements: questions, exact-match accuracy (%), mean options endorsed
    ("None of the above" included), omission (% of responses that endorsed only true statements but missed at
    least one) and commission (% that endorsed at least one false option, "None of the above" included)."""
    d = pd.DataFrame(human_ingest.ingest_humans(human_ingest.load_question_bank()))
    nota = d.option_n == 5
    d["true_content"] = d.option_is_true & ~nota
    d["false_endorsed"] = d.endorsed & ~d.option_is_true
    d["true_endorsed"] = d.endorsed & d.option_is_true
    d["wrong"] = d.endorsed != d.option_is_true
    r = d.groupby(["respondent_id", "topic", "question_id"]).agg(
        n_true=("true_content", "sum"), selected=("endorsed", "sum"), n_wrong=("wrong", "sum"),
        any_false=("false_endorsed", "any"), hits=("true_endorsed", "sum"), keyed=("option_is_true", "sum"))
    r["correct"] = r.n_wrong == 0
    r["omission"] = ~r.any_false & (r.hits < r.keyed)
    g = r.reset_index().groupby("n_true")
    out = pd.DataFrame({
        "questions": g.apply(lambda x: x[["topic", "question_id"]].drop_duplicates().shape[0], include_groups=False),
        "accuracy_pct": 100 * g.correct.mean(),
        "selected": g.selected.mean(),
        "omission_pct": 100 * g.omission.mean(),
        "commission_pct": 100 * g.any_false.mean(),
    }).round({"accuracy_pct": 1, "selected": 2, "omission_pct": 1, "commission_pct": 1})
    out.loc[out.index <= 1, "omission_pct"] = np.nan        # impossible with 0 or 1 true statements
    return out.reset_index()


# Gemini runs send no thinking setting except 3.6 Flash (minimal); the others use the API default level.
GEMINI_DEFAULT_THINKING = {"gemini-3.5-flash-lite": "Minimal", "gemini-3.8-flash": "On (med.)",
                           "gemini-3.1-pro": "On (high)"}


def _thinking(profile: str, s: dict) -> str:
    if profile in GEMINI_DEFAULT_THINKING:
        return GEMINI_DEFAULT_THINKING[profile]
    eb = s.get("extra_body") or {}
    if "thinking_level" in json.dumps(eb):
        return "Minimal"
    if not profile.endswith("-think"):
        return "Off"
    effort = s.get("reasoning_effort") or (eb.get("chat_template_kwargs") or {}).get("reasoning_effort")
    return "On (med.)" if effort == "medium" else "On"


def table3(runs: Path = RUNS) -> pd.DataFrame:
    rows = {}
    for f in sorted(runs.glob("*/*/*/tasks/config_snapshot.json")):
        slug, profile = f.parts[-5], f.parts[-4]
        if (slug, profile) in rows:
            continue
        s = json.loads(f.read_text())["profile"]["sampling"]
        omit = bool(s.get("omit_sampling"))
        rows[(slug, profile)] = {
            "model": model_label(slug), "thinking": _thinking(profile, s),
            "temperature": "not sent" if omit else s.get("temperature"),
            "top_p": "" if omit else s.get("top_p"), "top_k": "" if omit else s.get("top_k")}
    return pd.DataFrame(rows.values())


def write_tables(out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    table1().to_csv(out / "table1_passage_length.csv", index=False)
    table2().to_csv(out / "table2_human_by_true_statements.csv", index=False)
    table3().to_csv(out / "table3_sampling.csv", index=False)
