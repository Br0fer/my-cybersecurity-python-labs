# ЛР №3. FastAPI + SQLite (варіант 12)

**Предметна область:** облік використання сховищ. Категорія визначає тип
сховища (`logs`, `backups`, `archive`), `value` — частку зайнятого простору
у відсотках (`0–100`), `status` — стан перевірки вимірювання
(`new`, `in_progress`, `done`). Поріг для варіанту: `85.0`.

## Встановлення залежностей

З кореня репозиторію (віртуальне середовище з ЛР №1 має бути активоване):

```bash
pip install -r requirements.txt
```

## Початкове заповнення бази

Створює таблиці та додає 3 категорії і 8 записів з `data/seed.json`.
Повторний запуск нічого не змінює й не дублює дані.

```bash
python -m labs.lab_3.seed
```

## Запуск API

```bash
uvicorn labs.lab_3.main:app --reload --host 127.0.0.1 --port 8000
```

Swagger UI: http://127.0.0.1:8000/docs, OpenAPI-схема: http://127.0.0.1:8000/openapi.json

## Перевірка стилю

```bash
ruff check .
ruff format --check .
```

## Приклади запитів

```bash
curl -i "http://127.0.0.1:8000/ping"
curl -i "http://127.0.0.1:8000/records?category_id=1&status=new&limit=5&offset=0"

curl -i -X POST "http://127.0.0.1:8000/records" \
  -H "Content-Type: application/json" \
  -d '{"code":"V12-TEST","title":"Навчальне вимірювання","category_id":1,"value":75.5,"status":"new"}'

# пакет із дублем code: очікується 409, запис V12-ROLLBACK не зберігається
curl -i -X POST "http://127.0.0.1:8000/records/bulk" \
  -H "Content-Type: application/json" \
  -d '[{"code":"V12-ROLLBACK","title":"Перший елемент","category_id":1,"value":40.0,"status":"new"},{"code":"V12-01","title":"Дублікат коду","category_id":2,"value":50.0,"status":"new"}]'
```
