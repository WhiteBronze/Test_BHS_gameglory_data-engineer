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
from datetime import datetime
import re



# --------------------------------------------------------------------------- extract
def extract_store(path: Path) -> tuple[str, list[dict]]:
    """Read store_export.json. Return (exported_at, list of raw items)."""
    with Path(path).open(encoding="utf-8") as fh:
        payload = json.load(fh)
    return payload["exported_at"], payload["items"]


def extract_stats(path: Path) -> list[dict]:
    """Read stats.csv as a list of raw rows (strings)."""
    with Path(path).open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def extract_reviews(path: Path) -> tuple[list[dict], int]:
    """Read reviews.jsonl. Skip broken lines, count them."""
    rows = []
    broken = 0
    with Path(path).open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                broken += 1
    return rows, broken


def extract_fx(path: Path) -> dict[str, float]:
    """Read fx_rates.csv -> {"USD": 1.0, ...}."""
    fx: dict[str, float] = {}
    with Path(path).open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            fx[row["currency"].strip().upper()] = float(row["usd_per_unit"])
    fx.setdefault("USD", 1.0)
    return fx


# --------------------------------------------------------------------------- transform
def parse_date(value):
    """Return an ISO date string 'YYYY-MM-DD' or None."""
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None
    for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%b %d, %Y"):
        try:
            return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def parse_tags(value):
    """'RPG; Base-Building , rpg' -> ['base-building', 'rpg']."""
    if value is None:
        return []
    parts = re.split(r"[;,|]+", str(value))
    return sorted({p.strip().lower().replace(" ", "-") for p in parts if p.strip()})


def to_usd(price: dict, fx: dict[str, float]) -> float:
    """{'amount_cents': 1999, 'currency': 'EUR'} -> price in USD."""
    if not price:
        return None
    cents = price.get("amount_cents")
    if cents is None:
        return None
    currency = (price.get("currency") or "USD").upper()
    rate = fx.get(currency)
    if rate is None:
        return None
    return round(cents / 100 * rate, 4)


def match_key(title: str, year) -> tuple:
    """Key used to match a game from stats.csv with a game from store_export.json."""
    if not title:
        norm = ""
    else:
        t = str(title).lower()
        for ch in ("™", "®", "©"):
            t = t.replace(ch, " ")
        t = re.sub(r"[^\w\s]", " ", t, flags=re.UNICODE)
        t = re.sub(r"\s+", " ", t)
        norm = t.strip()

    if year is None:
        return (norm, None)
    try:
        year_int = int(year)
    except (ValueError, TypeError):
        year_int = None
    return (norm, year_int)

def transform_store(items, fx):
    """Clean store items: duplicates, dates, prices, tags. Return clean records + counters."""
    counters = {
        "read": len(items),
        "dropped_no_date": 0,
        "dropped_no_title": 0,
        "dropped_duplicate_store_id": 0,
        "price_without_fx": 0,
    }

    games_by_id = {}
    for item in items:
        store_id = (item.get("store_id") or "").strip()
        if not store_id:
            continue

        title = (item.get("title") or "").strip()
        if not title:
            counters["dropped_no_title"] += 1
            continue

        release_date = parse_date(item.get("release_date"))
        if release_date is None:
            counters["dropped_no_date"] += 1
            continue

        if store_id in games_by_id:
            counters["dropped_duplicate_store_id"] += 1
            continue

        price = item.get("price") or {}
        price_usd = to_usd(price, fx)
        if price_usd is None:
            counters["price_without_fx"] += 1

        games_by_id[store_id] = {
            "game_id": store_id,
            "title": title,
            "release_date": release_date,
            "year": int(release_date[:4]),
            "developer": (item.get("developer") or "").strip() or None,
            "publisher": (item.get("publisher") or "").strip() or None,
            "currency": (price.get("currency") or "USD").upper(),
            "price_cents": price.get("amount_cents"),
            "price_usd": price_usd,
            "tags": parse_tags(item.get("tags")),
        }

    return list(games_by_id.values()), counters


