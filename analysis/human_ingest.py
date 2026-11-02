#!/usr/bin/env python3
"""Option-level listener table from the raw Qualtrics export.

One row per (listener, topic, question, option) for the 201 listeners who passed all four attention checks.
Option-level endorsement is recovered from the comma-joined Qualtrics answer cell with a combinatorial matcher
(option texts can themselves contain commas). Used by levels_core.load_humans (asserted against
data/human/longdata_strict.csv) and tables.table2.
"""
from __future__ import annotations

import csv
from itertools import combinations

import yaml

from paths import HUMAN_TSV, STIMULI

# ── canonical topic / level / condition vocab ──
TOPICS = ["astronomy", "fruits", "martial_arts", "fabrics"]          # canonical
LEVELS = ["control", "repeat_short", "repeat_long", "distractor"]
# Qualtrics TSV uses fruits_v2 for the fruits topic; map both ways.
HUMAN_TSV_TOKEN = {"astronomy": "astronomy", "fruits": "fruits_v2",
                   "martial_arts": "martial_arts", "fabrics": "fabrics"}
FL_TOPIC = {"FL_32": "martial_arts", "FL_33": "fruits", "FL_34": "astronomy", "FL_35": "fabrics"}


# ── question bank: per-topic ordered content questions, option texts, truth ──
def load_question_bank() -> dict:
    """topic -> list of dicts: {q_id, options:{n:text}, answer:set[int]}, content only, in file order."""
    bank: dict[str, list[dict]] = {}
    for topic in TOPICS:
        qfile = STIMULI / topic / "questions.yaml"
        qdata = yaml.safe_load(qfile.open())
        qs = []
        for q in qdata["questions"]:
            if q["metadata"].get("type") != "content":
                continue
            ans = q["answer"] if isinstance(q["answer"], list) else [q["answer"]]
            qs.append({"q_id": q["q_id"],
                       "options": {int(k): str(v) for k, v in q["options"].items()},
                       "answer": set(int(a) for a in ans)})
        bank[topic] = qs
    return bank


def parse_response(raw: str, all_opts: list[str]) -> frozenset:
    """Recover the set of selected option TEXTS from a Qualtrics multi-select cell.

    Qualtrics joins selected choice texts with ', ' (or ',') and choice texts can
    themselves contain commas, so a plain split is wrong — try every subset whose
    join reproduces the cell (same approach as multi_v6/data_prep.parse_response)."""
    if not raw:
        return frozenset()
    for r in range(len(all_opts) + 1):
        for combo in combinations(all_opts, r):
            if ",".join(combo) == raw:
                return frozenset(combo)
    for r in range(len(all_opts) + 1):
        for combo in combinations(all_opts, r):
            if ", ".join(combo) == raw:
                return frozenset(combo)
    return frozenset(s.strip() for s in raw.split(","))


# ── humans ──
def ingest_humans(bank: dict) -> list[dict]:
    tsv = HUMAN_TSV
    with tsv.open(encoding="utf-16") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    rows = rows[2:]  # Qualtrics: two header/meta rows below the field names

    # dedupe by PROLIFIC_PID, keep the longest-duration finished submission
    best: dict[str, dict] = {}
    for r in rows:
        pid = (r.get("PROLIFIC_PID") or "").strip()
        if not pid:
            continue
        dur = float(r.get("Duration (in seconds)", 0) or 0)
        if pid not in best or dur > float(best[pid].get("Duration (in seconds)", 0) or 0):
            best[pid] = r

    out: list[dict] = []
    for pid, r in best.items():
        if (r.get("Finished") or "").strip() != "True":
            continue
        if not (r.get("martial_arts_cond") or "").strip():
            continue
        group = (r.get("group") or "").strip()
        fl_raw = (r.get("FL_27_DO") or "").strip()
        fl_order = [FL_TOPIC.get(c) for c in fl_raw.split("|") if c in FL_TOPIC]

        # WHOLE-PARTICIPANT attention exclusion (user directive 2026-07-30): keep a
        # respondent only if they passed the attention check in ALL 4 topics. This is
        # the `longdata_strict` rule — reconcile.py matches that file 1:1.
        attn_pass_all = True
        for topic in TOPICS:
            tok = HUMAN_TSV_TOKEN[topic]
            g = (r.get(f"{tok}_AT_{tok}") or "").strip()
            c = (r.get(f"{tok}_AT_correct") or "").strip()
            given = frozenset(g.split(",")) if g else frozenset()
            corr = frozenset(c.split(",")) if c else frozenset()
            if given != corr:
                attn_pass_all = False
                break
        if not attn_pass_all:
            continue

        for topic in TOPICS:
            tok = HUMAN_TSV_TOKEN[topic]
            level = (r.get(f"{tok}_cond") or "").strip()
            if level not in LEVELS:
                continue
            position = (fl_order.index(topic) + 1) if topic in fl_order else None
            t_qs = float(r.get(f"{tok}_timing_qs_Page Submit", 0) or 0)
            rt_ms = int(round(t_qs * 1000)) if t_qs else None

            for q in bank[topic]:
                q_id = q["q_id"]
                opts = q["options"]
                all_texts = list(opts.values())
                raw_cell = (r.get(f"{tok}_{q_id}") or "").strip()
                given_texts = parse_response(raw_cell, all_texts)
                for opt_n, opt_text in opts.items():
                    out.append({
                        "respondent_id": pid,
                        "agent": "human",
                        "model_name": None,
                        "sample_idx": None,
                        "group_id": int(group) if group.isdigit() else None,
                        "position": position,
                        "modality": "audio",
                        "topic": topic,
                        "level": level,
                        "question_id": q_id,
                        "option_id": f"{q_id}_o{opt_n}",
                        "option_n": opt_n,
                        "option_is_true": bool(opt_n in q["answer"]),
                        "endorsed": bool(opt_text in given_texts),
                        "rt_ms": rt_ms,
                        "attn_pass_all": True,
                        "system": "human",
                        "encode_mode": None,
                    })
    return out
