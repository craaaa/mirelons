# Data schema

```
data/
├── stimuli/<topic>/               one folder per topic: astronomy, fabrics, fruits, martial_arts
│   ├── texts/
│   │   ├── control.md             SayOnce
│   │   ├── repeat_short.md        SayTwice
│   │   ├── repeat_long.md         SayThrice
│   │   └── distractor.md          Interfere
│   ├── audio/                     the recordings participants heard, one MP3 per version (same file names)
│   ├── questions.yaml             5 content questions + 1 attention check, with the answer key
│   └── features.md                every mention of each tested fact, per version (fabrics, fruits, martial_arts)
├── survey/
│   ├── multi_v6.qsf               Qualtrics survey (import into Qualtrics to inspect)
│   └── participant_text.txt       everything participants read, in survey order
├── human/
│   ├── results.tsv                raw Qualtrics export
│   └── longdata_strict.csv        one row per person × topic × question (built from results.tsv)
└── models/<model>/<profile>/<task>/tasks/
    ├── <kind>_full_grid.jsonl     one row per trial (some are .jsonl.gz)
    ├── <kind>_full_grid_summary.json
    └── config_snapshot.json       exact settings of the run
```

Internal version names are used in file names and data; the paper's names are:

| Internal | Paper |
|---|---|
| `control` | SayOnce |
| `repeat_short` | SayTwice |
| `repeat_long` | SayThrice |
| `distractor` | Interfere |

## Topics

- **SayOnce** — a base paragraph with each fact once, then 2–3 filler sentences that test nothing.
- **SayTwice** — each fact followed by one restatement; no filler.
- **SayThrice** — each fact followed by two restatements.
- **Interfere** — the base paragraph, then a paragraph about a competing entity with the same attributes.

### `questions.yaml`

```yaml
title: Fruits — Mirelon
answer_type: multi_select
scoring: per_statement
questions:
  - q_id: QF_V2_01                  # question id, used everywhere else (longdata_strict.csv, model runs)
    question: "Which of the following correctly describe ... Select all that apply."
    options:                        # always 5; option 5 is "None of the above"
      1: "The skin is a dark, nearly black shade of blue"
      2: "..."
      5: "None of the above"
    answer: [1, 2]                  # correct option numbers, 1-indexed in Qualtrics choice order; [5] = none true
    metadata:
      type: content                 # content (scored) | attention_check (used only to exclude listeners)
      feature: exterior_appearance  # which fact the question tests
      concepts: [mirelon]
```

Question ids by topic: astronomy `QA01`–`QA05`, fabrics `QFB01`–`QFB05`, fruits `QF_V2_01`–`QF_V2_05`,
martial arts `QMA01`–`QMA05`; attention checks `AT_<topic>` (fruits: `AT_fruits_v2`). A question is scored
correct only if the endorsed options equal `answer` exactly (chance = 1/16).

## Human Results

### `human/results.tsv`

The Qualtrics export: UTF-16, tab-separated, three header rows (field names, question text, import ids). One row per
submission (259 rows). Participant ids are pseudonymized (`PROLIFIC_PID` = `pt-NNNN`). Columns used:

| Column | Meaning |
|---|---|
| `PROLIFIC_PID` | listener id; duplicates are resolved by keeping the longest submission |
| `Finished`, `Duration (in seconds)` | completion and total time |
| `group` | counterbalancing group (1–24): which version each topic is heard in |
| `<topic>_cond` | version heard for that topic (`fruits_v2_cond` for fruits) |
| `<topic>_<q_id>` | selected option texts, comma-joined |
| `<topic>_AT_<topic>`, `<topic>_AT_correct` | attention-check answer and key |
| `FL_27_DO` | order the four topics were heard in |
| `<topic>_timing_passage_*`, `<topic>_timing_qs_*` | page timers |
| `<topic>_difficulty_1`, `<topic>_difficulty_2` | passage and question difficulty ratings |

### `human/longdata_strict.csv`

The 201 listeners who passed all four attention checks; 20 rows each (4 topics × 5 questions).

