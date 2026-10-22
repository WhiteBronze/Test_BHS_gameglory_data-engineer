# Gameglory ETL — тестовое задание Data Engineer

ETL-пайплайн: читает две выгрузки (`batch_1`, `batch_2`) из трёх источников, чистит данные, сопоставляет игры между источниками и загружает в SQLite с идемпотентной загрузкой и историей цен.

## Как запустить

```
cd starter
python pipeline.py ../data/batch_1 --db gameglory.db
python pipeline.py ../data/batch_2 --db gameglory.db
```

Зависимости: `pandas`, `pytest` (см. `requirements.txt`). SQLite встроен в Python.

Тесты:

```
python tests/test_transform.py
```

SQL-вопросы:

```
python run_questions.py
```

или

```
sqlite3 gameglory.db < questions.sql
```

## Что сделано

1. **Extract** — чтение трёх файлов (`store_export.json`, `stats.csv`, `reviews.jsonl`) и `fx_rates.csv`.
2. **Transform**:
   - даты в 3 форматах → ISO (`parse_date`);
   - цены в центах → USD через `fx_rates.csv` (`to_usd`);
   - теги → нормализованный список (`parse_tags`);
   - дубли по `store_id` / `ext_id` / `review_id` — отбрасываются;
   - отрицательный `playtime_hours` → `NULL`;
   - отзывы на несуществующие игры — отбрасываются.
3. **Load** — SQLite с UPSERT (`ON CONFLICT ... DO UPDATE`, `INSERT OR IGNORE`):
   - таблицы: `games`, `game_tags`, `stats`, `reviews`, `price_history`, `etl_runs`;
   - повторный запуск не создаёт дублей;
   - `price_history` хранит все наблюдения цены (по `observed_at`).
4. **Отчёт** — счётчики по extract/transform и `SELECT COUNT(*)` по таблицам.
5. **SQL-вопросы** — `questions.sql` (Q1–Q5).

## Проблемы в данных и решения

- **Битые строки JSONL** → пропускаются, считаются (`broken_jsonl`).
- **Даты в разных форматах** → `parse_date` перебирает 3 формата (`%Y-%m-%d`, `%d.%m.%Y`, `%b %d, %Y`).
- **Числа с запятыми/пробелами** (`"1,234"`, `"3 907"`, `"95,6"`) → `parse_num` внутри `transform_stats`.
- **Отрицательный `playtime_hours`** → `NULL`.
- **Игры без даты** (`None`, `"Coming soon"`, `"TBA"`) → отбрасываются.
- **Дубли** `store_id` / `ext_id` / `review_id` → отбрасываются.
- **`™`, `®`** в названиях → убираются в `match_key` для сопоставления.
- **Лишние пробелы** в названиях (`"Hearth  of Vesmark"`) → схлопываются.
- **Отзывы на несуществующие игры** → отбрасываются.

## Сопоставление источников

У `store` и `stats` нет общего идентификатора. Сопоставление — по `(нормализованное название, год)` через `match_key`. Заполняется `stats.game_id`:

- **521 из 529** stats сопоставились (98.5%).
- **8** — без пары (названия/годы разошлись).

## Результаты Q1–Q5

### Q1 — топ-10 тегов по числу игр

| tag | games_count |
|---|---|
| singleplayer | 124 |
| 2d | 122 |
| multiplayer | 118 |
| difficult | 100 |
| sci-fi | 100 |
| 3d | 92 |
| story-rich | 91 |
| procedural-generation | 90 |
| base-building | 77 |
| crafting | 73 |

### Q2 — по годам 2018–2026

| year | games | free_games | avg_paid_price_usd |
|---|---|---|---|
| 2018 | 33 | 4 | 14.27 |
| 2019 | 44 | 1 | 10.88 |
| 2020 | 28 | 1 | 16.40 |
| 2021 | 49 | 8 | 13.02 |
| 2022 | 47 | 4 | 13.50 |
| 2023 | 49 | 5 | 15.87 |
| 2024 | 60 | 11 | 11.63 |
| 2025 | 48 | 3 | 12.43 |
| 2026 | 41 | 3 | 15.80 |

