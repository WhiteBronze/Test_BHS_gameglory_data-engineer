# Стартовый скелет

Скелет нужен, чтобы не тратить время на настройку. Это подсказка, а не обязательная структура:
можно переименовывать функции, разбивать код на модули, использовать pandas вместо стандартной библиотеки.

| Файл | Что это |
|---|---|
| `pipeline.py` | заготовка пайплайна: extract → transform → load → report, места для кода помечены `TODO` |
| `questions.sql` | 5 вопросов к итоговой базе (Q4 — по желанию) — напишите под каждым свой SQL-запрос |
| `tests/test_transform.py` | пример минимального теста; запускается и без pytest |
| `requirements.txt` | зависимости (для обязательной части не нужны) |

## Как запустить

Нужен только Python 3.11+ — SQLite встроен в него (модуль `sqlite3`), ничего устанавливать не нужно. На Windows вместо `python3` пишите `python`.

```bash
cd starter
python3 pipeline.py --db gameglory.db ../data/batch_1
python3 pipeline.py --db gameglory.db ../data/batch_2
python3 pipeline.py --db gameglory.db ../data/batch_2   # повторный запуск: дублей быть не должно

python3 tests/test_transform.py                         # или: python3 -m pytest -q

sqlite3 gameglory.db < questions.sql                    # если установлен консольный sqlite3
```

Пока функции с `TODO` не реализованы, пайплайн и тест падают с `NotImplementedError` — так и задумано.

Если консольной утилиты `sqlite3` нет, запросы можно выполнить из Python
(`conn.execute(sql).fetchall()`) или в любом GUI, например DB Browser for SQLite.

Не коммитьте файл базы (`*.db`) в репозиторий: проверяющий соберёт её сам вашей командой.