| Column | Meaning |
|---|---|
| `pid` | listener id |
| `group` | counterbalancing group |
| `topic` | `astronomy`, `fabrics`, `fruits_v2`, `martial_arts` |
| `question_id` | `q_id` from `questions.yaml` |
| `condition` | version (`control`, `repeat_short`, `repeat_long`, `distractor`) |
| `correct` | 1 if the endorsed options equal the key exactly |
| `partial` | (correct options endorsed − false options endorsed) / correct options, floored at 0 |
| `serial_position` | 1–4, when in the session the topic was heard |
| `t_passage`, `t_qs` | seconds on the passage page and on the question page |
| `diff_passage`, `diff_qs` | difficulty ratings |
| `duration` | total survey time (s) |

## Model Results

```
models/<model>/<profile>/<task>/tasks/
```

- **`<model>`** — 27 models, e.g. `Qwen_Qwen3-4B`, `gemini-3.1-pro-preview`, `claude-haiku-5-5`.
- **`<profile>`** — sampling profile and thinking mode, e.g. `qwen3-off`, `qwen3-think`, `gemini-3.1-pro`. Profiles
  ending in `-off` / `-think` are thinking off / on.
- **`<task>`** — setup and its hyperparameters:

| `<task>` | Setup (paper) | Memory | Encoding | Condition id |
|---|---|---|---|---|
| `prompted` | Prompted | full passage | – | `V1` Vanilla, `C1` TaskPr, `C2` HumPr, `C3` MemPr |
| `compactor-batch_k<k>` | Compactor | `k` key–value slots | whole passage | `C2` |
| `compactor-stream_k4` | Compactor | 4 slots | sentence by sentence | `C2-stream` |
| `sum-batch_<B>` | Summary | summary of ≤ `B` words (`B` = 15k) | whole passage | `C2` |
| `sum-stream_60` | Summary | ≤ 60 words | sentence by sentence | `C2-stream` |
| `prop-batch_<k>` | CBUS | ≤ `k` propositions | whole passage | `C2` |
| `prop-dropout_<k>` | CBUS + Dropout | `k` random of 3k extracted propositions | whole passage | `C2` |

`k` = 4 everywhere except the capacity sweep (k = 2–6) for 12 models. A configuration is one model × profile × task
× condition: 461 runs, 578 configurations (the prompted runs hold four conditions each).

### `*_full_grid.jsonl`

One row per trial: 4 topics × 4 versions × 50 repeats = 800 rows per condition. The file name starts with
`application_listening_qa` (prompted), `wm_application_listening_qa` (Compactor) or `sum_application_listening_qa`
(Summary, CBUS). Fields in every row:

| Field | Meaning |
|---|---|
| `id` | `<file prefix>:<condition>:r<repeat>:<topic>:<version>`; Summary and CBUS use `<file prefix>:<variant>:<budget>:r<repeat>:<topic>:<version>` |
| `condition_id`, `condition_name` | prompt / encoding condition (table above) |
| `topic_id`, `title` | topic folder name and title |
| `level` | version (`control`, `repeat_short`, `repeat_long`, `distractor`) |
| `repeat_index` | 1–50 |
| `recall_raw` (`raw_response` for prompted) | the model's answer text |
| `parsed_answers` | `{"1": [1, 3], ...}`: endorsed options per content question, keys in `questions.yaml` order |
| `parse_errors` | questions whose answer could not be parsed (scored wrong) |
| `metrics` | `exact_match_accuracy` (share of the 5 questions exactly right) and per-statement counts |
| `difficulty` | the model's passage / question difficulty ratings |

Additional fields by setup:

| Setup | Fields |
|---|---|
| Prompted | `prompt`, `reasoning` (thinking text if any), `finish_reason`, `completion_tokens` |
| Compactor | `encoding_log` (tool calls per step), `final_kv` (memory at question time), `segment_unit`, `recall_reasoning`, `recall_finish_reason` |
| Summary | `variant`, `encoding_log`, `final_summary`, `memory_words`, `budget`, `budget_fallbacks`, `budget_truncations`, `memory_calls`, `empty_response`, `n_unparsed_questions`, `reasoning` |
| CBUS (+ Dropout) | as Summary, with `final_propositions` instead of `final_summary` |

### `*_full_grid_summary.json`

Per-cell aggregates (`cells`), number of trials, and `llm_usage` (requests, tokens, reasoning tokens,
truncations, cost).

### `config_snapshot.json`

Everything needed to rerun: `model`, `backend`, `profile` (sampling settings, maximum tokens per request type),
`condition_id`, `streaming`, `segment_unit`, `slots` / budget, `n_repeats_per_cell`, tool-call caps, the full
`prompts`, and `git_provenance` (commit of the simulating-memory code that produced the run).
