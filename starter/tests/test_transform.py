import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pipeline  # noqa: E402

def test_parse_date_iso():
    assert pipeline.parse_date("2021-02-15") == "2021-02-15"

def test_parse_date_european():
    assert pipeline.parse_date("08.05.2026") == "2026-05-08"

def test_parse_date_english():
    assert pipeline.parse_date("Jun 16, 2024") == "2024-06-16"

def test_parse_date_none():
    assert pipeline.parse_date(None) is None

def test_parse_date_empty():
    assert pipeline.parse_date("") is None
    assert pipeline.parse_date("   ") is None


def test_parse_date_invalid():
    assert pipeline.parse_date("Coming soon") is None
    assert pipeline.parse_date("TBA") is None

def test_parse_tags_basic():
    assert pipeline.parse_tags("RPG; Base-Building , rpg") == ["base-building", "rpg"]

def test_parse_tags_multi_separators():
    assert pipeline.parse_tags("a|b,c;d") == ["a", "b", "c", "d"]

def test_parse_tags_duplicates():
    assert pipeline.parse_tags("a,a,A") == ["a"]

def test_parse_tags_spaces():
    assert pipeline.parse_tags("hack and slash; rpg") == ["hack-and-slash", "rpg"]

def test_parse_tags_none():
    assert pipeline.parse_tags(None) == []

def test_parse_tags_empty():
    assert pipeline.parse_tags("") == []
    assert pipeline.parse_tags(";;;") == []

def test_to_usd_usd():
    fx = {"USD": 1.0, "EUR": 1.08, "RUB": 0.0105}
    assert pipeline.to_usd({"amount_cents": 2499, "currency": "USD"}, fx) == 24.99

def test_to_usd_eur():
    fx = {"USD": 1.0, "EUR": 1.08, "RUB": 0.0105}
    assert pipeline.to_usd({"amount_cents": 1999, "currency": "EUR"}, fx) == 21.5892

def test_to_usd_rub():
    fx = {"USD": 1.0, "EUR": 1.08, "RUB": 0.0105}
    assert pipeline.to_usd({"amount_cents": 99900, "currency": "RUB"}, fx) == 10.4895

def test_to_usd_none():
    assert pipeline.to_usd(None, {"USD": 1.0}) is None
    assert pipeline.to_usd({}, {"USD": 1.0}) is None

def test_to_usd_unknown_currency():
    assert pipeline.to_usd({"amount_cents": 2499, "currency": "GBP"}, {"USD": 1.0}) is None

def test_match_key_special_chars():
    a = pipeline.match_key("Vesfell: Scarlet Atlas ™", 2022)
    b = pipeline.match_key("Vesfell Scarlet Atlas", 2022)
    assert a == b

def test_match_key_extra_spaces():
    a = pipeline.match_key("Hearth  of Vesmark", 2019)
    b = pipeline.match_key("Hearth of Vesmark", 2019)
    assert a == b

def test_match_key_year_string():
    assert pipeline.match_key("Game", "2014") == ("game", 2014)

def test_match_key_year_invalid():
    assert pipeline.match_key("Game", "abc") == ("game", None)

if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)