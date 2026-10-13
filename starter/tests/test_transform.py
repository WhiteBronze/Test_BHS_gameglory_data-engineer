"""Minimal tests for transformations.

Run without extra packages:   python tests/test_transform.py
or with pytest (optional):    python -m pytest -q
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pipeline  # noqa: E402


def test_parse_date_iso():
    assert pipeline.parse_date("2021-02-15") == "2021-02-15"


# TODO: add checks for the other date formats, tags, prices, dedup...


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