def transform_stats(rows):
    """Clean stats rows: duplicates, numbers like '1 234' or '1,234', empty values."""

    def parse_num(value):
        if value is None:
            return None
        s = str(value).strip().replace("\u00a0", "").replace(" ", "")
        if not s:
            return None
        if "," in s:
            if "." in s:
                s = s.replace(",", "")
            elif s.count(",") > 1:
                s = s.replace(",", "")
            else:
                head, _, tail = s.rpartition(",")
                if len(tail) == 3 and head.lstrip("-").isdigit():
                    s = s.replace(",", "")
                else:
                    s = s.replace(",", ".")
        try:
            return float(s)
        except ValueError:
            return None

    def parse_int(value):
        f = parse_num(value)
        return None if f is None else int(round(f))

    counters = {
        "read": len(rows),
        "dropped_no_ext_id": 0,
        "dropped_duplicate_ext_id": 0,
    }

    by_ext_id = {}
    for row in rows:
        ext_id = (row.get("ext_id") or "").strip()
        if not ext_id:
            counters["dropped_no_ext_id"] += 1
            continue

        rec = {
            "ext_id": ext_id,
            "name": (row.get("name") or "").strip() or None,
            "year": parse_int(row.get("year")),
            "owners": parse_int(row.get("owners")),
            "ccu_peak": parse_int(row.get("ccu_peak")),
            "positive_pct": parse_num(row.get("positive_pct")),
            "reviews_total": parse_int(row.get("reviews_total")),
            "updated_at": (row.get("updated_at") or "").strip() or None,
        }

        prev = by_ext_id.get(ext_id)
        if prev is not None:
            counters["dropped_duplicate_ext_id"] += 1
            if (rec["updated_at"] or "") > (prev["updated_at"] or ""):
                by_ext_id[ext_id] = rec
        else:
            by_ext_id[ext_id] = rec

    return list(by_ext_id.values()), counters


def transform_reviews(rows):
    """Clean reviews: duplicates, types, suspicious values."""
    counters = {
        "read": len(rows),
        "dropped_no_id": 0,
        "dropped_duplicate": 0,
        "fixed_negative_playtime": 0,
    }

    seen = set()
    out = []
    for row in rows:
        rid = row.get("review_id")
        if rid is None:
            counters["dropped_no_id"] += 1
            continue
        rid = str(rid)
        if not rid:
            counters["dropped_no_id"] += 1
            continue

        if rid in seen:
            counters["dropped_duplicate"] += 1
            continue
        seen.add(rid)

        playtime = row.get("playtime_hours")
        if playtime is not None and playtime < 0:
            counters["fixed_negative_playtime"] += 1
            playtime = None

        voted_up = row.get("voted_up")
        if voted_up is None:
            voted_up_int = None
        else:
            voted_up_int = 1 if voted_up else 0

        out.append({
            "review_id": rid,
            "game_id": row.get("game_ref"),
            "voted_up": voted_up_int,
            "text": row.get("text"),
            "playtime_hours": playtime,
            "created_at": row.get("created_at"),
        })

    return out, counters


