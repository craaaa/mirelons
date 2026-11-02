"""Gzipped run files (EXPANSION_RUNS.md: JSONL over 50 MB is committed as *.jsonl.gz) read like plain ones."""
import gzip
import json

import levels_analysis as la
import levels_core as lc


def _write(tmp_path, name, rows, gz):
    data = "".join(json.dumps(r) + "\n" for r in rows).encode()
    p = tmp_path / name
    if gz:
        with gzip.open(p, "wb") as f:
            f.write(data)
    else:
        p.write_bytes(data)
    return p


def test_gz_reads_and_hashes_like_plain(tmp_path):
    rows = [{"condition_id": "C2", "i": i} for i in range(3)]
    a, b = tmp_path / "a", tmp_path / "b"
    a.mkdir(), b.mkdir()
    plain = _write(a, "x_full_grid.jsonl", rows, gz=False)
    zipped = _write(b, "x_full_grid.jsonl.gz", rows, gz=True)
    assert lc.run_files(a) == [plain] and lc.run_files(b) == [zipped]
    assert list(lc.open_run(plain)) == list(lc.open_run(zipped))
    assert la._sha1(plain) == la._sha1(zipped)


def test_plain_wins_over_gz_copy(tmp_path):
    rows = [{"i": 0}]
    plain = _write(tmp_path, "x_full_grid.jsonl", rows, gz=False)
    _write(tmp_path, "x_full_grid.jsonl.gz", rows, gz=True)
    assert lc.run_files(tmp_path) == [plain]
