# Gameglory · Data Engineer · «ETL-пайплайн для каталога игр»

Тестовое задание на позицию Data Engineer (стажёр / джун) в проекте Gameglory, Bear Head Studio.
Вы получаете «грязные» выгрузки из двух вымышленных источников (карточки игр, статистика, отзывы)
и пишете пайплайн extract → transform → load в SQLite с идемпотентным повторным запуском и
инкрементальной загрузкой второй порции данных.

Задание — в документе
[`Тестовое_задание_Data_Engineer.docx`](Тестовое_задание_Data_Engineer.docx).

## Состав пакета

| Путь | Что это |
|---|---|
| `Тестовое_задание_Data_Engineer.docx` | задание: задача, входные данные, что сделать, как сдать |
| `data/` | выгрузки `batch_1/` и `batch_2/` (`store_export.json`, `stats.csv`, `reviews.jsonl`), курсы `fx_rates.csv`, описание форматов в `README.md` |
| `starter/` | скелет `pipeline.py` с TODO, `questions.sql` (4 вопроса и 1 по желанию), пример теста, `requirements.txt`, `README.md` |

## Как начать

Нужен Python 3.11+; SQLite встроен в Python. Команды ниже — для macOS и Linux, на Windows вместо `python3` пишите `python`.

```bash
cd starter
python3 pipeline.py --db gameglory.db ../data/batch_1
python3 tests/test_transform.py
```

Пока функции с `TODO` не реализованы, обе команды падают с `NotImplementedError` — так и задумано.

Подробнее — в `starter/README.md`.