# --------------------------------------------------------------------------- load
def create_schema(conn: sqlite3.Connection) -> None:
    """CREATE TABLE IF NOT EXISTS ... (games, game_tags, stats, reviews, price_history, etl_runs)."""
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS games (
            game_id       TEXT PRIMARY KEY,
            title         TEXT NOT NULL,
            release_date  TEXT,
            year          INTEGER,
            developer     TEXT,
            publisher     TEXT,
            currency      TEXT,
            price_cents   INTEGER,
            price_usd     REAL
        );

        CREATE TABLE IF NOT EXISTS game_tags (
            game_id TEXT NOT NULL REFERENCES games(game_id) ON DELETE CASCADE,
            tag     TEXT NOT NULL,
            PRIMARY KEY (game_id, tag)
        );

        CREATE TABLE IF NOT EXISTS stats (
            ext_id        TEXT PRIMARY KEY,
            game_id       TEXT REFERENCES games(game_id),
            name          TEXT,
            year          INTEGER,
            owners        INTEGER,
            ccu_peak      INTEGER,
            positive_pct  REAL,
            reviews_total INTEGER,
            updated_at    TEXT
        );

        CREATE TABLE IF NOT EXISTS reviews (
            review_id      TEXT PRIMARY KEY,
            game_id        TEXT REFERENCES games(game_id) ON DELETE CASCADE,
            voted_up       INTEGER,
            text           TEXT,
            playtime_hours REAL,
            created_at     TEXT
        );

        CREATE TABLE IF NOT EXISTS price_history (
            game_id     TEXT NOT NULL REFERENCES games(game_id) ON DELETE CASCADE,
            observed_at TEXT NOT NULL,
            currency    TEXT,
            price_usd   REAL,
            PRIMARY KEY (game_id, observed_at)
        );

        CREATE TABLE IF NOT EXISTS etl_runs (
            batch_hash   TEXT PRIMARY KEY,
            batch_label  TEXT,
            exported_at  TEXT,
            loaded_at    TEXT NOT NULL,
            rows_games   INTEGER,
            rows_stats   INTEGER,
            rows_reviews INTEGER
        );
    """)

def load(conn: sqlite3.Connection, games, stats, reviews, exported_at: str) -> None:
    """Idempotent load (INSERT ... ON CONFLICT ...). Write price_history only when the price changed."""
    with conn:
        for g in games:
            conn.execute(
                """
                INSERT INTO games (game_id, title, release_date, year,
                                   developer, publisher, currency,
                                   price_cents, price_usd)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(game_id) DO UPDATE SET
                    title        = excluded.title,
                    release_date = excluded.release_date,
                    year         = excluded.year,
                    developer    = COALESCE(excluded.developer, games.developer),
                    publisher    = COALESCE(excluded.publisher, games.publisher),
                    currency     = excluded.currency,
                    price_cents  = excluded.price_cents,
                    price_usd    = excluded.price_usd
                """,
                (
                    g["game_id"], g["title"], g["release_date"], g["year"],
                    g["developer"], g["publisher"], g["currency"],
                    g["price_cents"], g["price_usd"],
                ),
            )

            for tag in g["tags"]:
                conn.execute(
                    "INSERT OR IGNORE INTO game_tags (game_id, tag) VALUES (?, ?)",
                    (g["game_id"], tag),
                )

            conn.execute(
                """
                INSERT OR IGNORE INTO price_history
                    (game_id, observed_at, currency, price_usd)
                VALUES (?, ?, ?, ?)
                """,
                (g["game_id"], exported_at, g["currency"], g["price_usd"]),
            )

        game_lookup = {}
        for row in conn.execute("SELECT game_id, title, year FROM games").fetchall():
            game_lookup[match_key(row[1], row[2])] = row[0]

        for s in stats:
            s["game_id"] = game_lookup.get(match_key(s["name"], s["year"]))
            conn.execute(
                """
                INSERT INTO stats (ext_id, game_id, name, year, owners, ccu_peak,
                                   positive_pct, reviews_total, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(ext_id) DO UPDATE SET
                    game_id       = COALESCE(excluded.game_id, stats.game_id),
                    name          = excluded.name,
                    year          = excluded.year,
                    owners        = COALESCE(excluded.owners, stats.owners),
                    ccu_peak      = COALESCE(excluded.ccu_peak, stats.ccu_peak),
                    positive_pct  = COALESCE(excluded.positive_pct, stats.positive_pct),
                    reviews_total = COALESCE(excluded.reviews_total, stats.reviews_total),
                    updated_at    = COALESCE(excluded.updated_at, stats.updated_at)
                """,
                (
                    s["ext_id"], s["game_id"], s["name"], s["year"], s["owners"],
                    s["ccu_peak"], s["positive_pct"], s["reviews_total"], s["updated_at"],
                ),
            )

        for r in reviews:
            conn.execute(
                """
                INSERT OR IGNORE INTO reviews
                    (review_id, game_id, voted_up, text, playtime_hours, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    r["review_id"], r["game_id"], r["voted_up"],
                    r["text"], r["playtime_hours"], r["created_at"],
                ),
            )

# --------------------------------------------------------------------------- report
def report(counters: dict, conn: sqlite3.Connection) -> None:
    """Print the data quality report: what was read, dropped, fixed - and why."""
    print("\n=== data quality report ===")
    for block, data in counters.items():
        print(f"\n[{block}]")
        for key, value in data.items():
            print(f"  {key}: {value}")

    print("\n=== DB counts ===")
    for table in ("games", "game_tags", "stats", "reviews", "price_history", "etl_runs"):
        n = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"  {table}: {n}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Gameglory ETL: load one batch into SQLite")
    ap.add_argument("batch_dir", type=Path, help="e.g. ../data/batch_1")
    ap.add_argument("--db", type=Path, default=Path("gameglory.db"))
    ap.add_argument("--fx", type=Path, default=Path("../data/fx_rates.csv"))
    args = ap.parse_args()

    batch_dir = args.batch_dir

    exported_at, items = extract_store(batch_dir / "store_export.json")
    stats_rows = extract_stats(batch_dir / "stats.csv")
    reviews_rows, broken = extract_reviews(batch_dir / "reviews.jsonl")
    fx = extract_fx(args.fx)

    games, c_store = transform_store(items, fx)
    stats, c_stats = transform_stats(stats_rows)
    reviews, c_reviews = transform_reviews(reviews_rows)

    conn = sqlite3.connect(args.db)
    conn.execute("PRAGMA foreign_keys = ON")
    create_schema(conn)

    existing_ids = {row[0] for row in conn.execute("SELECT game_id FROM games").fetchall()}
    valid_game_ids = {g["game_id"] for g in games} | existing_ids
    before = len(reviews)
    reviews = [r for r in reviews if r["game_id"] in valid_game_ids]
    c_reviews["dropped_unknown_game"] = before - len(reviews)

    load(conn, games, stats, reviews, exported_at)

    counters = {
        "extract": {
            "store_items": len(items),
            "stats_rows": len(stats_rows),
            "reviews_rows": len(reviews_rows),
            "broken_jsonl": broken,
        },
        "store": c_store,
        "stats": c_stats,
        "reviews": c_reviews,
    }
    report(counters, conn)
    conn.close()

if __name__ == "__main__":
    main()
