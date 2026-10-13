"""Gameglory ETL test task - starter skeleton.

This is only a suggested structure. You may rename functions, split the code into modules
(extract.py / transform.py / load.py ...), use pandas or plain Python - whatever you can explain.

Run (suggested CLI):
    python pipeline.py --db gameglory.db ../data/batch_1
    python pipeline.py --db gameglory.db ../data/batch_2
Running the same command twice must not create duplicates.
"""
import argparse
import csv
import json
import sqlite3
from pathlib import Path


# --------------------------------------------------------------------------- extract
def extract_store(path: Path) -> tuple[str, list[dict]]:
    """Read store_export.json. Return (exported_at, list of raw items)."""
    # TODO
    raise NotImplementedError


def extract_stats(path: Path) -> list[dict]:
    """Read stats.csv as a list of raw rows (strings)."""
    # TODO
    raise NotImplementedError


def extract_reviews(path: Path) -> list[dict]:
    """Read reviews.jsonl line by line.

    Some lines are broken JSON - the pipeline must not crash on them.
    Count them for the data quality report.
    """
    # TODO
    raise NotImplementedError


def extract_fx(path: Path) -> dict[str, float]:
    """Read fx_rates.csv -> {"USD": 1.0, "EUR": ..., "RUB": ...}."""
    # TODO
    raise NotImplementedError


# --------------------------------------------------------------------------- transform
def parse_date(value):
    """Return an ISO date string 'YYYY-MM-DD' or None. Several input formats exist."""
    # TODO
    raise NotImplementedError


def parse_tags(value):
    """'RPG; Base-Building , rpg' -> a clean list of tags. Decide and document the rules."""
    # TODO
    raise NotImplementedError


def to_usd(price: dict, fx: dict[str, float]) -> float:
    """{'amount_cents': 1999, 'currency': 'EUR'} -> price in USD."""
    # TODO
    raise NotImplementedError


def match_key(title: str, year) -> tuple:
    """Key used to match a game from stats.csv with a game from store_export.json."""
    # TODO
    raise NotImplementedError


def transform_store(items, fx):
    """Clean store items: duplicates, dates, prices, tags. Return clean records + counters."""
    # TODO
    raise NotImplementedError


def transform_stats(rows):
    """Clean stats rows: duplicates, numbers like '1 234' or '1,234', empty values."""
    # TODO
    raise NotImplementedError


def transform_reviews(rows):
    """Clean reviews: duplicates, types, suspicious values."""
    # TODO
    raise NotImplementedError


# --------------------------------------------------------------------------- load
def create_schema(conn: sqlite3.Connection) -> None:
    """CREATE TABLE IF NOT EXISTS ... (games, tags, game_tags, reviews, price_history).

    Think about PRIMARY KEY / UNIQUE / FOREIGN KEY - they are what makes re-runs safe.
    """
    # TODO
    raise NotImplementedError


def load(conn: sqlite3.Connection, games, stats, reviews, exported_at: str) -> None:
    """Idempotent load (INSERT ... ON CONFLICT ...). Write price_history only when the price changed."""
    # TODO
    raise NotImplementedError


# --------------------------------------------------------------------------- report
def report(counters: dict, conn: sqlite3.Connection) -> None:
    """Print / save the data quality report: what was read, dropped, fixed - and why."""
    # TODO
    raise NotImplementedError


def main() -> None:
    ap = argparse.ArgumentParser(description="Gameglory ETL: load one batch into SQLite")
    ap.add_argument("batch_dir", type=Path, help="e.g. ../data/batch_1")
    ap.add_argument("--db", type=Path, default=Path("gameglory.db"))
    ap.add_argument("--fx", type=Path, default=Path("../data/fx_rates.csv"))
    args = ap.parse_args()

    conn = sqlite3.connect(args.db)
    conn.execute("PRAGMA foreign_keys = ON")
    create_schema(conn)
    # TODO: extract -> transform -> load -> report


if __name__ == "__main__":
    main()
