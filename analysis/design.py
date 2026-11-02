"""Design constants shared by every analysis: topics, passage versions, and the content-question answer key.

Versions use the internal level names; the paper's names are SayOnce (control), SayTwice (repeat_short),
SayThrice (repeat_long) and Distract (distractor).
"""
from __future__ import annotations

from pathlib import Path

import yaml

LEVELS = ["control", "repeat_short", "repeat_long", "distractor"]
TOPICS = ["astronomy", "fabrics", "fruits", "martial_arts"]
# longdata_strict.csv and the Qualtrics export call the fruits topic "fruits_v2"
HUMAN_TOPIC = {"astronomy": "astronomy", "fabrics": "fabrics", "fruits_v2": "fruits", "martial_arts": "martial_arts"}
NT, NL, NQ = len(TOPICS), len(LEVELS), 5


def load_bank(data_dir: Path) -> dict:
    """topic -> {q_ids: [...], answers: [set,...]} for content questions, in questions.yaml order."""
    bank = {}
    for topic in TOPICS:
        doc = yaml.safe_load((data_dir / topic / "questions.yaml").open())
        qs = [q for q in doc["questions"] if q["metadata"].get("type") == "content"]
        bank[topic] = {
            "q_ids": [q["q_id"] for q in qs],
            "answers": [set(int(a) for a in (q["answer"] if isinstance(q["answer"], list) else [q["answer"]])) for q in qs],
        }
        assert len(qs) == NQ, f"{topic}: expected {NQ} content questions, got {len(qs)}"
    return bank