### Q3 — топ-10 игр по числу отзывов

| title | reviews_count | pct_recommended | positive_pct |
|---|---|---|---|
| Bramblespire | 84 | 98.8 | 98.6 |
| Lumenheart: Second Wind | 83 | 79.5 | 65.2 |
| Tidedrift 3 | 83 | 79.5 | 79.4 |
| Luncross: Distant Comet | 82 | 84.1 | 79.2 |
| Frontier of Keshaven® | 80 | 98.8 | 98.4 |
| Gearbreak 2 | 79 | 92.4 | 95.0 |
| Silent Hearth | 79 | 86.1 | 80.5 |
| Pilgrim of Galdris | 78 | 83.3 | 82.1 |
| Starlit Bastion | 78 | 71.8 | 73.4 |
| Tidal Quarry | 78 | 87.2 | 85.8 |

`pct_recommended` (из `reviews`) и `positive_pct` (из `stats.csv`) часто близки, но иногда расходятся (например, Lumenheart: 79.5 vs 65.2) — это разные источники и разные выборки.

### Q4 — топ-3 игры по owners в топ-5 тегах (фрагмент)

| tag | rank | title | owners |
|---|---|---|---|
| 2d | 1 | Frontier of Keshaven® | 485030 |
| 2d | 2 | Hidden Canopy | 299892 |
| 2d | 3 | Ulmreach: Tiny Hearth | 299453 |
| difficult | 1 | Frontier of Keshaven® | 485030 |
| difficult | 2 | Gearbreak 2 | 452960 |
| difficult | 3 | Tidal Quarry | 321905 |
| multiplayer | 1 | Broken Comet | 1791643 |
| multiplayer | 2 | Restless Meadow | 687386 |
| multiplayer | 3 | Gearbreak 2 | 452960 |
| sci-fi | 1 | Frontier of Keshaven® | 485030 |

Полный вывод — 15 строк (5 тегов × 3 игры).

### Q5 — падения цен между выгрузками (топ-10)

| title | old_price | new_price | change_pct |
|---|---|---|---|
| Sunken Hearth | 4.99 | 0.99 | -80.2 |
| Parade of Eldwick | 9.99 | 1.99 | -80.1 |
| Silent Hearth | 9.99 | 1.99 | -80.1 |
| Stormbound | 9.96 | 1.99 | -80.0 |
| Rusted Quarry | 12.99 | 2.99 | -77.0 |
| Wild Signal | 12.99 | 2.99 | -77.0 |
| Woven Bastion | 29.99 | 6.99 | -76.7 |
| Foundry of Cairspire | 24.99 | 5.99 | -76.0 |
| The Little Furnace | 19.99 | 4.99 | -75.0 |
| The Rusted Parade | 19.99 | 4.99 | -75.0 |

Дополнительно: **32 игры подешевели**, **8 подорожали** (всего 40 изменений цены между `batch_1` и `batch_2`).

## Тесты

```
python tests/test_transform.py
```

**21 тест** на `parse_date`, `parse_tags`, `to_usd`, `match_key`:

- 3 формата дат, `None`, пусто, мусор;
- разделители тегов (`;`, `,`, `|`), дубли, пробелы;
- конвертация USD/EUR/RUB, неизвестная валюта;
- нормализация названий (`™`, лишние пробелы, год).

## Где использовал ИИ

ИИ использовал как справочник по синтаксису — уточнял отдельные места, когда нужно было быстро вспомнить точную формулировку. Также с его помощью оформил этот README (структура разделов, markdown-таблицы с результатами Q1–Q5).

**В Python** уточнял:
- синтаксис `ON CONFLICT DO UPDATE` в `sqlite3` (порядок параметров, роль `with conn:`);
- `strptime`/`strftime` для перебора нескольких форматов дат;
- регулярку `re.split(r"[;,|]+", ...)` для разделителей тегов.

**В SQL** уточнял:
- `ROW_NUMBER() OVER (PARTITION BY ... ORDER BY ...)` для Q4;
- `LAG(...) OVER (PARTITION BY ... ORDER BY ...)` для Q5;
