#!/usr/bin/env python3
"""Build data/human/longdata_strict.csv from the raw Qualtrics export: one row per listener x topic x question,
keeping only listeners who passed all four attention checks (N = 201)."""
import pandas as pd

from data_prep import TOPICS, content_cols, col_qid, load_records

from paths import DATA
OUT = DATA / 'human'

COND_CATEGORIES = ['control', 'repeat_short', 'repeat_long', 'distractor']


def build_rows(records):
    """Rows for every listener who passed the attention check in all four topics."""
    rows = []
    for rec in records:
        if not rec['attn_pass']:
            continue
        for topic in TOPICS:
            sub = rec[topic]
            if not rec['fl_order']:
                serial_position = None
            else:
                serial_position = rec['fl_order'].index(topic) + 1 if topic in rec['fl_order'] else None
            cols = content_cols[topic]
            for qi, col in enumerate(cols):
                rows.append({
                    'pid':             rec['pid'],
                    'group':           rec['group'],
                    'topic':           topic,
                    'question_id':     col_qid[col],
                    'condition':       sub['cond'],
                    'correct':         sub['scores'][qi],
                    'partial':         sub['partial'][qi],
                    'serial_position': serial_position,
                    't_passage':       sub['t_passage'],
                    't_qs':            sub['t_qs'],
                    'diff_passage':    sub['diff_passage'],
                    'diff_qs':         sub['diff_qs'],
                    'duration':        rec['duration'],
                })
    df = pd.DataFrame(rows)
    df['condition'] = pd.Categorical(df['condition'], categories=COND_CATEGORIES, ordered=False)
    df['serial_position'] = pd.Categorical(df['serial_position'], categories=[1, 2, 3, 4], ordered=False)
    return df


def main():
    records, _ = load_records()
    df = build_rows(records)
    assert not df.duplicated(subset=['pid', 'topic', 'question_id']).any(), \
        'duplicate (pid, topic, question_id) rows'
    assert list(df['condition'].cat.categories) == COND_CATEGORIES
    df.to_csv(OUT / 'longdata_strict.csv', index=False)
    print(f'longdata_strict.csv: {len(df)} rows, {df["pid"].nunique()} listeners')
    print(df.groupby(['topic', 'condition'], observed=True)['pid'].nunique().unstack())


if __name__ == '__main__':
    main()
